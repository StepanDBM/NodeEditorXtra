import os

from maya import cmds

import NEx_SDBM.core.node_editor as NEx
import NEx_SDBM.core.serializer as serializer

from NEx_SDBM.items.backdrop import BackdropItem
import NEx_SDBM.core.scene_storage as scene_storage
from NEx_SDBM.core.utilities import undoChunk as unDo

_NEX_ITEMS = []

# api.py selection-related replacements

def clear_nex_selection():

    scene = NEx.get_scene()

    scene.clearSelection()


def delete_selected_backdrops():

    scene = NEx.get_scene()

    selected = scene.selectedItems()

    deleted_count = 0

    for item in list(selected):

        if not serializer.is_backdrop_like(item):
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
        "NEx | Deleted {} backdrop(s)".format(
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

    selected_backdrops = (
        NEx.get_selected_backdrop_items()
    )

    backdrop_bounds = (
        NEx.get_selected_backdrop_bounds()
    )

    padding = 40

    if node_bounds:

        bounds = node_bounds

        contained_nodes = (
            NEx.get_selected_node_names()
        )

        child_backdrops = []

    elif backdrop_bounds:

        bounds = backdrop_bounds

        contained_nodes = []

        child_backdrops = selected_backdrops

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

    backdrop.contained_nodes = contained_nodes

    # If this is a parent backdrop, put it visually behind the selected children.
    if child_backdrops:

        try:

            min_z = min(
                child.zValue()
                for child in child_backdrops
            )

            backdrop.setZValue(
                min_z - 1
            )

        except Exception:

            backdrop.setZValue(
                -1
            )

    _NEX_ITEMS.append(
        backdrop
    )

    return backdrop


def clear_all_backdrops():

    removed = serializer.clear_all_tab_backdrops()

    _NEX_ITEMS[:] = [
        item for item in _NEX_ITEMS
        if item not in removed
    ]

    print(
        "NEx | Cleared {} backdrop(s)".format(
            len(removed)
        )
    )

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

    return serializer.save_nex(
        filepath
    )


def load_all(
    filepath=None,
    clear_existing=True
):

    if filepath is None:
        filepath = get_default_nex_path()

    if clear_existing:
        clear_all_backdrops()

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
# SceneLoader
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
        clear_all_backdrops()

    data = scene_storage.read_scene_data()

    created = serializer.load_data(
        data
    )

    _NEX_ITEMS.extend(
        created
    )

    print(
        "NEx | Loaded {} backdrop(s) from scene data.".format(
            len(created)
        )
    )

    return created


def clear_scene_storage():

    return scene_storage.clear_scene_data()


def has_scene_storage():

    return scene_storage.has_scene_data()


_NEX_WINDOW = None


def show_ui():

    global _NEX_WINDOW

    from NEx_SDBM.ui.main_window import (
        NExMainWindow
    )

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