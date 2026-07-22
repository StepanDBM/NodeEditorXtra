# TODO# NEx_SDBM/items/comment.py

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


class CommentTextEditor(QGraphicsTextItem):

    def __init__(
        self,
        comment
    ):
        super().__init__(
            comment
        )

        self.comment = comment

        self.setPlainText(
            comment.text
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
            10,
            8
        )

        self.setTextWidth(
            max(
                60,
                comment.width - 20
            )
        )

    def focusOutEvent(
        self,
        event
    ):

        super().focusOutEvent(
            event
        )

        self.comment.finish_text_edit(
            commit=True
        )

    def keyPressEvent(
        self,
        event
    ):

        if event.key() == Qt.Key_Escape:

            self.comment.finish_text_edit(
                commit=False
            )

            event.accept()
            return

        super().keyPressEvent(
            event
        )


class CommentItem(QGraphicsItem):

    def __init__(
        self,
        text="Comment",
        width=240,
        height=120
    ):
        super().__init__()

        self.nex_item_type = "comment"

        self.text = text

        self.width = width
        self.height = height
        self.roundness = 8

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

        self._hovered = False
        self._pressed = False

        self._dragging = False
        self._drag_start_mouse = None
        self._drag_start_pos = None

        self.text_editor = None

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
    # Geometry
    # -----------------------------------------------------

    def boundingRect(self):

        return QRectF(
            0,
            0,
            self.width,
            self.height
        )

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

    def get_paint_background_color(self):

        color = self.clone_color(
            self.background_color
        )

        if self._pressed:
            return color.lighter(
                145
            )

        if self._hovered:
            return color.lighter(
                120
            )

        return color

    def get_paint_border_color(self):

        if self._pressed:
            return self.selected_border_color

        if self.isSelected():
            return self.selected_border_color

        return self.border_color

    def pick_color(self):

        picked_color = QColorDialog.getColor(
            self.background_color,
            None,
            "Comment Color"
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

        self.update()

    # -----------------------------------------------------
    # Text editing
    # -----------------------------------------------------

    def start_text_edit(self):

        if self.text_editor:
            return

        self.text_editor = CommentTextEditor(
            self
        )

        self.text_editor.setFocus()

        self.update()

    def finish_text_edit(
        self,
        commit=True
    ):

        if not self.text_editor:
            return

        editor = self.text_editor
        self.text_editor = None

        if commit:

            new_text = (
                editor
                .toPlainText()
                .strip()
            )

            if new_text:
                self.text = new_text

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
    # Mouse events
    # -----------------------------------------------------

    def mousePressEvent(
        self,
        event
    ):

        self._pressed = True
        self.update()

        super().mousePressEvent(
            event
        )

        self._drag_start_mouse = (
            event.scenePos()
        )

        self._drag_start_pos = (
            self.pos()
        )

        self._dragging = False

        event.accept()

    def mouseReleaseEvent(
        self,
        event
    ):

        self._pressed = False
        self.update()

        self._dragging = False
        self._drag_start_mouse = None
        self._drag_start_pos = None

        super().mouseReleaseEvent(
            event
        )

    def mouseMoveEvent(
        self,
        event
    ):

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

        self.setPos(
            self._drag_start_pos
            + delta
        )

        event.accept()

    def mouseDoubleClickEvent(
        self,
        event
    ):

        self._pressed = False
        self.update()

        if event.modifiers() & Qt.ControlModifier:

            self.pick_color()

        else:

            self.start_text_edit()

        event.accept()

    def contextMenuEvent(
        self,
        event
    ):

        try:
            from PySide2.QtWidgets import QMenu

        except ImportError:
            from PySide6.QtWidgets import QMenu

        menu = QMenu()

        edit_action = menu.addAction(
            "Edit"
        )

        color_action = menu.addAction(
            "Color"
        )

        delete_action = menu.addAction(
            "Delete"
        )

        result = menu.exec_(
            event.screenPos()
        )

        if result == edit_action:
            self.start_text_edit()

        elif result == color_action:
            self.pick_color()

        elif result == delete_action:

            scene = self.scene()

            if scene:
                scene.removeItem(
                    self
                )

    # -----------------------------------------------------
    # Hover
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

        super().hoverLeaveEvent(
            event
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

        border_width = 2

        if self._pressed or self.isSelected():
            border_width = 3

        painter.setBrush(
            QBrush(
                self.get_paint_background_color()
            )
        )

        painter.setPen(
            QPen(
                self.get_paint_border_color(),
                border_width
            )
        )

        painter.drawRoundedRect(
            self.boundingRect(),
            self.roundness,
            self.roundness
        )

        if self.text_editor is None:

            font = painter.font()
            font.setPointSize(11)
            painter.setFont(font)

            text_rect = QRectF(
                10,
                8,
                self.width - 20,
                self.height - 16
            )

            painter.setPen(
                QColor(
                    255,
                    255,
                    255,
                    230
                )
            )

            painter.drawText(
                text_rect,
                Qt.TextWordWrap,
                self.text
            )