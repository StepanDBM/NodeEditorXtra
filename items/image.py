# NEx_SDBM/items/image.py

import os

try:
    from PySide2.QtGui import (
        QColor,
        QPainter,
        QPixmap
    )

    from PySide2.QtCore import (
        QRectF,
        Qt
    )

except ImportError:
    from PySide6.QtGui import (
        QColor,
        QPainter,
        QPixmap
    )

    from PySide6.QtCore import (
        QRectF,
        Qt
    )


from NEx_SDBM.items.nex_item import (
    NExGraphicsItem
)


class ImageItem(NExGraphicsItem):

    def __init__(
        self,
        title="Image",
        image_path="",
        width=320,
        height=220
    ):
        super().__init__(
            title=title,
            width=width,
            height=height
        )

        self.nex_item_type = "image"
        self.nex_parentable = True
        self.nex_container = False

        self.image_path = image_path
        self.pixmap = QPixmap()

        self.roundness = 8

        self.background_color = QColor(
            35,
            35,
            35,
            220
        )

        self.header_color = QColor(
            25,
            25,
            25,
            235
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

        self.load_pixmap()

    # -----------------------------------------------------
    # Image
    # -----------------------------------------------------

    def load_pixmap(self):

        self.pixmap = QPixmap()

        if not self.image_path:
            return

        if not os.path.exists(
            self.image_path
        ):
            return

        self.pixmap.load(
            self.image_path
        )

    def set_image_path(
        self,
        image_path
    ):

        self.image_path = image_path
        self.load_pixmap()
        self.update()

    def get_image_rect(self):

        body_rect = self.get_body_rect()

        return QRectF(
            body_rect.left() + 8,
            body_rect.top() + 8,
            body_rect.width() - 16,
            body_rect.height() - 16
        )

    # -----------------------------------------------------
    # Mouse events
    # -----------------------------------------------------

    def on_body_double_click(
        self,
        event
    ):

        self.pick_image_file()

    def pick_image_file(self):

        try:
            from maya import cmds

            result = cmds.fileDialog2(
                fileMode=1,
                caption="Choose Image",
                fileFilter=(
                    "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp)"
                )
            )

            if not result:
                return

            self.set_image_path(
                result[0]
            )

        except Exception as error:

            print(
                "NEx | Could not pick image:",
                error
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

        replace_action = menu.addAction(
            "Replace Image"
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

        if result == replace_action:

            self.pick_image_file()

        elif result == color_action:

            self.pick_color()

        elif result == delete_action:

            self.delete_self()

    # -----------------------------------------------------
    # Paint
    # -----------------------------------------------------

    def paint_missing_image(
        self,
        painter,
        image_rect
    ):

        painter.setPen(
            QColor(
                255,
                255,
                255,
                150
            )
        )

        painter.drawText(
            image_rect,
            Qt.AlignCenter,
            "Missing Image"
        )

    def paint_image(
        self,
        painter
    ):

        image_rect = self.get_image_rect()

        if self.pixmap.isNull():

            self.paint_missing_image(
                painter,
                image_rect
            )

            return

        target_width = max(
            1,
            int(
                image_rect.width()
            )
        )

        target_height = max(
            1,
            int(
                image_rect.height()
            )
        )

        scaled_pixmap = self.pixmap.scaled(
            target_width,
            target_height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        draw_x = (
            image_rect.left()
            + (
                image_rect.width()
                - scaled_pixmap.width()
            )
            * 0.5
        )

        draw_y = (
            image_rect.top()
            + (
                image_rect.height()
                - scaled_pixmap.height()
            )
            * 0.5
        )

        painter.drawPixmap(
            int(
                draw_x
            ),
            int(
                draw_y
            ),
            scaled_pixmap
        )

    def paint(
        self,
        painter,
        option,
        widget
    ):

        self.paint_base_panel(
            painter
        )

        painter.save()

        painter.setClipRect(
            self.get_body_rect()
        )

        self.paint_image(
            painter
        )

        painter.restore()