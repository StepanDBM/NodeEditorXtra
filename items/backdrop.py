# NEx_SDBM/items/backdrop.py

try:
    from PySide2.QtWidgets import QGraphicsItem

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
    from PySide6.QtWidgets import QGraphicsItem

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


import NEx_SDBM.ui.backdrop_editor as BdE
import NEx_SDBM.core.node_editor as NEx


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
    # State
    # -----------------------------------------------------

    def clear_drag_state(self):

        self._dragging = False
        self._drag_start_mouse = None
        self._drag_start_pos = None
        self._x_pressed = False
        self._multi_drag_start_positions = {}

    # -----------------------------------------------------
    # Rects
    # -----------------------------------------------------

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

    def cache_multi_drag_positions(self):

        self._multi_drag_start_positions = {}

        for item in self.get_selected_backdrops():

            try:

                item.update_contained_nodes()

            except Exception:
                pass

            if item is self:
                continue

            self._multi_drag_start_positions[item] = (
                item.pos()
            )

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

        # Let Qt/Maya handle selection first.
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

        editor = BdE.BackdropEditor(
            backdrop=self
        )

        editor.exec_()

        event.accept()

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

        new_pos = (
            self._drag_start_pos
            + delta
        )

        move_delta = (
            new_pos
            - self.pos()
        )

        self.setPos(
            new_pos
        )

        NEx.move_nodes(
            self.contained_nodes,
            move_delta.x(),
            move_delta.y()
        )

        for item, start_pos in self._multi_drag_start_positions.items():

            try:

                target_pos = (
                    start_pos
                    + delta
                )

                item_move_delta = (
                    target_pos
                    - item.pos()
                )

                item.setPos(
                    target_pos
                )

                NEx.move_nodes(
                    item.contained_nodes,
                    item_move_delta.x(),
                    item_move_delta.y()
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

        scene_map = NEx.get_scene_node_map()

        self.contained_nodes = []

        my_bounds = self.sceneBoundingRect()

        for node_name, item in scene_map.items():

            node_bounds = item.sceneBoundingRect()

            if my_bounds.contains(
                node_bounds
            ):

                self.contained_nodes.append(
                    node_name
                )

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
                    120,
                    30,
                    30
                )
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    255,
                    255,
                    255
                ),
                1
            )
        )

        painter.drawRoundedRect(
            close_rect,
            4,
            4
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