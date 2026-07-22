# NEx_SDBM/items/comment.py

try:
    from PySide2.QtWidgets import (
        QGraphicsTextItem
    )
    from PySide2.QtGui import (
        QColor,
        QBrush,
        QPen,
        QPainter,
        QTextDocument,
        QTextOption
    )
    from PySide2.QtCore import (
        QRectF,
        Qt
    )

except ImportError:
    from PySide6.QtWidgets import (
        QGraphicsTextItem
    )

    from PySide6.QtGui import (
        QColor,
        QBrush,
        QPen,
        QPainter,
        QTextDocument,
        QTextOption
    )

    from PySide6.QtCore import (
        QRectF,
        Qt
    )


from NEx_SDBM.items.nex_item import (
    NExGraphicsItem
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

        text_rect = comment.get_text_rect()

        self.setPos(
            text_rect.left(),
            text_rect.top()
        )

        self.setTextWidth(
            max(
                60,
                text_rect.width()
            )
        )
        self.document().setDefaultTextOption(
            comment.get_text_option()
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
    def mouseDoubleClickEvent(
        self,
        event
    ):

        if event.button() != Qt.LeftButton:

            event.accept()
            return

        super().mouseDoubleClickEvent(
            event
        )


    def contextMenuEvent(
        self,
        event
    ):

        event.accept()


class CommentItem(NExGraphicsItem):

    def __init__(
        self,
        text="Comment",
        width=240,
        height=120
    ):
        super().__init__(
            width=width,
            height=height
        )

        self.nex_item_type = "comment"
        self.nex_parentable = True
        self.nex_container = False

        self.text = text
        self.text_editor = None

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

    # -----------------------------------------------------
    # Size hook
    # -----------------------------------------------------

    def on_size_changed(self):

        if self.text_editor:

            self.text_editor.setTextWidth(
                max(
                    60,
                    self.width - 20
                )
            )

    # -----------------------------------------------------
    # Color helpers
    # -----------------------------------------------------


    def get_color_rect(self):
        return QRectF(
            self.width - 30,
            7,
            20,
            20
        )


    def get_text_rect(self):

        return QRectF(
            10,
            34,
            self.width - 20,
            self.height - 42
        )

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


    def get_text_option(self):

        option = QTextOption()

        option.setWrapMode(
            QTextOption.WrapAnywhere
        )

        option.setAlignment(
            Qt.AlignJustify
        )

        return option


    # -----------------------------------------------------
    # Mouse events
    # -----------------------------------------------------

    def mouseDoubleClickEvent(
        self,
        event
    ):

        if event.button() != Qt.LeftButton:

            event.accept()
            return

        self.clear_interaction_state()

        self._pressed = False
        self.update()

        if self.get_color_rect().contains(
            event.pos()
        ):

            self.pick_color()

            event.accept()
            return

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

        border_width = self.get_paint_border_width()

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
        color_rect = self.get_color_rect()

        painter.setBrush(
            QBrush(
                self.background_color.lighter(
                    130
                )
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    255,
                    255,
                    255,
                    180
                ),
                1
            )
        )

        painter.drawRoundedRect(
            color_rect,
            4,
            4
        )
        if self.text_editor is None:

            font = painter.font()
            font.setPointSize(11)
            painter.setFont(font)

            text_rect = self.get_text_rect()

            painter.setPen(
                QColor(
                    255,
                    255,
                    255,
                    230
                )
            )

            document = QTextDocument()

            document.setPlainText(
                self.text
            )

            document.setDefaultFont(
                font
            )

            document.setDefaultTextOption(
                self.get_text_option()
            )

            document.setTextWidth(
                text_rect.width()
            )

            painter.save()

            painter.translate(
                text_rect.topLeft()
            )

            painter.setClipRect(
                QRectF(
                    0,
                    0,
                    text_rect.width(),
                    text_rect.height()
                )
            )

            document.drawContents(
                painter,
                QRectF(
                    0,
                    0,
                    text_rect.width(),
                    text_rect.height()
                )
            )

            painter.restore()