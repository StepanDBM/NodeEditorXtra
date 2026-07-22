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

    def on_body_double_click(
        self,
        event
    ):

        self.start_text_edit()
    def contextMenuEvent(
        self,
        event
    ):

        event.accept()


class CommentItem(NExGraphicsItem):

    def __init__(
        self,
        title="Comment",
        text="Comment",
        width=240,
        height=120
    ):
        super().__init__(
            title=title,
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
                    self.get_text_rect().width()
                )
            )

    # -----------------------------------------------------
    # Color helpers
    # -----------------------------------------------------


    def get_text_rect(self):

        body_rect = self.get_body_rect()

        return QRectF(
            body_rect.left() + 10,
            body_rect.top() + 8,
            body_rect.width() - 20,
            body_rect.height() - 16
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

    def on_body_double_click(
        self,
        event
    ):

        self.start_text_edit()

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

        self.paint_base_panel(
            painter
        )

        if self.text_editor is None:

            font = painter.font()
            font.setPointSize(11)
            font.setBold(False)
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