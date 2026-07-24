#NEx_SDBM.api.py
import os

from maya import cmds

import NEx_SDBM.core.node_editor as NEx
import NEx_SDBM.core.serializer as serializer
import NEx_SDBM.core.utilities.events as events

import NEx_SDBM.core.scene_storage as scene_storage
from NEx_SDBM.items.backdrop import BackdropItem
from NEx_SDBM.items.comment import CommentItem
from NEx_SDBM.items.image import ImageItem
#from NEx_SDBM.core.utilities import undoChunk as unDo

_NEX_ITEMS = []

# api.py selection-related replacements

# ---------------------------------------------------------
# General NEx
# ---------------------------------------------------------
def clear_nex_selection():
    scene = NEx.get_scene()
    scene.clearSelection()


# -----------------------------------------------------
# FocusViewList Event Abstraction
# -----------------------------------------------------

def notify_items_changed(reason ="unknown"):

    try:
        events.emit_items_changed( reason = reason)

    except Exception:
        pass
# ---------------------------------------------------------
# BackDropSpecific Actions
# ---------------------------------------------------------

def _get_scene_bounds_from_items(
    items
):
    valid_rects = []
    for item in items:
        try:
            rect = item.sceneBoundingRect()
        except RuntimeError:
            continue
        except Exception:
            continue

        if rect.isNull() or rect.isEmpty():
            continue

        valid_rects.append(rect)

    if not valid_rects:
        return None

    bounds = valid_rects[0]
    for rect in valid_rects[1:]:
        bounds = bounds.united(rect)

    return bounds


def _get_area_from_rect(
    rect
):

    return (
        rect.width()
        * rect.height()
    )


def _item_contains_item(
    container,
    item
):
    try:

        container_rect = container.sceneBoundingRect()
        item_rect = item.sceneBoundingRect()

    except RuntimeError:
        return False

    except Exception:
        return False

    return container_rect.contains(item_rect)


def _get_existing_container_parent_for_item(
    item
):

    try:

        return item.get_parent_container()

    except RuntimeError:
        return None

    except Exception:
        return None


def _item_has_selected_nex_ancestor(
    item,
    selected_nex_items
):

    parent = _get_existing_container_parent_for_item(item)
    safety = 0
    while parent and safety < 50:
        if parent in selected_nex_items:
            return True
        parent = _get_existing_container_parent_for_item(parent)
        safety += 1

    return False


def _filter_selected_nex_roots(
    selected_nex_items
):
    result = []

    for item in selected_nex_items:
        if _item_has_selected_nex_ancestor(
            item,
            selected_nex_items
        ):

            continue

        result.append(item)

    return result


def _native_node_is_inside_selected_nex_container(
    node_item,
    selected_nex_items
):
    for nex_item in selected_nex_items:

        if not getattr(
            nex_item,
            "nex_container",
            False
        ):
            continue

        if _item_contains_item(
            nex_item,
            node_item
        ):

            return True

    return False


def _get_parent_container_if_backdrop_would_duplicate_parent(
    selected_nex_items,
    target_bounds,
    tolerance=4.0
):
    if not selected_nex_items or not target_bounds:
        return None
    candidate_parents = []
    for item in selected_nex_items:
        parent = _get_existing_container_parent_for_item(item)
        if not parent:
            continue
        try:
            parent_rect = parent.sceneBoundingRect()

        except RuntimeError:
            continue
        except Exception:
            continue

        if not parent_rect.contains(item.sceneBoundingRect()):
            continue
        target_area = _get_area_from_rect(target_bounds)
        parent_area = _get_area_from_rect(parent_rect)

        if parent_area <= 0:
            continue

        area_delta = abs(
            parent_area
            - target_area
        )

        size_is_too_close = (
            area_delta
            <= tolerance
            * max(
                parent_rect.width(),
                parent_rect.height()
            )
        )

        rect_is_too_close = (
            abs(
                parent_rect.left()
                - target_bounds.left()
            )
            <= tolerance
            and abs(
                parent_rect.top()
                - target_bounds.top()
            )
            <= tolerance
            and abs(
                parent_rect.width()
                - target_bounds.width()
            )
            <= tolerance
            and abs(
                parent_rect.height()
                - target_bounds.height()
            )
            <= tolerance
        )
        if size_is_too_close or rect_is_too_close:
            candidate_parents.append(parent)

    if not candidate_parents:
        return None

    candidate_parents = sorted(
        candidate_parents,
        key=lambda item: item.get_area()
    )

    return candidate_parents[0]


def create_backdrop_from_selection(
    title="New Group"
):
    scene = NEx.get_scene()
    selected_node_items = NEx.get_selected_node_items()
    selected_nex_items = NEx.get_selected_parentable_nex_items()

    # -----------------------------------------------------
    # 1. Remove selected NEx children if their selected parent
    #    is already selected.
    # -----------------------------------------------------

    selected_nex_roots = _filter_selected_nex_roots(selected_nex_items)

    # -----------------------------------------------------
    # 2. Remove native Maya nodes already represented by
    #    a selected NEx container.
    # -----------------------------------------------------

    filtered_node_items = []
    for node_item in selected_node_items:
        if _native_node_is_inside_selected_nex_container(
            node_item,
            selected_nex_roots
        ):
            continue

        filtered_node_items.append(node_item)

    # -----------------------------------------------------
    # 3. Build combined selection bounds.
    # -----------------------------------------------------

    bounds_items = (
        filtered_node_items
        + selected_nex_roots
    )

    bounds = _get_scene_bounds_from_items(bounds_items)

    if not bounds:
        raise RuntimeError("Nothing selected.")

    padding = 40
    target_bounds = bounds.adjusted(
        -padding,
        -padding,
        padding,
        padding
    )

    # -----------------------------------------------------
    # 4. Safety:
    #    If wrapping a selected NEx item would create a backdrop
    #    basically identical to its current parent, wrap the parent
    #    instead. This prevents same-size/overlapping container
    #    ambiguity and hierarchy cycles.
    # -----------------------------------------------------

    duplicate_parent = (
        _get_parent_container_if_backdrop_would_duplicate_parent(
            selected_nex_roots,
            target_bounds
        )
    )
    if duplicate_parent is not None:
        try:
            parent_rect = duplicate_parent.sceneBoundingRect()
            bounds = parent_rect
            target_bounds = bounds.adjusted(
                -padding,
                -padding,
                padding,
                padding
            )
            selected_nex_roots = [duplicate_parent]
            filtered_node_items = []

        except RuntimeError:
            pass
        except Exception:
            pass
    width = target_bounds.width()
    height = target_bounds.height()

    backdrop = BackdropItem(
        title=title,
        width=width,
        height=height
    )
    scene.addItem(backdrop)

    backdrop.setPos(
        target_bounds.left(),
        target_bounds.top()
    )
    contained_nodes = []

    for node_item in filtered_node_items:
        node_name = NEx.get_node_name(node_item)
        if node_name:
            contained_nodes.append(node_name)

    backdrop.contained_nodes = contained_nodes

    # Let geometry-based direct ownership resolve now that
    # the selected roots and nodes are inside the new backdrop.
    backdrop.update_z_hierarchy()
    _NEX_ITEMS.append(backdrop)
    notify_items_changed(reason ="create")

    return backdrop

def clear_all_NExItems():
    removed = serializer.clear_all_tab_backdrops()

    _NEX_ITEMS[:] = [
        item for item in _NEX_ITEMS
        if item not in removed
    ]

    notify_items_changed(reason ="clear")
    print(
        "NEx | Cleared {} item(s)".format(
            len(removed)
        )
    )






# ---------------------------------------------------------
# CommentSpecific Actions
# ---------------------------------------------------------

def create_comment(
    title="Comment",
    text="Comment"
):
    scene = NEx.get_scene()
    comment = CommentItem(title=title, text=text)
    scene.addItem(comment)
    try:
        view = scene.views()[0]
        center = view.mapToScene(
            view.viewport().rect()
        ).boundingRect().center()

        comment.setPos(
            center.x() - 120,
            center.y() - 60
        )

    except Exception:
        comment.setPos(0, 0)

    comment.update_z_hierarchy()

    _NEX_ITEMS.append(comment)
    notify_items_changed(reason ="create")
    return comment








# ---------------------------------------------------------
# Save/LoadSpecific Actions
# ---------------------------------------------------------

def get_default_nex_path():
    scene_path = cmds.file(query=True, sceneName=True)

    if scene_path:
        folder = os.path.dirname(scene_path)
        name = os.path.splitext(
            os.path.basename(scene_path)
        )[0]

        return os.path.join(folder, name + ".nex")

    workspace = cmds.workspace(query=True, rootDirectory=True)

    return os.path.join(workspace, "untitled.nex")

def save_all(filepath=None):
    if filepath is None:
        filepath = get_default_nex_path()

    live_data = serializer.build_data()
    if serializer.data_has_nex_items(live_data):
        print("NEx | Exporting live Node Editor data.")
        return serializer.save_data(filepath, live_data)
    print("NEx | No live NEx items found. Checking scene storage...")

    try:
        scene_data = scene_storage.read_scene_data()
    except Exception as error:
        print("NEx | No usable scene storage found:",
            error
        )

        print("NEx | Exporting empty live data.")

        return serializer.save_data(filepath, live_data)

    if serializer.data_has_nex_items(scene_data):
        print("NEx | Exporting NEx_SceneData storage.")
        return serializer.save_data(filepath, scene_data)

    print("NEx | Scene storage exists but contains no NEx items. Exporting empty data.")
    return serializer.save_data(filepath, live_data)


def load_all(
    filepath=None,
    clear_existing=True
):
    if filepath is None:
        filepath = get_default_nex_path()

    if clear_existing:
        clear_all_NExItems()

    created = serializer.load_nex(filepath)

    _NEX_ITEMS.extend(created)
    notify_items_changed(reason ="load")
    return created


def save_all_dialog():
    default_path = get_default_nex_path()
    result = cmds.fileDialog2(
        fileMode=0,
        caption="Save NEx File",
        fileFilter="NEx Files (*.nex)",
        startingDirectory=os.path.dirname(default_path)
    )

    if not result:
        return None

    return save_all(result[0])


def load_all_dialog():
    default_path = get_default_nex_path()
    result = cmds.fileDialog2(
        fileMode=1,
        caption="Load NEx File",
        fileFilter="NEx Files (*.nex)",
        startingDirectory=os.path.dirname(default_path)
    )

    if not result:
        return None
    notify_items_changed(reason ="load")
    return load_all(
        result[0],
        clear_existing=True
    )







# ---------------------------------------------------------
# SceneSave/Loadspecific Actions
# ---------------------------------------------------------
def save_to_scene():
    data = serializer.build_data()
    node = scene_storage.write_scene_data(data)
    return node


def load_from_scene(
    clear_existing=True
):
    if clear_existing:
        clear_all_NExItems()

    data = scene_storage.read_scene_data()
    created = serializer.load_data(data)
    _NEX_ITEMS.extend(created)

    print("NEx | Loaded {} item(s) from scene data.".format(
            len(created)
        )
    )

    return created

def clear_scene_storage():
    return scene_storage.clear_scene_data()

def has_scene_storage():
    return scene_storage.has_scene_data()


# ---------------------------------------------------------
# ImageSpecific Actions
# ---------------------------------------------------------

def create_image(
    image_path=None,
    title="Image"
):

    if image_path is None:

        result = cmds.fileDialog2(
            fileMode=1,
            caption="Choose Image",
            fileFilter="Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp)"
        )

        if not result:
            return None

        image_path = result[0]

    scene = NEx.get_scene()

    image = ImageItem(
        title=title,
        image_path=image_path
    )

    scene.addItem(image)

    try:

        view = scene.views()[0]

        center = view.mapToScene(
            view.viewport().rect()
        ).boundingRect().center()

        image.setPos(
            center.x() - 160,
            center.y() - 110
        )

    except Exception:

        image.setPos(0,0)

    image.update_z_hierarchy()

    _NEX_ITEMS.append(image)
    notify_items_changed(reason ="create")
    return image

# ---------------------------------------------------------
# MainUISpecific Actions
# ---------------------------------------------------------

def show_ui():

    import NEx_SDBM.launcher as launcher

    return launcher.show()