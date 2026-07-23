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
        QTreeWidgetItem
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
        QTreeWidgetItem
    )


import NEx_SDBM.core.node_editor as NEx
import NEx_SDBM.core.scene_view as scene_view
import NEx_SDBM.core.utilities.events as events


class FocusListWidget(QWidget):

    ITEM_ROLE = Qt.UserRole

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

        self.tree.itemCollapsed.connect(
            self.on_item_collapsed
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

    def build_hierarchy(self):

        items = self.get_scene_nex_items()

        item_set = set(
            items
        )

        children_by_parent = {}
        roots = []

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

        roots = self.sort_items(
            roots
        )

        for parent, children in list(
            children_by_parent.items()
        ):

            children_by_parent[parent] = self.sort_items(
                children
            )

        return roots, children_by_parent

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

        tree_item.setFlags(
            tree_item.flags()
            | Qt.ItemIsEditable
        )

        self.apply_row_style(
            tree_item,
            nex_item
        )

        return tree_item

    def refresh_tree(self):

        if self._refreshing:
            return

        self._refreshing = True

        try:

            self.tree.blockSignals(
                True
            )

            self.tree.clear()

            roots, children_by_parent = (
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
                    children_by_parent
                )

            self.tree.expandAll()

            self.tree.resizeColumnToContents(
                0
            )

        finally:

            self.tree.blockSignals(
                False
            )

            self._refreshing = False

    def populate_children(
        self,
        parent_tree_item,
        parent_nex_item,
        children_by_parent
    ):

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
                children_by_parent
            )

    # -----------------------------------------------------
    # Tree events
    # -----------------------------------------------------

    def on_item_collapsed(
        self,
        tree_item
    ):

        self.tree.expandItem(
            tree_item
        )

    def on_item_double_clicked(
        self,
        tree_item,
        column
    ):

        nex_item = tree_item.data(
            0,
            self.ITEM_ROLE
        )

        if not nex_item:
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
                nex_item
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