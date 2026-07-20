#backdrop_editor.py
try:
    from PySide2.QtWidgets import (
        QDialog,
        QLabel,
        QLineEdit,
        QSpinBox,
        QPushButton,
        QVBoxLayout,
        QHBoxLayout,
        QColorDialog
    )
    from PySide2.QtGui import QColor

except ImportError:

    from PySide6.QtWidgets import (
        QDialog,
        QLabel,
        QLineEdit,
        QSpinBox,
        QPushButton,
        QVBoxLayout,
        QHBoxLayout,
        QColorDialog
    )
    from PySide6.QtGui import QColor


class BackdropEditor(QDialog):

    def __init__(
        self,
        backdrop,
        parent=None
    ):
        super().__init__(parent)

        self.backdrop = backdrop

        self.setWindowTitle(
            "Backdrop Settings"
        )

        self.setMinimumWidth(300)
        self.color = QColor(
            backdrop.background_color
        )
        
        self.create_ui()

    def update_color_preview(self):

        self.color_preview.setStyleSheet(
            f"""
            background-color:
            {self.color.name()};
            border: 1px solid #222;
            """
        )

    def pick_color(self):

        color = QColorDialog.getColor(
            self.color,
            self,
            "Backdrop Color"
        )

        if not color.isValid():
            return

        self.color = color

        self.update_color_preview()
    
    def apply(self):

        self.backdrop.prepareGeometryChange()

        self.backdrop.title = (self.name_le.text().strip())
        self.backdrop.width = (self.width_sb.value())
        self.backdrop.height = (self.height_sb.value())
        self.backdrop.roundness = (self.roundness_sb.value())
        self.backdrop.background_color = QColor(self.color)
        self.backdrop.header_color = (self.color.darker(160))
        self.backdrop.update()

        self.close()

    def create_ui(self):

        layout = QVBoxLayout()

        # ---------------------
        # Name
        # ---------------------

        layout.addWidget(QLabel("Name"))

        self.name_le = QLineEdit()
        self.name_le.setText(self.backdrop.title)

        layout.addWidget(self.name_le)

        # ---------------------
        # Width
        # ---------------------

        layout.addWidget(QLabel("Width"))
        self.width_sb = QSpinBox()
        self.width_sb.setRange(50, 5000)

        self.width_sb.setValue(int(self.backdrop.width))

        layout.addWidget(self.width_sb)

        # ---------------------
        # Height
        # ---------------------

        layout.addWidget(
            QLabel("Height")
        )

        self.height_sb = QSpinBox()
        self.height_sb.setRange(50, 5000)
        self.height_sb.setValue(int(self.backdrop.height))

        layout.addWidget(self.height_sb)
        layout.addWidget(QLabel("Roundness"))
        self.roundness_sb = QSpinBox()

        self.roundness_sb.setRange(0, 50)

        self.roundness_sb.setValue(int(self.backdrop.roundness))

        layout.addWidget(self.roundness_sb)


        layout.addWidget(QLabel("Color"))
        self.color_preview = QLabel()

        self.color_preview.setFixedHeight(24)

        layout.addWidget(self.color_preview)

        self.pick_color_btn = QPushButton("Pick Color")
        self.pick_color_btn.clicked.connect(self.pick_color)

        self.update_color_preview()

        layout.addWidget(self.pick_color_btn)
        # ---------------------
        # Buttons
        # ---------------------

        button_layout = QHBoxLayout()

        apply_btn = QPushButton("Apply")
        cancel_btn = QPushButton("Cancel")

        button_layout.addWidget(apply_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)
        apply_btn.clicked.connect(self.apply)

        cancel_btn.clicked.connect(self.close)