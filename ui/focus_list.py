# NEx_SDBM/ui/focus_list.py

try:
    from PySide2.QtCore import (
        Qt,
        QTimer
    )

    from PySide2.QtGui import (
        QColor,
        QBrush
    )

    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QComboBox,
        QAbstractItemView,
        QTreeWidget,
        QTreeWidgetItem,
        QHeaderView,
        QLineEdit,
        QCheckBox
    )

except ImportError:
    from PySide6.QtCore import (
        Qt,
        QTimer
    )

    from PySide6.QtGui import (
        QColor,
        QBrush
    )

    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QComboBox,
        QAbstractItemView,
        QTreeWidget,
        QTreeWidgetItem,
        QHeaderView,
        QLineEdit,
        QCheckBox
    )
from maya import cmds

import NEx_SDBM.core.node_editor as NEx
import NEx_SDBM.core.scene_view as scene_view
import NEx_SDBM.core.utilities.events as events
import NEx_SDBM.core.utilities.scene_index as scene_index


class FocusListWidget(QWidget):

    ITEM_ROLE = Qt.UserRole
    KIND_ROLE = Qt.UserRole + 1

    KIND_NEX_ITEM = "nex_item"
    KIND_NATIVE_NODE = "native_node"

    OPTION_SHOW_NATIVE_NODES = "NEx_show_native_nodes"
    OPTION_TREE_COLUMN_0 = "NEx_outliner_column_0"
    OPTION_TREE_COLUMN_1 = "NEx_outliner_column_1"

    def __init__(
        self,
        parent=None
    ):

        super().__init__(
            parent
        )

        self._refreshing = False
        self._syncing_tabs = False
        self.current_tab_info = None

        self.search_text = ""
        self.show_native_nodes = True

        self._tree_refresh_pending = False
        self._filter_refresh_pending = False
        self._tree_items_by_scene_item = {}

        self.build_ui()
        self.create_connections()

        self.refresh_tabs()
        self.refresh_tree_now()

    # -----------------------------------------------------
    # UI
    # -----------------------------------------------------

    def build_ui(self):

        layout = QVBoxLayout(
            self
        )

        layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        layout.setSpacing(
            4
        )

        self.tab_combo = QComboBox()

        layout.addWidget(
            self.tab_combo
        )
        self.search_field = QLineEdit()

        self.search_field.setPlaceholderText(
            "Search NEx / Maya nodes..."
        )

        layout.addWidget(
            self.search_field
        )

        self.show_native_nodes_checkbox = QCheckBox(
            "Show Maya Nodes"
        )

        self.show_native_nodes = self.get_option_bool(
            self.OPTION_SHOW_NATIVE_NODES,
            True
        )

        self.show_native_nodes_checkbox.setChecked(
            self.show_native_nodes
        )

        layout.addWidget(
            self.show_native_nodes_checkbox
        )
        self.tree = QTreeWidget()

        self.tree.setColumnCount(
            2
        )

        self.tree.setHeaderLabels(
            [
                "Type",
                "Title"
            ]
        )

        self.tree.header().setSectionResizeMode(
            0,
            QHeaderView.Interactive
        )

        self.tree.header().setSectionResizeMode(
            1,
            QHeaderView.Interactive
        )

        self.tree.setMinimumHeight(
            180
        )

        self.tree.setAlternatingRowColors(
            True
        )
        self.tree.setUniformRowHeights(
            True
        )

        self.tree.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.tree.setEditTriggers(
            QAbstractItemView.SelectedClicked
            | QAbstractItemView.EditKeyPressed
        )

        self.tree.setExpandsOnDoubleClick(
            False
        )

        layout.addWidget(
            self.tree
        )

    def create_connections(self):

        self.tree.header().sectionResized.connect(
            self.on_tree_column_resized
        )

        self.tab_combo.currentIndexChanged.connect(
            self.on_tab_combo_changed
        )

        self.search_field.textChanged.connect(
            self.on_search_text_changed
        )

        self.show_native_nodes_checkbox.toggled.connect(
            self.on_show_native_nodes_toggled
        )

        self.tree.itemDoubleClicked.connect(
            self.on_item_double_clicked
        )

        self.tree.itemChanged.connect(
            self.on_tree_item_changed
        )

        bus = events.get_event_bus()

        bus.items_changed.connect(
            self.schedule_tree_refresh
        )

        bus.item_changed.connect(
            self.on_bus_item_changed
        )

        bus.tabs_changed.connect(
            self.on_tabs_changed
        )

        bus.current_tab_changed.connect(
            self.on_current_tab_changed
        )

    # -----------------------------------------------------
    # Tab handling
    # -----------------------------------------------------

    def get_current_maya_tab_info(self):

        try:

            return NEx.get_current_tab_info()

        except Exception:

            return None

    def refresh_tabs(self):

        self._syncing_tabs = True

        try:

            self.tab_combo.clear()

            try:

                tab_infos = NEx.get_tab_infos()

            except Exception:

                tab_infos = []

            if not tab_infos:

                self.tab_combo.addItem(
                    "Open a Node Editor",
                    None
                )

                self.current_tab_info = None
                return

            current_tab = self.get_current_maya_tab_info()

            current_key = None

            if current_tab:

                current_key = current_tab.get(
                    "key"
                )

            selected_combo_index = 0

            for combo_index, tab_info in enumerate(
                tab_infos
            ):

                label = "{} | {}".format(
                    tab_info.get(
                        "index",
                        combo_index
                    ),
                    tab_info.get(
                        "name",
                        "Tab_{}".format(
                            combo_index
                        )
                    )
                )

                self.tab_combo.addItem(
                    label,
                    tab_info
                )

                if (
                    current_key is not None
                    and tab_info.get(
                        "key"
                    )
                    == current_key
                ):

                    selected_combo_index = combo_index

            if self.tab_combo.count():

                self.tab_combo.setCurrentIndex(
                    selected_combo_index
                )

                self.current_tab_info = self.tab_combo.itemData(
                    selected_combo_index
                )

            else:

                self.current_tab_info = None

        finally:

            self._syncing_tabs = False

    def select_combo_tab_by_key(
        self,
        tab_key
    ):

        if tab_key is None:
            return

        self._syncing_tabs = True

        try:

            for index in range(
                self.tab_combo.count()
            ):

                tab_info = self.tab_combo.itemData(
                    index
                )

                if not tab_info:
                    continue

                if tab_info.get(
                    "key"
                ) == tab_key:

                    self.tab_combo.setCurrentIndex(
                        index
                    )

                    self.current_tab_info = tab_info

                    break

        finally:

            self._syncing_tabs = False

    def on_tab_combo_changed(
        self,
        index
    ):

        if self._syncing_tabs:
            return

        tab_info = self.tab_combo.itemData(
            index
        )

        if not tab_info:
            return

        self.current_tab_info = tab_info

        try:

            NEx.set_current_tab_by_index(
                tab_info.get(
                    "index",
                    0
                )
            )

        except Exception as error:

            print(
                "NEx | Could not switch Node Editor tab:",
                error
            )

        self.schedule_tree_refresh()

    def on_current_tab_changed(
        self,
        tab_info
    ):

        if not tab_info:
            return

        self.current_tab_info = tab_info

        self.select_combo_tab_by_key(
            tab_info.get(
                "key"
            )
        )

        self.schedule_tree_refresh()

    def on_tabs_changed(self):

        self.refresh_tabs()
        self.schedule_tree_refresh()

    # -----------------------------------------------------
    # Scene / item collection
    # -----------------------------------------------------

    def get_current_scene(self):

        if not self.current_tab_info:

            try:

                return NEx.get_scene()

            except Exception:

                return None

        try:

            return NEx.get_scene_for_tab_index(
                self.current_tab_info.get(
                    "index",
                    0
                )
            )

        except Exception:

            return None


    def get_scene_native_node_items(self):

        scene = self.get_current_scene()

        if not scene:
            return []

        try:

            scene_items = scene.items()

        except RuntimeError:
            return []

        except Exception:
            return []

        result = []

        for item in scene_items:

            if NEx.is_nex_item(
                item
            ):
                continue

            try:

                node_name = NEx.get_node_name(
                    item
                )

            except Exception:

                node_name = None

            if not node_name:
                continue

            result.append(
                (
                    node_name,
                    item
                )
            )

        return result

    def get_scene_nex_items(self):

        scene = self.get_current_scene()

        if not scene:
            return []

        try:

            scene_items = scene.items()

        except RuntimeError:
            return []

        except Exception:
            return []

        result = []

        for item in scene_items:

            if not NEx.is_nex_item(
                item
            ):
                continue

            try:

                if item.scene() is None:
                    continue

            except Exception:
                continue

            result.append(
                item
            )

        return result

    def get_parent_for_item(
        self,
        item,
        item_set
    ):

        try:

            parent = item.get_parent_container()

        except RuntimeError:
            return None

        except Exception:
            return None

        if parent in item_set:
            return parent

        return None

    def get_direct_container_for_native_node(
        self,
        node_item,
        containers
    ):

        try:

            node_rect = node_item.sceneBoundingRect()

        except RuntimeError:
            return None

        except Exception:
            return None

        candidates = []

        for container in containers:

            try:

                if container.sceneBoundingRect().contains(
                    node_rect
                ):

                    candidates.append(
                        container
                    )

            except RuntimeError:
                continue

            except Exception:
                continue

        if not candidates:
            return None

        candidates = sorted(
            candidates,
            key=lambda item: item.get_area()
        )

        return candidates[0]


    def create_native_node_tree_item(
        self,
        node_name,
        node_item
    ):

        tree_item = QTreeWidgetItem(
            [
                "Maya Node",
                node_name
            ]
        )

        tree_item.setData(
            0,
            self.ITEM_ROLE,
            node_item
        )

        tree_item.setData(
            1,
            self.ITEM_ROLE,
            node_item
        )

        tree_item.setData(
            0,
            self.KIND_ROLE,
            self.KIND_NATIVE_NODE
        )

        tree_item.setData(
            1,
            self.KIND_ROLE,
            self.KIND_NATIVE_NODE
        )

        tree_item.setFlags(
            tree_item.flags()
            & ~Qt.ItemIsEditable
        )

        background = QBrush(
            QColor(
                70,
                70,
                70,
                170
            )
        )

        foreground = QBrush(
            QColor(
                220,
                220,
                220
            )
        )

        for column in range(
            self.tree.columnCount()
        ):

            tree_item.setBackground(
                column,
                background
            )

            tree_item.setForeground(
                column,
                foreground
            )
        self._tree_items_by_scene_item[node_item] = tree_item
        return tree_item


    def tree_item_matches_search(
        self,
        tree_item
    ):

        if not self.search_text:
            return True

        type_text = tree_item.text(
            0
        ).lower()

        title_text = tree_item.text(
            1
        ).lower()

        combined = "{} {}".format(
            type_text,
            title_text
        )

        return self.search_text in combined


    def apply_filter_to_tree_item(
        self,
        tree_item
    ):

        own_match = self.tree_item_matches_search(
            tree_item
        )

        child_match = False

        for index in range(
            tree_item.childCount()
        ):

            child = tree_item.child(
                index
            )

            if self.apply_filter_to_tree_item(
                child
            ):

                child_match = True

        visible = (
            own_match
            or child_match
            or not self.search_text
        )

        hidden = not visible

        if tree_item.isHidden() != hidden:

            tree_item.setHidden(
                hidden
            )

        if child_match and self.search_text:

            tree_item.setExpanded(
                True
            )

        return visible


    def apply_tree_filter(self):

        for index in range(
            self.tree.topLevelItemCount()
        ):

            tree_item = self.tree.topLevelItem(
                index
            )

            self.apply_filter_to_tree_item(
                tree_item
            )
    def on_tree_column_resized(
        self,
        logical_index,
        old_size,
        new_size
    ):

        if self._refreshing:
            return

        self.save_tree_column_widths()


    # -----------------------------------------------------
    # Sorting / labels
    # -----------------------------------------------------

    def sort_items(
        self,
        items
    ):

        return sorted(
            items,
            key=lambda item: (
                self.get_sort_type_rank(
                    item
                ),
                getattr(
                    item,
                    "title",
                    ""
                ).lower()
            )
        )

    def get_sort_type_rank(
        self,
        item
    ):

        item_type = getattr(
            item,
            "nex_item_type",
            ""
        )

        if item_type == "backdrop":
            return 0

        if item_type == "comment":
            return 1

        if item_type == "image":
            return 2

        return 99

    def get_item_type_label(
        self,
        item
    ):

        item_type = getattr(
            item,
            "nex_item_type",
            "item"
        )

        if item_type == "backdrop":
            return "Backdrop"

        if item_type == "comment":
            return "Comment"

        if item_type == "image":
            return "Image"

        return item_type

    def get_item_title(
        self,
        item
    ):

        return getattr(
            item,
            "title",
            self.get_item_type_label(
                item
            )
        )
    # -----------------------------------------------------
    # Set Options for Native Nodes
    # -----------------------------------------------------

    def get_option_bool(
        self,
        name,
        default=True
    ):

        try:

            if cmds.optionVar(
                exists=name
            ):

                return bool(
                    cmds.optionVar(
                        query=name
                    )
                )

        except Exception:
            pass

        return default


    def set_option_bool(
        self,
        name,
        value
    ):

        try:

            cmds.optionVar(
                intValue=(
                    name,
                    int(
                        bool(
                            value
                        )
                    )
                )
            )

        except Exception:
            pass


    def get_option_int(
        self,
        name,
        default=0
    ):

        try:

            if cmds.optionVar(
                exists=name
            ):

                return int(
                    cmds.optionVar(
                        query=name
                    )
                )

        except Exception:
            pass

        return default


    def set_option_int(
        self,
        name,
        value
    ):

        try:

            cmds.optionVar(
                intValue=(
                    name,
                    int(
                        value
                    )
                )
            )

        except Exception:
            pass

    # -----------------------------------------------------
    # Styling
    # -----------------------------------------------------

    def get_item_color(
        self,
        item
    ):

        color = getattr(
            item,
            "background_color",
            QColor(
                45,
                45,
                45,
                220
            )
        )

        return QColor(
            color.red(),
            color.green(),
            color.blue(),
            180
        )
    
    def save_tree_column_widths(self):

        try:

            self.set_option_int(
                self.OPTION_TREE_COLUMN_0,
                self.tree.columnWidth(
                    0
                )
            )

            self.set_option_int(
                self.OPTION_TREE_COLUMN_1,
                self.tree.columnWidth(
                    1
                )
            )

        except Exception:
            pass

    def resize_tree_columns(self):

        saved_column_0 = self.get_option_int(
            self.OPTION_TREE_COLUMN_0,
            0
        )

        saved_column_1 = self.get_option_int(
            self.OPTION_TREE_COLUMN_1,
            0
        )

        if (
            saved_column_0 > 0
            and saved_column_1 > 0
        ):

            self.tree.setColumnWidth(
                0,
                saved_column_0
            )

            self.tree.setColumnWidth(
                1,
                saved_column_1
            )

            return

        width = self.tree.viewport().width()

        type_width = int(
            width
            * 0.50
        )

        title_width = (
            width
            - type_width
        )

        self.tree.setColumnWidth(
            0,
            type_width
        )

        self.tree.setColumnWidth(
            1,
            title_width
        )

    def apply_row_style(
        self,
        tree_item,
        nex_item
    ):

        background = QBrush(
            self.get_item_color(
                nex_item
            )
        )

        foreground = QBrush(
            QColor(
                255,
                255,
                255
            )
        )

        for column in range(
            self.tree.columnCount()
        ):

            tree_item.setBackground(
                column,
                background
            )

            tree_item.setForeground(
                column,
                foreground
            )

    # -----------------------------------------------------
    # Tree creation / refresh
    # -----------------------------------------------------

    def create_tree_item(
        self,
        nex_item
    ):

        tree_item = QTreeWidgetItem(
            [
                self.get_item_type_label(
                    nex_item
                ),
                self.get_item_title(
                    nex_item
                )
            ]
        )

        tree_item.setData(
            0,
            self.ITEM_ROLE,
            nex_item
        )

        tree_item.setData(
            1,
            self.ITEM_ROLE,
            nex_item
        )

        tree_item.setData(
            0,
            self.KIND_ROLE,
            self.KIND_NEX_ITEM
        )

        tree_item.setData(
            1,
            self.KIND_ROLE,
            self.KIND_NEX_ITEM
        )

        tree_item.setFlags(
            tree_item.flags()
            | Qt.ItemIsEditable
        )

        self.apply_row_style(
            tree_item,
            nex_item
        )
        self._tree_items_by_scene_item[nex_item] = tree_item
        return tree_item

    def build_hierarchy(self):

        scene = self.get_current_scene()

        if not scene:

            return (
                [],
                {},
                {}
            )

        index = scene_index.get_scene_index(
            scene=scene
        )

        roots = index.get_root_nex_items()

        children_by_parent = {}

        for parent in index.get_container_items():

            children_by_parent[parent] = index.get_children(
                parent
            )

        native_nodes_by_parent = {}

        for parent in index.get_container_items():

            native_node_items = index.get_native_nodes_for_parent(
                parent
            )

            node_data = []

            for node_item in native_node_items:

                node_name = index.get_native_node_name(
                    node_item
                )

                if not node_name:
                    continue

                node_data.append(
                    (
                        node_name,
                        node_item
                    )
                )

            native_nodes_by_parent[parent] = node_data

        return (
            roots,
            children_by_parent,
            native_nodes_by_parent
        )

    def tree_item_has_nex_child(
        self,
        tree_item
    ):

        for index in range(
            tree_item.childCount()
        ):

            child = tree_item.child(
                index
            )

            kind = child.data(
                0,
                self.KIND_ROLE
            )

            if kind == self.KIND_NEX_ITEM:
                return True

        return False


    def apply_initial_expansion_to_item(
        self,
        tree_item
    ):

        kind = tree_item.data(
            0,
            self.KIND_ROLE
        )

        if kind != self.KIND_NEX_ITEM:
            return

        has_nex_child = self.tree_item_has_nex_child(
            tree_item
        )

        if has_nex_child:

            tree_item.setExpanded(
                True
            )

            for index in range(
                tree_item.childCount()
            ):

                child = tree_item.child(
                    index
                )

                self.apply_initial_expansion_to_item(
                    child
                )

        else:

            # This keeps native Maya node lists hidden by default
            # when this NEx item has no NEx children.
            tree_item.setExpanded(
                False
            )


    def apply_initial_expansion(self):

        for index in range(
            self.tree.topLevelItemCount()
        ):

            tree_item = self.tree.topLevelItem(
                index
            )

            self.apply_initial_expansion_to_item(
                tree_item
            )


    def schedule_tree_refresh(
        self
    ):

        if self._tree_refresh_pending:
            return

        self._tree_refresh_pending = True

        QTimer.singleShot(
            100,
            self.refresh_tree_now
        )


    def refresh_tree(self):

        # Backward-compatible alias.
        self.schedule_tree_refresh()


    def refresh_tree_now(self):

        self._tree_refresh_pending = False

        self._refresh_tree_impl()

    def _refresh_tree_impl(self):

        if self._refreshing:
            return

        self._refreshing = True

        try:

            self.tree.setUpdatesEnabled(
                False
            )

            self.tree.blockSignals(
                True
            )
            self._tree_items_by_scene_item = {}
            self.tree.clear()

            roots, children_by_parent, native_nodes_by_parent = (
                self.build_hierarchy()
            )

            for root in roots:

                tree_item = self.create_tree_item(
                    root
                )

                self.tree.addTopLevelItem(
                    tree_item
                )

                self.populate_children(
                    tree_item,
                    root,
                    children_by_parent,
                    native_nodes_by_parent
                )

            self.apply_initial_expansion()

            self.resize_tree_columns()

            self.apply_tree_filter()

        finally:

            self.tree.blockSignals(
                False
            )

            self.tree.setUpdatesEnabled(
                True
            )

            try:

                self.tree.viewport().update()

            except Exception:
                pass

            self._refreshing = False

    def resizeEvent(
        self,
        event
    ):

        super().resizeEvent(
            event
        )

        self.resize_tree_columns()

    def populate_children(
        self,
        parent_tree_item,
        parent_nex_item,
        children_by_parent,
        native_nodes_by_parent
    ):

        # -----------------------------------------------------
        # Child NEx items first
        # -----------------------------------------------------

        children = children_by_parent.get(
            parent_nex_item,
            []
        )

        for child in children:

            child_tree_item = self.create_tree_item(
                child
            )

            parent_tree_item.addChild(
                child_tree_item
            )

            self.populate_children(
                child_tree_item,
                child,
                children_by_parent,
                native_nodes_by_parent
            )

        # -----------------------------------------------------
        # Direct native Maya nodes under this container
        # -----------------------------------------------------

        if self.show_native_nodes:

            native_nodes = native_nodes_by_parent.get(
                parent_nex_item,
                []
            )

            for node_name, node_item in native_nodes:

                node_tree_item = self.create_native_node_tree_item(
                    node_name,
                    node_item
                )

                parent_tree_item.addChild(
                    node_tree_item
                )

    # -----------------------------------------------------
    # Tree events
    # -----------------------------------------------------

    def on_item_double_clicked(
        self,
        tree_item,
        column
    ):

        scene_item = tree_item.data(
            0,
            self.ITEM_ROLE
        )

        if not scene_item:
            return

        tab_info = self.current_tab_info

        if tab_info:

            try:

                NEx.set_current_tab_by_index(
                    tab_info.get(
                        "index",
                        0
                    )
                )

            except Exception:
                pass

        QTimer.singleShot(
            100,
            lambda: scene_view.frame_view_on_item(
                scene_item
            )
        )

    def on_tree_item_changed(
        self,
        tree_item,
        column
    ):

        if self._refreshing:
            return

        if column != 1:
            return

        kind = tree_item.data(
            0,
            self.KIND_ROLE
        )

        if kind != self.KIND_NEX_ITEM:
            return

        nex_item = tree_item.data(
            0,
            self.ITEM_ROLE
        )

        if not nex_item:
            return

        new_title = tree_item.text(
            1
        ).strip()

        if not new_title:

            self.refresh_tree()
            return

        old_title = getattr(
            nex_item,
            "title",
            ""
        )

        if new_title == old_title:
            return

        nex_item.title = new_title

        try:

            nex_item.on_title_changed()

        except Exception:
            pass

        try:

            nex_item.update()

        except Exception:
            pass

        try:

            nex_item.notify_item_changed()

        except Exception:

            events.emit_item_changed(
                nex_item
            )
    def on_search_text_changed(
        self,
        text
    ):

        self.search_text = text.strip().lower()

        self.schedule_filter_refresh()

    def schedule_filter_refresh(self):

        if self._filter_refresh_pending:
            return

        self._filter_refresh_pending = True

        QTimer.singleShot(
            50,
            self.apply_tree_filter_now
        )


    def apply_tree_filter_now(self):

        self._filter_refresh_pending = False

        self.apply_tree_filter()

    def on_show_native_nodes_toggled(
        self,
        enabled
    ):

        self.show_native_nodes = bool(
            enabled
        )

        self.set_option_bool(
            self.OPTION_SHOW_NATIVE_NODES,
            self.show_native_nodes
        )

        self.schedule_tree_refresh()
    def on_bus_item_changed(
        self,
        item
    ):

        tree_item = self._tree_items_by_scene_item.get(
            item
        )

        if not tree_item:

            # If we do not know this item yet, schedule a rebuild.
            self.schedule_tree_refresh()
            return

        kind = tree_item.data(
            0,
            self.KIND_ROLE
        )

        if kind == self.KIND_NEX_ITEM:

            try:

                tree_item.setText(
                    0,
                    self.get_item_type_label(
                        item
                    )
                )

                tree_item.setText(
                    1,
                    self.get_item_title(
                        item
                    )
                )

                self.apply_row_style(
                    tree_item,
                    item
                )

            except Exception:
                pass

        self.schedule_filter_refresh()