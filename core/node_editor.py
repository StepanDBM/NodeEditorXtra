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
# Node Editor Stack
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




# ---------------------------------------------------------
# Tabs For Detection Helpers.
# ---------------------------------------------------------


def get_tab_infos():

    return get_all_tab_infos()


def get_current_tab_info():

    return get_tab_info(
        get_current_tab_index()
    )


def set_current_tab_by_index(
    tab_index
):

    try:

        stack = get_stack()

        count = _safe_count(
            stack
        )

        if tab_index < 0 or tab_index >= count:
            return False

    except RuntimeError:
        return False

    except Exception:
        return False

    tab_bar = get_tab_bar()

    if tab_bar:

        try:

            if 0 <= tab_index < tab_bar.count():

                tab_bar.setCurrentIndex(
                    tab_index
                )

                tab_bar.repaint()

        except RuntimeError:
            pass

        except Exception:
            pass

    try:

        stack.setCurrentIndex(
            tab_index
        )

    except RuntimeError:
        return False

    except Exception:
        return False

    tab_bar = get_tab_bar()

    if tab_bar:

        try:

            if 0 <= tab_index < tab_bar.count():

                tab_bar.setCurrentIndex(
                    tab_index
                )

                tab_bar.repaint()

        except RuntimeError:
            pass

        except Exception:
            pass

    return True

def get_all_tab_bars():

    root = get_search_root_widget()

    try:
        return root.findChildren(
            QTabBar
        )

    except Exception:
        return []

#---------------------------------------------------
#debugging
#---------------------------------------------------
def debug_tab_bars():

    stack = get_stack()
    stack_count = get_tab_count()
    stack_widget = _get_stack_widget_for_geometry(
        stack
    )

    ancestors = _widget_ancestors(
        stack_widget,
        max_depth=10
    )

    print(
        "NEx | Stack:",
        stack
    )

    print(
        "NEx | Stack count:",
        stack_count
    )

    print(
        "NEx | Stack current:",
        stack.currentIndex()
    )

    for ancestor_depth, ancestor in enumerate(
        ancestors
    ):

        try:

            tab_bars = ancestor.findChildren(
                QTabBar
            )

        except Exception:

            tab_bars = []

        if not tab_bars:
            continue

        print(
            "NEx | Ancestor depth:",
            ancestor_depth,
            "|",
            ancestor
        )

        for index, tab_bar in enumerate(
            tab_bars
        ):

            try:

                count = tab_bar.count()

            except Exception:

                count = "?"

            try:

                current = tab_bar.currentIndex()

            except Exception:

                current = "?"

            texts = _tab_bar_texts(
                tab_bar
            )

            try:

                visible = tab_bar.isVisible()

            except Exception:

                visible = "?"

            try:

                score = _score_tab_bar_candidate(
                    tab_bar,
                    stack,
                    ancestor_depth
                )

            except Exception:

                score = "?"

            print(
                "NEx |   TabBar {} | count={} | current={} | visible={} | score={} | texts={}".format(
                    index,
                    count,
                    current,
                    visible,
                    score,
                    texts
                )
            )

    chosen = get_tab_bar()

    print(
        "NEx | Chosen tab bar:",
        chosen
    )

    if chosen:

        print(
            "NEx | Chosen texts:",
            _tab_bar_texts(
                chosen
            )
        )
# ---------------------------------------------------------
# Node Editor Tab Bar Detection
# ---------------------------------------------------------

def _get_stack_widget_for_geometry(
    stack
):

    try:

        if isinstance(
            stack,
            QStackedLayout
        ):

            return stack.parentWidget()

    except Exception:
        pass

    return stack


def _tab_bar_texts(
    tab_bar
):

    texts = []

    try:

        count = tab_bar.count()

    except Exception:

        return texts

    for index in range(
        count
    ):

        try:

            texts.append(
                tab_bar.tabText(
                    index
                )
            )

        except Exception:

            texts.append(
                ""
            )

    return texts


def _tab_bar_matches_node_editor_count(
    tab_bar,
    stack_count
):

    try:

        tab_count = tab_bar.count()

    except RuntimeError:
        return False

    except Exception:
        return False

    if tab_count == stack_count:
        return True

    # Maya Node Editor often has one extra empty tab/button entry.
    if tab_count == stack_count + 1:

        texts = _tab_bar_texts(
            tab_bar
        )

        if texts and texts[-1] == "":
            return True

    return False


def _tab_bar_has_false_positive_names(
    tab_bar
):

    texts = _tab_bar_texts(
        tab_bar
    )

    false_positive_words = [
        "outliner",
        "anim",
        "modeling toolkit",
        "channel",
        "channel box",
        "attribute editor",
        "tool settings",
        "layer editor"
    ]

    for text in texts:

        lowered = text.lower()

        for word in false_positive_words:

            if word in lowered:
                return True

    return False


def _score_tab_bar_candidate(
    tab_bar,
    stack
):

    score = 0

    try:

        if tab_bar.isVisible():
            score += 100000

    except Exception:
        pass

    try:

        if tab_bar.currentIndex() == stack.currentIndex():
            score += 50000

    except Exception:
        pass

    texts = _tab_bar_texts(
        tab_bar
    )

    for text in texts:

        lowered = text.lower()

        if "untitled" in lowered:
            score += 50000

    if _tab_bar_has_false_positive_names(
        tab_bar
    ):

        score -= 500000

    return score


def get_tab_bar():

    stack = get_stack()

    stack_count = get_tab_count()

    # IMPORTANT:
    # Search the actual Node Editor widget first.
    # Do not start from Maya's main/root widget, because that finds
    # Outliner / Anim / Channel Box / Modeling Toolkit tab bars.
    try:

        root = get_node_editor_widget()

    except Exception:

        root = get_search_root_widget()

    try:

        tab_bars = root.findChildren(
            QTabBar
        )

    except Exception:

        return None

    candidates = []

    for tab_bar in tab_bars:

        if not _tab_bar_matches_node_editor_count(
            tab_bar,
            stack_count
        ):
            continue

        score = _score_tab_bar_candidate(
            tab_bar,
            stack
        )

        candidates.append(
            (
                score,
                tab_bar
            )
        )

    if not candidates:
        return None

    candidates = sorted(
        candidates,
        key=lambda data: data[0],
        reverse=True
    )

    return candidates[0][1]


def get_tab_count():

    stack = get_stack()

    return _safe_count(
        stack
    )


def get_current_tab_index():

    tab_bar = get_tab_bar()

    if tab_bar:

        try:

            index = tab_bar.currentIndex()
            count = tab_bar.count()

            if 0 <= index < count:

                return index

        except RuntimeError:
            pass

        except Exception:
            pass

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