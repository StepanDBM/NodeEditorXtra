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
        QHeaderView
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
        QHeaderView
    )


import NEx_SDBM.core.node_editor as NEx
import NEx_SDBM.core.scene_view as scene_view
import NEx_SDBM.core.utilities.events as events


class FocusListWidget(QWidget):

    ITEM_ROLE = Qt.UserRole
    KIND_ROLE = Qt.UserRole + 1

    KIND_NEX_ITEM = "nex_item"
    KIND_NATIVE_NODE = "native_node"

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

        self.build_ui()
        self.create_connections()

        self.refresh_tabs()
        self.refresh_tree()

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

        self.tree.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        self.tree.setEditTriggers(
            QAbstractItemView.SelectedClicked
            | QAbstractItemView.EditKeyPressed
        )

        layout.addWidget(
            self.tree
        )

    def create_connections(self):

        self.tab_combo.currentIndexChanged.connect(
            self.on_tab_combo_changed
        )

        self.tree.itemDoubleClicked.connect(
            self.on_item_double_clicked
        )

        self.tree.itemChanged.connect(
            self.on_tree_item_changed
        )

        bus = events.get_event_bus()

        bus.items_changed.connect(
            self.refresh_tree
        )

        bus.item_changed.connect(
            self.refresh_tree
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

        self.refresh_tree()

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

        self.refresh_tree()

    def on_tabs_changed(self):

        self.refresh_tabs()
        self.refresh_tree()

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

        return tree_item

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

    def resize_tree_columns(self):

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

        return tree_item

    def build_hierarchy(self):

        items = self.get_scene_nex_items()

        item_set = set(
            items
        )

        children_by_parent = {}
        roots = []

        # -----------------------------------------------------
        # NEx item hierarchy
        # -----------------------------------------------------

        for item in items:

            parent = self.get_parent_for_item(
                item,
                item_set
            )

            if parent is None:

                roots.append(
                    item
                )

            else:

                children_by_parent.setdefault(
                    parent,
                    []
                ).append(
                    item
                )

        # -----------------------------------------------------
        # Native Maya nodes under direct NEx container
        # -----------------------------------------------------

        containers = [
            item
            for item in items
            if getattr(
                item,
                "nex_container",
                False
            )
        ]

        native_nodes = self.get_scene_native_node_items()

        native_nodes_by_parent = {}

        for node_name, node_item in native_nodes:

            parent = self.get_direct_container_for_native_node(
                node_item,
                containers
            )

            if parent is None:
                continue

            native_nodes_by_parent.setdefault(
                parent,
                []
            ).append(
                (
                    node_name,
                    node_item
                )
            )

        roots = self.sort_items(
            roots
        )

        for parent, children in list(
            children_by_parent.items()
        ):

            children_by_parent[parent] = self.sort_items(
                children
            )

        for parent, nodes in list(
            native_nodes_by_parent.items()
        ):

            native_nodes_by_parent[parent] = sorted(
                nodes,
                key=lambda data: data[0].lower()
            )

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


    def refresh_tree(self):

        if self._refreshing:
            return

        self._refreshing = True

        try:

            self.tree.blockSignals(
                True
            )

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

        finally:

            self.tree.blockSignals(
                False
            )

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