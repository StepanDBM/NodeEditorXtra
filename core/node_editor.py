# NEx_SDBM/core/node_editor.py

from maya import OpenMayaUI


try:
    from shiboken2 import wrapInstance
    from PySide2.QtCore import (
        QObject,
        QEvent,
        Qt
    )
    from PySide2.QtWidgets import (
        QWidget,
        QGraphicsView,
        QStackedWidget,
        QStackedLayout,
        QTabBar
    )

except ImportError:
    from shiboken6 import wrapInstance
    from PySide6.QtCore import (
        QObject,
        QEvent,
        Qt
    )
    from PySide6.QtWidgets import (
        QWidget,
        QGraphicsView,
        QStackedWidget,
        QStackedLayout,
        QTabBar
    )


NODE_EDITOR_NAME = "nodeEditorPanel1NodeEditorEd"


# ---------------------------------------------------------
# Node Editor Access
# ---------------------------------------------------------

def get_node_editor_widget():

    ptr = OpenMayaUI.MQtUtil.findControl(
        NODE_EDITOR_NAME
    )

    if not ptr:
        raise RuntimeError(
            "Open a Node Editor first."
        )

    return wrapInstance(
        int(ptr),
        QWidget
    )


def get_search_root_widget():

    widget = get_node_editor_widget()

    current = widget

    last = widget

    while current:

        last = current

        try:
            current = current.parentWidget()

        except RuntimeError:
            break

        except Exception:
            break

    return last


# ---------------------------------------------------------
# Stack / Tabs
# ---------------------------------------------------------

def _safe_count(widget):

    try:
        return widget.count()

    except RuntimeError:
        return 0

    except Exception:
        return 0


def _page_has_graph_view(page):

    if not page:
        return False

    try:
        views = page.findChildren(
            QGraphicsView
        )

    except RuntimeError:
        return False

    except Exception:
        return False

    for view in views:

        try:
            if view.scene():
                return True

        except RuntimeError:
            continue

        except Exception:
            continue

    return False


def get_all_stacks():

    root = get_search_root_widget()

    stacks = []

    try:
        stacks.extend(
            root.findChildren(
                QStackedWidget
            )
        )

    except Exception:
        pass

    try:
        stacks.extend(
            root.findChildren(
                QStackedLayout
            )
        )

    except Exception:
        pass

    clean = []

    for stack in stacks:

        count = _safe_count(
            stack
        )

        if count <= 0:
            continue

        has_graph_page = False

        for index in range(count):

            try:
                page = stack.widget(
                    index
                )

            except Exception:
                page = None

            if _page_has_graph_view(
                page
            ):
                has_graph_page = True
                break

        if has_graph_page:
            clean.append(
                stack
            )

    clean = sorted(
        clean,
        key=lambda stack: _safe_count(stack),
        reverse=True
    )

    return clean


def get_stack():

    stacks = get_all_stacks()

    if not stacks:
        raise RuntimeError(
            "Node Editor stack not found."
        )

    return stacks[0]


def get_all_tab_bars():

    root = get_search_root_widget()

    try:
        return root.findChildren(
            QTabBar
        )

    except Exception:
        return []


def get_tab_bar():

    root = get_search_root_widget()

    stack_count = get_tab_count()

    try:
        tab_bars = root.findChildren(
            QTabBar
        )

    except Exception:
        return None

    exact_matches = []

    for tab_bar in tab_bars:

        try:
            count = tab_bar.count()

        except RuntimeError:
            continue

        except Exception:
            continue

        # IMPORTANT:
        # Only accept tab bars whose count matches the actual
        # Node Editor stacked pages. Do NOT accept bigger tab bars,
        # because Maya has many unrelated tab bars.
        if count == stack_count:

            exact_matches.append(
                tab_bar
            )

    if not exact_matches:
        return None

    # Prefer a visible tab bar if possible.
    visible_matches = []

    for tab_bar in exact_matches:

        try:

            if tab_bar.isVisible():
                visible_matches.append(
                    tab_bar
                )

        except Exception:
            pass

    if visible_matches:
        return visible_matches[0]

    return exact_matches[0]


def get_tab_count():

    stack = get_stack()

    return _safe_count(
        stack
    )


def get_current_tab_index():

    # IMPORTANT:
    # The stack is the source of truth for scene/page index.
    # The tab bar is only used for display names.
    try:

        stack = get_stack()

        index = stack.currentIndex()

        count = _safe_count(
            stack
        )

        if 0 <= index < count:
            return index

    except RuntimeError:
        pass

    except Exception:
        pass

    return 0


def get_tab_name(tab_index):

    tab_bar = get_tab_bar()

    if tab_bar:

        try:

            if 0 <= tab_index < tab_bar.count():

                name = tab_bar.tabText(
                    tab_index
                )

                if name:
                    return name

        except RuntimeError:
            pass

        except Exception:
            pass

    return "Tab_{}".format(
        tab_index
    )


def sanitize_tab_name(name):

    safe = str(name)

    for char in (
        " ",
        "/",
        "\\",
        ":",
        "*",
        "?",
        "\"",
        "<",
        ">",
        "|"
    ):

        safe = safe.replace(
            char,
            "_"
        )

    return safe


def get_tab_key_from_name(
    tab_index,
    tab_name
):

    return "tab_{}_{}".format(
        tab_index,
        sanitize_tab_name(
            tab_name
        )
    )


def get_tab_key(tab_index):

    return get_tab_key_from_name(
        tab_index,
        get_tab_name(
            tab_index
        )
    )


def get_current_tab_key():

    return get_tab_key(
        get_current_tab_index()
    )


def get_tab_info(tab_index):

    name = get_tab_name(
        tab_index
    )

    return {
        "index": tab_index,
        "name": name,
        "key": get_tab_key_from_name(
            tab_index,
            name
        )
    }


def get_all_tab_infos():

    infos = []

    count = get_tab_count()

    for index in range(count):

        infos.append(
            get_tab_info(
                index
            )
        )

    return infos


def find_tab_info_by_name(tab_name):

    for info in get_all_tab_infos():

        if info["name"] == tab_name:
            return info

    return None


# ---------------------------------------------------------
# Scene / View Access
# ---------------------------------------------------------

def _scene_from_view(view):

    try:
        scene = view.scene()

        if scene:
            return scene

    except RuntimeError:
        return None

    except Exception:
        return None

    return None


def _view_score(view):

    score = 0

    try:
        if view.isVisible():
            score += 1000000

        if view.viewport().isVisible():
            score += 1000000

        rect = view.viewport().rect()

        score += (
            rect.width()
            * rect.height()
        )

    except Exception:
        pass

    return score


def get_live_views_from_page(page):

    if not page:
        return []

    try:
        views = page.findChildren(
            QGraphicsView
        )

    except RuntimeError:
        return []

    except Exception:
        return []

    live_views = []

    for view in views:

        scene = _scene_from_view(
            view
        )

        if scene:
            live_views.append(
                view
            )

    return live_views


def get_scene_for_tab_index(tab_index):

    stack = get_stack()

    count = _safe_count(
        stack
    )

    if tab_index < 0 or tab_index >= count:

        raise RuntimeError(
            "Node Editor tab does not exist: {} / count {}".format(
                tab_index,
                count
            )
        )

    try:

        page = stack.widget(
            tab_index
        )

    except RuntimeError:
        page = None

    except Exception:
        page = None

    if not page:

        raise RuntimeError(
            "Node Editor tab page not found: {}".format(
                tab_index
            )
        )

    live_views = get_live_views_from_page(
        page
    )

    if not live_views:

        raise RuntimeError(
            "Node Editor graph view not found for tab: {}".format(
                tab_index
            )
        )

    live_views = sorted(
        live_views,
        key=_view_score,
        reverse=True
    )

    scene = _scene_from_view(
        live_views[0]
    )

    if not scene:

        raise RuntimeError(
            "Node Editor scene not found for tab: {}".format(
                tab_index
            )
        )

    return scene


def get_scene():

    return get_scene_for_tab_index(
        get_current_tab_index()
    )


def iter_tab_scenes():

    count = get_tab_count()

    for tab_index in range(count):

        try:

            yield (
                tab_index,
                get_scene_for_tab_index(
                    tab_index
                )
            )

        except Exception as error:

            print(
                "NEx | Could not get tab scene:",
                tab_index,
                error
            )


# ---------------------------------------------------------
# Item Checks
# ---------------------------------------------------------

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

def is_nex_parentable_item(item):

    return bool(
        getattr(
            item,
            "nex_parentable",
            False
        )
    )

# ---------------------------------------------------------
# Node Mapping
# ---------------------------------------------------------

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


def get_graph_item_from_name(node_name):

    return get_scene_node_map().get(
        node_name
    )


# ---------------------------------------------------------
# Selection
# ---------------------------------------------------------

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

def get_selected_backdrop_items():

    return [
        item
        for item in get_selected_items()
        if is_nex_backdrop(item)
    ]
# ---------------------------------------------------------
# NEx Abstraction to item methods
# ---------------------------------------------------------

def get_selected_nex_items():

    return [
        item
        for item in get_selected_items()
        if is_nex_item(item)
    ]
def get_selected_parentable_nex_items():

    return [
        item
        for item in get_selected_items()
        if is_nex_parentable_item(item)
    ]
def get_selected_parentable_nex_bounds():

    return get_bounds_from_items(
        get_selected_parentable_nex_items()
    )


def get_bounds_from_items(items):

    valid_items = []

    for item in items:

        try:
            item.sceneBoundingRect()
            valid_items.append(
                item
            )

        except RuntimeError:
            continue

        except Exception:
            continue

    if not valid_items:
        return None

    bounds = valid_items[0].sceneBoundingRect()

    for item in valid_items[1:]:

        bounds = bounds.united(
            item.sceneBoundingRect()
        )

    return bounds


def get_selected_backdrop_bounds():

    return get_bounds_from_items(
        get_selected_backdrop_items()
    )


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


def get_selection_bounds():

    return get_bounds_from_items(
        get_selected_node_items()
    )


# ---------------------------------------------------------
# Movement
# ---------------------------------------------------------

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