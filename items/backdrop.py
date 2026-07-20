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

import ui.backdrop_editor as BdE


class BackdropItem(QGraphicsItem):
    def __init__(
        self,
        title="Backdrop",
        width=300,
        height=180
    ):
        super().__init__()

        self._x_pressed = False
        self.contained_nodes = []
        self._dragging = False
        self._drag_start_mouse = None
        self._drag_start_pos = None
        self._resizing = False
        self._resize_edge = None
        self.resize_margin = 8

        self.title = title

        self.width = width
        self.height = height
        self.header_height = 35
        self.roundness = 4

        self.background_color = QColor(70, 120, 255, 80)
        self.header_color = QColor(50, 80, 180, 180)
        self.border_color = QColor(70, 150, 255)
        self.pressed_border_color = QColor(255, 180, 0)

        self.setFlag(QGraphicsItem.ItemIsMovable,False)
        self.setFlag(QGraphicsItem.ItemIsSelectable,True)
        self.setFlag(QGraphicsItem.ItemIsFocusable,True)
        self.setAcceptHoverEvents(True)

        self.close_size = 20
        self.close_padding = 8


    def clear_drag_state(self):

        self._dragging = False
        self._drag_start_mouse = None
        self._drag_start_pos = None
        self._x_pressed = False

    def get_close_rect(self):
        size = 18
        margin = 6

        return QRectF(
            self.width - size - margin,
            (35 - size) * 0.5,
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
    
    def is_in_drag_area(self, pos):
        if self.get_close_rect().contains(pos):
            return False

        return self.get_header_rect().contains(pos)
        
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


    def delete_self(self):

        scene = self.scene()

        if scene:
            scene.removeItem(self)

    def contextMenuEvent(
        self,
        event
    ):

        from PySide2.QtWidgets import (
            QMenu
        )

        menu = QMenu()

        delete_action = menu.addAction(
            "Delete"
        )

        result = menu.exec_(
            event.screenPos()
        )

        if result == delete_action:

            scene = self.scene()

            if scene:

                scene.removeItem(self)

    def mousePressEvent(
        self,
        event
    ):
        print("PRESS")

        self._x_pressed = (
            self.get_close_rect().contains(
                event.pos()
            )
        )
        edge = self.get_resize_edge(
            event.pos()
        )

        if edge:

            self._resizing = True

            self._resize_edge = edge

            self._resize_start_mouse = (
                event.scenePos()
            )

            self._start_width = (
                self.width
            )

            self._start_height = (
                self.height
            )

            event.accept()
            return

        if self._x_pressed:

            event.accept()
            return

        if self.is_in_drag_area(
            event.pos()
        ):

            self.update_contained_nodes()

            self._drag_start_mouse = event.scenePos()
            self._drag_start_pos = self.pos()
            self._dragging = False

            event.accept()

            return
        super().mousePressEvent(event)


    def mouseReleaseEvent(
        self,
        event
    ):
        print("RELEASE")
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

            return

        self.clear_drag_state()

        super().mouseReleaseEvent(event)
        
    def mouseDoubleClickEvent(
        self,
        event
    ):
        print("DOUBLE CLICK")
        self.clear_drag_state()
        
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

        self.setPos(new_pos)
        event.accept()

        import core.node_editor as NEx

        NEx.move_nodes(
            self.contained_nodes,
            move_delta.x(),
            move_delta.y()
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



    def boundingRect(self):

        return QRectF(
            0,
            0,
            self.width,
            self.height
        )

    def update_contained_nodes(self):

        import core.node_editor as NEx

        scene_map = NEx.get_scene_node_map()

        self.contained_nodes = []

        my_bounds = self.sceneBoundingRect()

        for node_name, item in scene_map.items():

            node_bounds = item.sceneBoundingRect()

            if my_bounds.contains(node_bounds):

                self.contained_nodes.append(
                    node_name
                )

    def paint(
        self,
        painter,
        option,
        widget
    ):

        painter.setRenderHint(QPainter.Antialiasing)

        background_color = self.background_color
        border_color = self.border_color

        if self.isSelected():
            border_color = self.pressed_border_color

        painter.setBrush(QBrush(background_color))
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(self.boundingRect(),
            self.roundness,
            self.roundness
        )

        header_rect = QRectF(
            0,
            0,
            self.width,
            self.header_height
        )

        painter.setBrush(self.header_color)

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

        painter.setBrush(QBrush(
                QColor(120, 30, 30)
            )
        )

        painter.setPen(
            QPen(
                QColor(255, 255, 255),
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

        for offset in (4, 8, 12):

            painter.drawLine(
                self.width - offset,
                self.height,
                self.width,
                self.height - offset
            )