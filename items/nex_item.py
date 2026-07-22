# NEx_SDBM/items/nex_item.py

try:
    from PySide2.QtWidgets import (
        QGraphicsItem,
        QColorDialog
    )

    from PySide2.QtGui import (
        QColor
    )

    from PySide2.QtCore import (
        QRectF,
        Qt
    )

except ImportError:
    from PySide6.QtWidgets import (
        QGraphicsItem,
        QColorDialog
    )

    from PySide6.QtGui import (
        QColor
    )

    from PySide6.QtCore import (
        QRectF,
        Qt
    )


import NEx_SDBM.core.node_editor as NEx


class NExGraphicsItem(QGraphicsItem):

    def __init__(
        self,
        width=240,
        height=120
    ):
        super().__init__()

        self.nex_item_type = "item"
        self.nex_parentable = True
        self.nex_container = False

        self.width = width
        self.height = height
        self.roundness = 6

        self.background_color = QColor(
            45,
            45,
            45,
            210
        )

        self.border_color = QColor(
            255,
            255,
            255,
            120
        )

        self.selected_border_color = QColor(
            90,
            255,
            130,
            240
        )

        self.normal_border_alpha = 180
        self.normal_border_darker_factor = 1000

        self.hover_lighter_factor = 120
        self.pressed_lighter_factor = 145

        self.normal_border_width = 2
        self.selected_border_width = 3
        self.pressed_border_width = 3


        self._hovered = False
        self._pressed = False

        self._dragging = False
        self._drag_start_mouse = None
        self._drag_start_pos = None

        self._resizing = False
        self._resize_edge = None
        self.resize_margin = 8
        self._resize_start_mouse = None
        self._start_width = width
        self._start_height = height

        self._drag_roots = []
        self._drag_tree = {}
        self._last_drag_delta = None
        self._drag_tree_cached = False

        self._hover_cursor_state = None

        self.setFlag(
            QGraphicsItem.ItemIsMovable,
            False
        )

        self.setFlag(
            QGraphicsItem.ItemIsSelectable,
            True
        )

        self.setFlag(
            QGraphicsItem.ItemIsFocusable,
            True
        )

        self.setAcceptHoverEvents(
            True
        )

        self.setAcceptedMouseButtons(
            Qt.LeftButton
            | Qt.RightButton
        )

    # -----------------------------------------------------
    # Generic geometry
    # -----------------------------------------------------

    def boundingRect(self):

        return QRectF(
            0,
            0,
            self.width,
            self.height
        )

    def get_area(self):

        return float(
            self.width
            * self.height
        )

    def set_size(
        self,
        width,
        height
    ):

        self.prepareGeometryChange()

        self.width = max(
            40,
            width
        )

        self.height = max(
            40,
            height
        )

        self.on_size_changed()

        self.update()

    def on_size_changed(self):

        pass

    # -----------------------------------------------------
    # Generic type checks
    # -----------------------------------------------------

    def is_nex_item(
        self,
        item
    ):

        return bool(
            getattr(
                item,
                "nex_item_type",
                None
            )
        )

    def is_parentable_nex_item(
        self,
        item
    ):

        return bool(
            getattr(
                item,
                "nex_parentable",
                False
            )
        )

    def is_container_nex_item(
        self,
        item
    ):

        return bool(
            getattr(
                item,
                "nex_container",
                False
            )
        )

    def get_scene_nex_items(self):

        scene = self.scene()

        if not scene:
            return []

        return [
            item
            for item in scene.items()
            if self.is_nex_item(item)
        ]

    def get_scene_parentable_items(self):

        return [
            item
            for item in self.get_scene_nex_items()
            if self.is_parentable_nex_item(item)
        ]

    def get_scene_container_items(self):

        return [
            item
            for item in self.get_scene_nex_items()
            if self.is_container_nex_item(item)
        ]


    # -----------------------------------------------------
    # Solver for scene chain reading in mouse-move-drag (avoid slow movement)
    # -----------------------------------------------------
    def resolve_node_items(
        self,
        node_names
    ):

        node_map = NEx.get_scene_node_map()

        node_items = []

        for node_name in node_names:

            item = node_map.get(
                node_name
            )

            if item:

                node_items.append(
                    item
                )

        return node_items

    # -----------------------------------------------------
    # Z-order hierarchy
    # -----------------------------------------------------

    def get_z_step(self):

        return 10


    def get_native_node_z_range(self):

        scene = self.scene()

        if not scene:
            return (
                0,
                0
            )

        z_values = []

        for item in scene.items():

            if self.is_nex_item(
                item
            ):
                continue

            try:

                node_name = NEx.get_node_name(
                    item
                )

            except RuntimeError:
                node_name = None

            except Exception:
                node_name = None

            if not node_name:
                continue

            try:

                z_values.append(
                    item.zValue()
                )

            except RuntimeError:
                pass

            except Exception:
                pass

        if not z_values:

            return (
                0,
                0
            )

        return (
            min(
                z_values
            ),
            max(
                z_values
            )
        )


    def get_container_z_base(self):

        native_min_z, native_max_z = (
            self.get_native_node_z_range()
        )

        return native_min_z - 1000


    def get_leaf_item_z_base(self):

        native_min_z, native_max_z = (
            self.get_native_node_z_range()
        )

        return native_max_z + 1000


    def get_hierarchy_depth_for_item(
        self,
        item
    ):

        depth = 0

        parent = self.get_parent_container_for_item(
            item
        )

        while parent:

            depth += 1

            parent = self.get_parent_container_for_item(
                parent
            )

        return depth


    def get_z_value_for_item(
        self,
        item
    ):

        depth = self.get_hierarchy_depth_for_item(
            item
        )

        if self.is_container_nex_item(
            item
        ):

            return (
                self.get_container_z_base()
                + (
                    depth
                    * self.get_z_step()
                )
            )

        return (
            self.get_leaf_item_z_base()
            + (
                depth
                * self.get_z_step()
            )
        )


    def update_z_for_item(
        self,
        item
    ):

        try:

            item.setZValue(
                self.get_z_value_for_item(
                    item
                )
            )

        except RuntimeError:
            pass

        except Exception:
            pass


    def update_z_hierarchy(self):

        scene = self.scene()

        if not scene:
            return

        nex_items = [
            item
            for item in scene.items()
            if self.is_nex_item(
                item
            )
        ]

        nex_items = sorted(
            nex_items,
            key=lambda item: self.get_hierarchy_depth_for_item(
                item
            )
        )

        for item in nex_items:

            self.update_z_for_item(
                item
            )
    # -----------------------------------------------------
    # Hierarchy
    # -----------------------------------------------------

    def contains_scene_rect(
        self,
        scene_rect
    ):

        try:

            return self.sceneBoundingRect().contains(
                scene_rect
            )

        except RuntimeError:
            return False

        except Exception:
            return False

    def get_parent_container_for_item(
        self,
        child_item
    ):

        try:

            child_rect = child_item.sceneBoundingRect()

        except RuntimeError:
            return None

        except Exception:
            return None

        candidates = []

        for container in self.get_scene_container_items():

            if container is child_item:
                continue

            try:

                if container.sceneBoundingRect().contains(
                    child_rect
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


    def get_parent_container(self):

        return self.get_parent_container_for_item(
            self
        )


    def is_item_descendant_of(
        self,
        child_item,
        possible_parent
    ):

        parent = self.get_parent_container_for_item(
            child_item
        )

        while parent:

            if parent is possible_parent:
                return True

            parent = self.get_parent_container_for_item(
                parent
            )

        return False


    def is_descendant_of(
        self,
        possible_parent
    ):

        return self.is_item_descendant_of(
            self,
            possible_parent
        )


    def get_direct_child_nex_items(self):

        children = []

        for item in self.get_scene_parentable_items():

            if item is self:
                continue

            parent = self.get_parent_container_for_item(
                item
            )

            if parent is self:

                children.append(
                    item
                )

        return children

    def filter_top_level_items(
        self,
        items
    ):

        roots = []

        for item in items:

            has_selected_parent = False

            for other in items:

                if other is item:
                    continue

                try:

                    if self.is_item_descendant_of(
                        item,
                        other
                    ):

                        has_selected_parent = True
                        break

                except Exception:
                    pass

            if not has_selected_parent:

                roots.append(
                    item
                )

        return roots


    # -----------------------------------------------------
    # Container hooks
    # -----------------------------------------------------

    def get_direct_node_names(self):

        return []

    def update_direct_contents(self):

        self.contained_nodes = (
            self.get_direct_node_names()
        )

        self.child_nex_items = (
            self.get_direct_child_nex_items()
        )

    def cache_subtree_for_drag(
        self,
        item
    ):

        if item in self._drag_tree:
            return

        node_names = []
        node_items = []
        children = []

        try:

            if self.is_container_nex_item(
                item
            ):

                item.update_direct_contents()

                node_names = list(
                    getattr(
                        item,
                        "contained_nodes",
                        []
                    )
                )

                node_items = self.resolve_node_items(
                    node_names
                )

                children = list(
                    getattr(
                        item,
                        "child_nex_items",
                        []
                    )
                )

        except Exception:

            node_names = []
            node_items = []
            children = []

        self._drag_tree[item] = {
            "start_pos": item.pos(),
            "node_names": node_names,
            "node_items": node_items,
            "children": children
        }

        for child in children:

            self.cache_subtree_for_drag(
                child
            )

    def cache_drag_tree(self):

        scene = self.scene()

        if not scene:
            return

        selected_items = [
            item
            for item in scene.selectedItems()
            if self.is_nex_item(item)
        ]

        if self not in selected_items:

            selected_items.append(
                self
            )

        self._drag_roots = (
            self.filter_top_level_items(
                selected_items
            )
        )

        self._drag_tree = {}

        for root in self._drag_roots:

            self.cache_subtree_for_drag(
                root
            )

        self._last_drag_delta = None

    def apply_subtree_drag_delta(
        self,
        item,
        total_delta,
        incremental_delta
    ):

        data = self._drag_tree.get(
            item
        )

        if not data:
            return

        item.setPos(
            data["start_pos"]
            + total_delta
        )

        node_items = data.get(
            "node_items",
            []
        )

        for node_item in node_items:

            try:

                node_item.moveBy(
                    incremental_delta.x(),
                    incremental_delta.y()
                )

            except RuntimeError:
                pass

            except Exception:
                pass

        for child in data.get(
            "children",
            []
        ):

            self.apply_subtree_drag_delta(
                child,
                total_delta,
                incremental_delta
            )

    # -----------------------------------------------------
    # Resize
    # -----------------------------------------------------

    def get_resize_edge(
        self,
        pos
    ):

        right = (
            abs(
                pos.x() - self.width
            )
            <= self.resize_margin
        )

        bottom = (
            abs(
                pos.y() - self.height
            )
            <= self.resize_margin
        )

        if right and bottom:
            return "bottom_right"

        if right:
            return "right"

        if bottom:
            return "bottom"

        return None

    def can_resize_from_pos(
        self,
        pos
    ):

        return bool(
            self.get_resize_edge(
                pos
            )
        )

    # -----------------------------------------------------
    # Drag
    # -----------------------------------------------------

    def can_drag_from_pos(
        self,
        pos
    ):

        return self.boundingRect().contains(
            pos
        )

    def clear_interaction_state(self):

        self._dragging = False
        self._drag_start_mouse = None
        self._drag_start_pos = None

        self._resizing = False
        self._resize_edge = None
        self._resize_start_mouse = None

        self._drag_roots = []
        self._drag_tree = {}
        self._last_drag_delta = None
        self._drag_tree_cached = False

    # -----------------------------------------------------
    # Color
    # -----------------------------------------------------

    def clone_color(
        self,
        color
    ):

        return QColor(
            color.red(),
            color.green(),
            color.blue(),
            color.alpha()
        )


    def get_hover_background_color(self):

        color = self.clone_color(
            self.background_color
        )

        return color.lighter(
            self.hover_lighter_factor
        )


    def get_pressed_background_color(self):

        color = self.clone_color(
            self.background_color
        )

        return color.lighter(
            self.pressed_lighter_factor
        )


    def get_normal_border_color(self):

        color = self.clone_color(
            self.background_color
        )

        color.setAlpha(
            self.normal_border_alpha
        )

        return color.darker(
            self.normal_border_darker_factor
        )


    def get_selected_border_color(self):

        return self.selected_border_color


    def get_pressed_border_color(self):

        return self.selected_border_color


    def get_paint_background_color(self):

        if self._pressed:

            return self.get_pressed_background_color()

        if self._hovered:

            return self.get_hover_background_color()

        return self.background_color


    def get_paint_border_color(self):

        if self._pressed:

            return self.get_pressed_border_color()

        if self.isSelected():

            return self.get_selected_border_color()

        return self.get_normal_border_color()


    def get_paint_border_width(self):

        if self._pressed:

            return self.pressed_border_width

        if self.isSelected():

            return self.selected_border_width

        return self.normal_border_width

    def pick_color(self):

        picked_color = QColorDialog.getColor(
            self.background_color,
            None,
            "NEx Item Color"
        )

        if not picked_color.isValid():
            return

        alpha = self.background_color.alpha()

        self.background_color = QColor(
            picked_color.red(),
            picked_color.green(),
            picked_color.blue(),
            alpha
        )

        self.on_color_changed(
            picked_color
        )

        self.update()

    def on_color_changed(
        self,
        picked_color
    ):

        pass

    # -----------------------------------------------------
    # Mouse events
    # -----------------------------------------------------

    def mousePressEvent(
        self,
        event
    ):

        self._pressed = True
        self.update()

        edge = self.get_resize_edge(
            event.pos()
        )

        super().mousePressEvent(
            event
        )

        if edge:

            self._resizing = True
            self._resize_edge = edge
            self._resize_start_mouse = event.scenePos()
            self._start_width = self.width
            self._start_height = self.height

            event.accept()
            return

        if self.can_drag_from_pos(
            event.pos()
        ):

            self._drag_start_mouse = (
                event.scenePos()
            )

            self._drag_start_pos = (
                self.pos()
            )

            self._dragging = False
            self._drag_tree_cached = False

            event.accept()
            return

    def mouseReleaseEvent(
        self,
        event
    ):

        self._pressed = False
        self.update()

        self.setCursor(
            Qt.ArrowCursor
        )

        if self._resizing:

            self._resizing = False
            self._resize_edge = None
            self._drag_tree_cached = False

            event.accept()
            return

        self.clear_interaction_state()
        self.update_z_hierarchy()
        super().mouseReleaseEvent(
            event
        )

    def mouseMoveEvent(
        self,
        event
    ):

        if self._resizing:

            delta = (
                event.scenePos()
                - self._resize_start_mouse
            )

            self.setCursor(
                Qt.ClosedHandCursor
            )

            if self._resize_edge == "right":

                self.set_size(
                    self._start_width + delta.x(),
                    self.height
                )

            elif self._resize_edge == "bottom":

                self.set_size(
                    self.width,
                    self._start_height + delta.y()
                )

            elif self._resize_edge == "bottom_right":

                self.set_size(
                    self._start_width + delta.x(),
                    self._start_height + delta.y()
                )

            event.accept()
            return

        if self._drag_start_mouse is None:
            return

        if not self._dragging:

            move_distance = (
                event.scenePos()
                - self._drag_start_mouse
            ).manhattanLength()

            if move_distance < 4:
                return

            self._dragging = True

            if not self._drag_tree_cached:

                self.cache_drag_tree()

                self._drag_tree_cached = True

        delta = (
            event.scenePos()
            - self._drag_start_mouse
        )

        if self._last_drag_delta is None:

            incremental_delta = delta

        else:

            incremental_delta = (
                delta
                - self._last_drag_delta
            )

        self._last_drag_delta = delta

        for root in self._drag_roots:

            try:

                self.apply_subtree_drag_delta(
                    root,
                    delta,
                    incremental_delta
                )

            except RuntimeError:
                pass

            except Exception:
                pass

        event.accept()

    def mouseDoubleClickEvent(
        self,
        event
    ):

        if event.button() != Qt.LeftButton:

            event.accept()
            return

        self._pressed = False
        self.update()

        self.pick_color()

        event.accept()

    # -----------------------------------------------------
    # Hover
    # -----------------------------------------------------

    def hoverEnterEvent(
        self,
        event
    ):

        if not self._hovered:

            self._hovered = True
            self.update()

        super().hoverEnterEvent(
            event
        )

    def hoverLeaveEvent(
        self,
        event
    ):

        changed = False

        if self._hovered:

            self._hovered = False
            changed = True

        if self._pressed:

            self._pressed = False
            changed = True

        self._hover_cursor_state = None

        self.setCursor(
            Qt.ArrowCursor
        )

        if changed:

            self.update()

        super().hoverLeaveEvent(
            event
        )

    def hoverMoveEvent(
        self,
        event
    ):

        edge = self.get_resize_edge(
            event.pos()
        )

        if edge == "right":

            cursor_state = "resize_right"
            cursor = Qt.SizeHorCursor

        elif edge == "bottom":

            cursor_state = "resize_bottom"
            cursor = Qt.SizeVerCursor

        elif edge == "bottom_right":

            cursor_state = "resize_bottom_right"
            cursor = Qt.SizeFDiagCursor

        elif self.can_drag_from_pos(
            event.pos()
        ):

            cursor_state = "drag"
            cursor = Qt.OpenHandCursor

        else:

            cursor_state = "default"
            cursor = Qt.ArrowCursor

        if cursor_state != self._hover_cursor_state:

            self._hover_cursor_state = cursor_state

            self.setCursor(
                cursor
            )

        super().hoverMoveEvent(
            event
        )