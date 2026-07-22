#NEx_SDBM.api.py
import os

from maya import cmds

import NEx_SDBM.core.node_editor as NEx
import NEx_SDBM.core.serializer as serializer

from NEx_SDBM.items.backdrop import BackdropItem
import NEx_SDBM.core.scene_storage as scene_storage
from NEx_SDBM.items.comment import CommentItem
#from NEx_SDBM.core.utilities import undoChunk as unDo

_NEX_ITEMS = []

# api.py selection-related replacements

# ---------------------------------------------------------
# General NEx
# ---------------------------------------------------------
def clear_nex_selection():

    scene = NEx.get_scene()

    scene.clearSelection()




# ---------------------------------------------------------
# BackDropSpecific Actions
# ---------------------------------------------------------

def delete_selected_backdrops():

    scene = NEx.get_scene()

    selected = scene.selectedItems()

    deleted_count = 0

    for item in list(selected):

        if not serializer.is_nex_item_like(item):
            continue

        try:
            scene.removeItem(item)

            try:
                _NEX_ITEMS.remove(item)

            except ValueError:
                pass

            deleted_count += 1

        except RuntimeError:
            deleted_count += 1

        except Exception:
            pass

    print(
        "NEx | Deleted {} item(s)".format(
            deleted_count
        )
    )


def create_backdrop(title="First Prototype"):
    #with unDo("NEx Create Backdrop"):
    scene = NEx.get_scene()
    backdrop = BackdropItem(title)
    scene.addItem(backdrop)
    backdrop.setPos(0, 0)

    _NEX_ITEMS.append(backdrop)

    return backdrop


def create_backdrop_from_selection(title="New Group"):

    node_bounds = NEx.get_selection_bounds()

    selected_nex_items = (
        NEx.get_selected_parentable_nex_items()
    )

    nex_item_bounds = (
        NEx.get_selected_parentable_nex_bounds()
    )

    padding = 40

    if node_bounds:

        bounds = node_bounds

        contained_nodes = (
            NEx.get_selected_node_names()
        )

        child_nex_items = []

    elif nex_item_bounds:

        bounds = nex_item_bounds

        contained_nodes = []

        child_nex_items = selected_nex_items

    else:

        raise RuntimeError(
            "Nothing selected."
        )

    width = bounds.width() + (padding * 2)
    height = bounds.height() + (padding * 2)

    backdrop = BackdropItem(
        title=title,
        width=width,
        height=height
    )

    scene = NEx.get_scene()

    scene.addItem(
        backdrop
    )
    backdrop.setPos(
        bounds.left() - padding,
        bounds.top() - padding
    )

    backdrop.update_z_hierarchy()

    backdrop.contained_nodes = contained_nodes

    backdrop.update_z_hierarchy()

    _NEX_ITEMS.append(
        backdrop
    )

    return backdrop


def clear_all_NExItems():

    removed = serializer.clear_all_tab_backdrops()

    _NEX_ITEMS[:] = [
        item for item in _NEX_ITEMS
        if item not in removed
    ]

    print(
        "NEx | Cleared {} item(s)".format(
            len(removed)
        )
    )






# ---------------------------------------------------------
# CommentSpecific Actions
# ---------------------------------------------------------

def create_comment(text="Comment"):

    scene = NEx.get_scene()

    comment = CommentItem(
        text=text
    )

    scene.addItem(
        comment
    )

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

        comment.setPos(
            0,
            0
        )
    comment.update_z_hierarchy()

    _NEX_ITEMS.append(
        comment
    )

    return comment








# ---------------------------------------------------------
# Save/LoadSpecific Actions
# ---------------------------------------------------------

def get_default_nex_path():
    scene_path = cmds.file(
        query=True,
        sceneName=True
    )

    if scene_path:
        folder = os.path.dirname(scene_path)
        name = os.path.splitext(
            os.path.basename(scene_path)
        )[0]

        return os.path.join(
            folder,
            name + ".nex"
        )

    workspace = cmds.workspace(
        query=True,
        rootDirectory=True
    )

    return os.path.join(
        workspace,
        "untitled.nex"
    )

def save_all(filepath=None):

    if filepath is None:
        filepath = get_default_nex_path()

    live_data = serializer.build_data()

    if serializer.data_has_nex_items(
        live_data
    ):

        print(
            "NEx | Exporting live Node Editor data."
        )

        return serializer.save_data(
            filepath,
            live_data
        )

    print(
        "NEx | No live NEx items found. Checking scene storage..."
    )

    try:

        scene_data = scene_storage.read_scene_data()

    except Exception as error:

        print(
            "NEx | No usable scene storage found:",
            error
        )

        print(
            "NEx | Exporting empty live data."
        )

        return serializer.save_data(
            filepath,
            live_data
        )

    if serializer.data_has_nex_items(
        scene_data
    ):

        print(
            "NEx | Exporting NEx_SceneData storage."
        )

        return serializer.save_data(
            filepath,
            scene_data
        )

    print(
        "NEx | Scene storage exists but contains no NEx items. Exporting empty data."
    )

    return serializer.save_data(
        filepath,
        live_data
    )


def load_all(
    filepath=None,
    clear_existing=True
):

    if filepath is None:
        filepath = get_default_nex_path()

    if clear_existing:
        clear_all_NExItems()

    created = serializer.load_nex(
        filepath
    )

    _NEX_ITEMS.extend(
        created
    )

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

    return save_all(
        result[0]
    )


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

    return load_all(
        result[0],
        clear_existing=True
    )







# ---------------------------------------------------------
# SceneSave/Loadspecific Actions
# ---------------------------------------------------------
def save_to_scene():

    data = serializer.build_data()

    node = scene_storage.write_scene_data(
        data
    )

    return node


def load_from_scene(
    clear_existing=True
):

    if clear_existing:
        clear_all_NExItems()

    data = scene_storage.read_scene_data()

    created = serializer.load_data(
        data
    )

    _NEX_ITEMS.extend(
        created
    )

    print(
        "NEx | Loaded {} item(s) from scene data.".format(
            len(created)
        )
    )

    return created


def clear_scene_storage():

    return scene_storage.clear_scene_data()


def has_scene_storage():

    return scene_storage.has_scene_data()





# ---------------------------------------------------------
# MainUISpecific Actions
# ---------------------------------------------------------
_NEX_WINDOW = None
def show_ui():

    global _NEX_WINDOW

    from NEx_SDBM.ui.main_window import NExMainWindow

    try:

        if _NEX_WINDOW is not None:
            _NEX_WINDOW.close()
            _NEX_WINDOW.deleteLater()

    except Exception:
        pass

    _NEX_WINDOW = NExMainWindow()

    _NEX_WINDOW.show()
    _NEX_WINDOW.raise_()
    _NEX_WINDOW.activateWindow()

    return _NEX_WINDOW