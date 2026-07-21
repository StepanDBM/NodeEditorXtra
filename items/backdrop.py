# NEx_SDBM/items/backdrop.py

try:
    from PySide2.QtWidgets import (
        QGraphicsItem,
        QGraphicsTextItem,
        QColorDialog
    )

    from PySide2.QtGui import (
        QColor,
        QBrush,
        QPen,
        QPainter
    )

    from PySide2.QtCore import (
        QRectF,
        Qt
    )

except ImportError:
    from PySide6.QtWidgets import (
        QGraphicsItem,
        QGraphicsTextItem,
        QColorDialog
    )

    from PySide6.QtGui import (
        QColor,
        QBrush,
        QPen,
        QPainter
    )

    from PySide6.QtCore import (
        QRectF,
        Qt
    )


import NEx_SDBM.core.node_editor as NEx


class BackdropTitleEditor(QGraphicsTextItem):

    def __init__(
        self,
        backdrop
    ):
        super().__init__(
            backdrop
        )

        self.backdrop = backdrop

        self.setPlainText(
            backdrop.title
        )

        self.setTextInteractionFlags(
            Qt.TextEditorInteraction
        )

        self.setDefaultTextColor(
            QColor(
                255,
                255,
                255
            )
        )

        self.setZValue(
            999
        )

        self.setPos(
            8,
            5
        )

        self.setTextWidth(
            max(
                50,
                backdrop.width - 45
            )
        )

    def focusOutEvent(
        self,
        event
    ):

        super().focusOutEvent(
            event
        )

        self.backdrop.finish_title_edit(
            commit=True
        )

    def keyPressEvent(
        self,
        event
    ):

        if event.key() in (
            Qt.Key_Return,
            Qt.Key_Enter
        ):

            self.backdrop.finish_title_edit(
                commit=True
            )

            event.accept()
            return

        if event.key() == Qt.Key_Escape:

            self.backdrop.finish_title_edit(
                commit=False
            )

            event.accept()
            return

        super().keyPressEvent(
            event
        )


class BackdropItem(QGraphicsItem):

    def __init__(
        self,
        title="Backdrop",
        width=300,
        height=180
    ):
        super().__init__()

        self.nex_item_type = "backdrop"

        self._x_pressed = False

        self.contained_nodes = []

        self._dragging = False
        self._drag_start_mouse = None
        self._drag_start_pos = None

        self._resizing = False
        self._resize_edge = None
        self.resize_margin = 8

        self._hovered = False
        self._pressed = False

        self._multi_drag_start_positions = {}

        self._drag_roots = []
        self._drag_tree = {}
        self._last_drag_delta = None

        self.title_editor = None

        self.title = title

        self.width = width
        self.height = height
        self.header_height = 35
        self.roundness = 4

        self.background_color = QColor(
            70,
            120,
            255,
            80
        )

        self.header_color = QColor(
            50,
            80,
            180,
            180
        )

        self.border_color = QColor(
            70,
            150,
            255
        )

        self.pressed_border_color = QColor(
            255,
            180,
            0
        )

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

        self.close_size = 20
        self.close_padding = 8

    # -----------------------------------------------------
    # Hierarchy helpers
    # -----------------------------------------------------

    def get_scene_backdrops(self):

        scene = self.scene()

        if not scene:
            return []

        return [
            item
            for item in scene.items()
            if self.is_backdrop_item(item)
        ]


    def get_backdrop_area(self):

        return float(
            self.width
            * self.height
        )


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


    def find_smallest_owner_for_rect(
        self,
        scene_rect
    ):

        candidates = []

        for backdrop in self.get_scene_backdrops():

            if backdrop.contains_scene_rect(
                scene_rect
            ):

                candidates.append(
                    backdrop
                )

        if not candidates:
            return None

        candidates = sorted(
            candidates,
            key=lambda item: item.get_backdrop_area()
        )

        return candidates[0]


    def get_parent_backdrop(self):

        my_rect = self.sceneBoundingRect()

        candidates = []

        for backdrop in self.get_scene_backdrops():

            if backdrop is self:
                continue

            if backdrop.contains_scene_rect(
                my_rect
            ):

                candidates.append(
                    backdrop
                )

        if not candidates:
            return None

        candidates = sorted(
            candidates,
            key=lambda item: item.get_backdrop_area()
        )

        return candidates[0]


    def get_direct_child_backdrops(self):

        children = []

        for backdrop in self.get_scene_backdrops():

            if backdrop is self:
                continue

            parent = backdrop.get_parent_backdrop()

            if parent is self:

                children.append(
                    backdrop
                )

        return children


    def get_direct_node_names(self):

        direct_nodes = []

        scene_map = NEx.get_scene_node_map()

        for node_name, item in scene_map.items():

            try:

                node_rect = item.sceneBoundingRect()

            except RuntimeError:
                continue

            except Exception:
                continue

            owner = self.find_smallest_owner_for_rect(
                node_rect
            )

            if owner is self:

                direct_nodes.append(
                    node_name
                )

        return direct_nodes


    def update_direct_contents(self):

        self.contained_nodes = (
            self.get_direct_node_names()
        )

        self.child_backdrops = (
            self.get_direct_child_backdrops()
        )

    # -----------------------------------------------------
    # Drag-tree helpers
    # -----------------------------------------------------
    def is_descendant_of(
        self,
        possible_parent
    ):

        parent = self.get_parent_backdrop()

        while parent:

            if parent is possible_parent:
                return True

            parent = parent.get_parent_backdrop()

        return False


    def filter_top_level_backdrops(
        self,
        backdrops
    ):

        roots = []

        for backdrop in backdrops:

            has_selected_parent = False

            for other in backdrops:

                if other is backdrop:
                    continue

                if backdrop.is_descendant_of(
                    other
                ):

                    has_selected_parent = True
                    break

            if not has_selected_parent:

                roots.append(
                    backdrop
                )

        return roots


    def cache_subtree_for_drag(
        self,
        backdrop
    ):

        if backdrop in self._drag_tree:
            return

        backdrop.update_direct_contents()

        children = list(
            getattr(
                backdrop,
                "child_backdrops",
                []
            )
        )

        self._drag_tree[backdrop] = {
            "start_pos": backdrop.pos(),
            "nodes": list(
                getattr(
                    backdrop,
                    "contained_nodes",
                    []
                )
            ),
            "children": children
        }

        for child in children:

            self.cache_subtree_for_drag(
                child
            )


    def cache_multi_drag_positions(self):

        selected_backdrops = (
            self.get_selected_backdrops()
        )

        if self not in selected_backdrops:

            selected_backdrops.append(
                self
            )

        self._drag_roots = (
            self.filter_top_level_backdrops(
                selected_backdrops
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
        backdrop,
        total_delta,
        incremental_delta
    ):

        data = self._drag_tree.get(
            backdrop
        )

        if not data:
            return

        start_pos = data["start_pos"]

        backdrop.setPos(
            start_pos + total_delta
        )

        NEx.move_nodes(
            data["nodes"],
            incremental_delta.x(),
            incremental_delta.y()
        )

        for child in data["children"]:

            self.apply_subtree_drag_delta(
                child,
                total_delta,
                incremental_delta
            )

    # -----------------------------------------------------
    # State
    # -----------------------------------------------------

    def clear_drag_state(self):

        self._dragging = False
        self._drag_start_mouse = None
        self._drag_start_pos = None
        self._x_pressed = False
        self._multi_drag_start_positions = {}

        self._drag_roots = []
        self._drag_tree = {}
        self._last_drag_delta = None


    # -----------------------------------------------------
    # Rects
    # -----------------------------------------------------

    def get_title_rect(self):

        return QRectF(
            8,
            0,
            self.width - 45,
            self.header_height
        )

    def get_close_rect(self):

        size = 18
        margin = 6

        return QRectF(
            self.width - size - margin,
            (self.header_height - size) * 0.5,
            size,
            size
        )

    def get_header_rect(self):

        return QRectF(
            0,
            0,
            self.width,
            self.header_height
        )

    def is_in_drag_area(
        self,
        pos
    ):

        if self.get_close_rect().contains(
            pos
        ):
            return False

        return self.get_header_rect().contains(
            pos
        )

    def is_inside_backdrop(
        self,
        pos
    ):

        return self.boundingRect().contains(
            pos
        )

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

    # -----------------------------------------------------
    # Selection helpers
    # -----------------------------------------------------

    def is_backdrop_item(
        self,
        item
    ):

        return (
            getattr(
                item,
                "nex_item_type",
                None
            )
            == "backdrop"
        )

    def get_selected_backdrops(self):

        scene = self.scene()

        if not scene:
            return []

        return [
            item
            for item in scene.selectedItems()
            if self.is_backdrop_item(item)
        ]

    # -----------------------------------------------------
    # Color helpers
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
            120
        )

    def get_pressed_background_color(self):

        color = self.clone_color(
            self.background_color
        )

        return color.lighter(
            145
        )

    def get_hover_header_color(self):

        color = self.clone_color(
            self.header_color
        )

        return color.lighter(
            120
        )

    def get_pressed_header_color(self):

        color = self.clone_color(
            self.header_color
        )

        return color.lighter(
            150
        )

    def get_soft_selection_color(self):

        color = self.clone_color(
            self.background_color
        )

        color.setAlpha(
            210
        )

        return color.lighter(
            180
        )

    def get_pressed_selection_color(self):

        return QColor(
            90,
            255,
            130,
            240
        )

    def get_paint_background_color(self):

        if self._pressed:
            return self.get_pressed_background_color()

        if self._hovered:
            return self.get_hover_background_color()

        return self.background_color

    def get_paint_header_color(self):

        if self._pressed:
            return self.get_pressed_header_color()

        if self._hovered:
            return self.get_hover_header_color()

        return self.header_color

    def get_paint_border_color(self):

        if self._pressed:
            return self.get_pressed_selection_color()

        if self.isSelected():
            return self.get_soft_selection_color()

        color = self.clone_color(
            self.background_color
        )

        color.setAlpha(
            150
        )

        return color.lighter(
            130
        )

    def pick_backdrop_color(self):

        picked_color = QColorDialog.getColor(
            self.background_color,
            None,
            "Backdrop Color"
        )

        if not picked_color.isValid():
            return

        background_alpha = (
            self.background_color.alpha()
        )

        header_alpha = (
            self.header_color.alpha()
        )

        self.background_color = QColor(
            picked_color.red(),
            picked_color.green(),
            picked_color.blue(),
            background_alpha
        )

        header_color = QColor(
            picked_color
        ).darker(
            160
        )

        header_color.setAlpha(
            header_alpha
        )

        self.header_color = header_color

        self.update()

    # -----------------------------------------------------
    # Title editing
    # -----------------------------------------------------

    def start_title_edit(self):

        if self.title_editor:
            return

        self.title_editor = BackdropTitleEditor(
            self
        )

        self.title_editor.setFocus()

        self.update()

    def finish_title_edit(
        self,
        commit=True
    ):

        if not self.title_editor:
            return

        editor = self.title_editor
        self.title_editor = None

        if commit:

            new_title = (
                editor
                .toPlainText()
                .strip()
            )

            if new_title:
                self.title = new_title

        scene = self.scene()

        try:

            editor.setParentItem(
                None
            )

            if scene:
                scene.removeItem(
                    editor
                )

        except RuntimeError:
            pass

        except Exception:
            pass

        self.update()

    # -----------------------------------------------------
    # Deletion
    # -----------------------------------------------------

    def delete_self(self):

        scene = self.scene()

        if scene:
            scene.removeItem(
                self
            )

    def contextMenuEvent(
        self,
        event
    ):

        try:
            from PySide2.QtWidgets import QMenu

        except ImportError:
            from PySide6.QtWidgets import QMenu

        menu = QMenu()

        delete_action = menu.addAction(
            "Delete"
        )

        result = menu.exec_(
            event.screenPos()
        )

        if result == delete_action:
            self.delete_self()

    # -----------------------------------------------------
    # Mouse events
    # -----------------------------------------------------

    def mousePressEvent(
        self,
        event
    ):

        self._pressed = True
        self.update()

        self._x_pressed = (
            self.get_close_rect().contains(
                event.pos()
            )
        )

        edge = self.get_resize_edge(
            event.pos()
        )

        inside_header = self.is_in_drag_area(
            event.pos()
        )

        inside_backdrop = self.is_inside_backdrop(
            event.pos()
        )

        super().mousePressEvent(
            event
        )

        if edge:

            self._resizing = True
            self._resize_edge = edge

            self._resize_start_mouse = (
                event.scenePos()
            )

            self._start_width = self.width
            self._start_height = self.height

            event.accept()
            return

        if self._x_pressed:

            event.accept()
            return

        if inside_header:

            self.update_contained_nodes()

            self._drag_start_mouse = (
                event.scenePos()
            )

            self._drag_start_pos = (
                self.pos()
            )

            self._dragging = False

            self.cache_multi_drag_positions()

            event.accept()
            return

        if inside_backdrop:

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

            event.accept()
            return

        if self._x_pressed:

            self._x_pressed = False

            if self.get_close_rect().contains(
                event.pos()
            ):
                self.delete_self()

            event.accept()
            return

        self.clear_drag_state()

        super().mouseReleaseEvent(
            event
        )

    def mouseDoubleClickEvent(
        self,
        event
    ):

        self.clear_drag_state()

        self._pressed = False
        self.update()

        if self.get_title_rect().contains(
            event.pos()
        ):

            self.start_title_edit()

            event.accept()
            return

        self.pick_backdrop_color()

        event.accept()

    def mouseMoveEvent(
        self,
        event
    ):

        # -----------------------------------------------------
        # Resize
        # -----------------------------------------------------

        if self._resizing:

            delta = (
                event.scenePos()
                - self._resize_start_mouse
            )

            self.setCursor(
                Qt.ClosedHandCursor
            )

            self.prepareGeometryChange()

            if self._resize_edge == "right":

                self.width = max(
                    100,
                    self._start_width
                    + delta.x()
                )

            elif self._resize_edge == "bottom":

                self.height = max(
                    60,
                    self._start_height
                    + delta.y()
                )

            elif self._resize_edge == "bottom_right":

                self.width = max(
                    100,
                    self._start_width
                    + delta.x()
                )

                self.height = max(
                    60,
                    self._start_height
                    + delta.y()
                )

            self.update()

            event.accept()
            return

        # -----------------------------------------------------
        # Drag
        # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Hover events
    # -----------------------------------------------------

    def hoverEnterEvent(
        self,
        event
    ):

        self._hovered = True
        self.update()

        super().hoverEnterEvent(
            event
        )

    def hoverLeaveEvent(
        self,
        event
    ):

        self._hovered = False
        self._pressed = False
        self.update()

        self.setCursor(
            Qt.ArrowCursor
        )

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

            self.setCursor(
                Qt.SizeHorCursor
            )

        elif edge == "bottom":

            self.setCursor(
                Qt.SizeVerCursor
            )

        elif edge == "bottom_right":

            self.setCursor(
                Qt.SizeFDiagCursor
            )

        elif self.is_in_drag_area(
            event.pos()
        ):

            self.setCursor(
                Qt.OpenHandCursor
            )

        else:

            self.setCursor(
                Qt.ArrowCursor
            )

        super().hoverMoveEvent(
            event
        )

    # -----------------------------------------------------
    # Geometry / Membership
    # -----------------------------------------------------

    def boundingRect(self):

        return QRectF(
            0,
            0,
            self.width,
            self.height
        )

    def update_contained_nodes(self):

        self.update_direct_contents()

    # -----------------------------------------------------
    # Paint
    # -----------------------------------------------------

    def paint(
        self,
        painter,
        option,
        widget
    ):

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        background_color = (
            self.get_paint_background_color()
        )

        header_color = (
            self.get_paint_header_color()
        )

        border_color = (
            self.get_paint_border_color()
        )

        border_width = 2

        if self._pressed:
            border_width = 3

        elif self.isSelected():
            border_width = 3

        painter.setBrush(
            QBrush(
                background_color
            )
        )

        painter.setPen(
            QPen(
                border_color,
                border_width
            )
        )

        painter.drawRoundedRect(
            self.boundingRect(),
            self.roundness,
            self.roundness
        )

        header_rect = QRectF(
            0,
            0,
            self.width,
            self.header_height
        )

        painter.setBrush(
            header_color
        )

        painter.drawRoundedRect(
            header_rect,
            self.roundness,
            self.roundness
        )

        if self.title_editor is None:

            font = painter.font()
            font.setPointSize(14)
            font.setBold(True)
            painter.setFont(font)

            painter.drawText(
                10,
                25,
                self.title
            )

        close_rect = self.get_close_rect()

        painter.setBrush(
            QBrush(
                QColor(
                    255,
                    255,
                    255,
                    210
                )
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    40,
                    40,
                    40,
                    180
                ),
                1
            )
        )

        painter.drawRoundedRect(
            close_rect,
            6,
            6
        )

        painter.drawText(
            close_rect,
            Qt.AlignCenter,
            "X"
        )

        painter.setPen(
            QColor(
                255,
                255,
                255,
                120
            )
        )

        for offset in (
            4,
            8,
            12
        ):

            painter.drawLine(
                self.width - offset,
                self.height,
                self.width,
                self.height - offset
            )