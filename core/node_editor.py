# NEx_SDBM/core/node_editor.py

from maya import OpenMayaUI


try:
    from shiboken2 import wrapInstance

    from PySide2.QtWidgets import (
        QWidget,
        QGraphicsView,
        QStackedWidget
    )

except ImportError:
    from shiboken6 import wrapInstance

    from PySide6.QtWidgets import (
        QWidget,
        QGraphicsView,
        QStackedWidget
    )


def get_scene():

    ptr = OpenMayaUI.MQtUtil.findControl(
        "nodeEditorPanel1NodeEditorEd"
    )

    if not ptr:
        raise RuntimeError(
            "Open a Node Editor first."
        )

    widget = wrapInstance(
        int(ptr),
        QWidget
    )

    stack = widget.findChild(
        QStackedWidget
    )

    if not stack:
        raise RuntimeError(
            "Node Editor stack not found."
        )

    current = stack.currentWidget()

    if not current:
        raise RuntimeError(
            "No active Node Editor tab."
        )

    view = current.findChild(
        QGraphicsView
    )

    if not view:
        raise RuntimeError(
            "Node Editor graph view not found."
        )

    return view.scene()


def get_node_name(item):

    if is_nex_item(item):
        return None

    try:
        children = item.childItems()

    except RuntimeError:
        return None

    except Exception:
        return None

    for child in children:

        try:
            return child.text()

        except Exception:
            continue

    return None


def is_nex_item(item):

    return bool(
        getattr(
            item,
            "nex_item_type",
            None
        )
    )


def is_nex_backdrop(item):

    return (
        getattr(
            item,
            "nex_item_type",
            None
        )
        == "backdrop"
    )


def get_selected_items():

    scene = get_scene()

    return scene.selectedItems()


def get_selected_node_items():

    node_items = []

    for item in get_selected_items():

        name = get_node_name(
            item
        )

        if name:
            node_items.append(
                item
            )

    return node_items


def get_selected_backdrops():

    return [
        item
        for item in get_selected_items()
        if is_nex_backdrop(item)
    ]


def get_selected_node_names():

    names = []

    for item in get_selected_node_items():

        name = get_node_name(
            item
        )

        if name:
            names.append(
                name
            )

    return names


def get_graph_item_from_name(node_name):

    return get_scene_node_map().get(
        node_name
    )


def inspect_selected_items():

    node_map = get_scene_node_map()

    node_map["persp"]


def get_scene_node_map():

    scene = get_scene()

    mapping = {}

    for item in scene.items():

        name = get_node_name(
            item
        )

        if name:
            mapping[name] = item

    return mapping


def get_selection_bounds():

    selected = get_selected_node_items()

    if not selected:
        return None

    bounds = selected[0].sceneBoundingRect()

    for item in selected[1:]:

        bounds = bounds.united(
            item.sceneBoundingRect()
        )

    return bounds


def move_nodes(
    node_names,
    dx,
    dy
):

    node_map = get_scene_node_map()

    for node_name in node_names:

        item = node_map.get(
            node_name
        )

        if item:

            try:
                item.moveBy(
                    dx,
                    dy
                )

            except RuntimeError:
                pass

            except Exception:
                pass