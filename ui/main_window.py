# NEx_SDBM/ui/main_window.py

from maya import OpenMayaUI
from maya import cmds
import NEx_SDBM.api as api

try:
    from shiboken2 import wrapInstance

    from PySide2.QtCore import (
        Qt,
        QTimer
    )

    from PySide2.QtWidgets import (
        QWidget,
        QPushButton,
        QVBoxLayout,
        QHBoxLayout,
        QLabel
    )

except ImportError:
    from shiboken6 import wrapInstance

    from PySide6.QtCore import (
        Qt,
        QTimer
    )

    from PySide6.QtWidgets import (
        QWidget,
        QPushButton,
        QVBoxLayout,
        QHBoxLayout,
        QLabel
    )


def maya_main_window():

    ptr = OpenMayaUI.MQtUtil.mainWindow()

    if not ptr:
        return None

    return wrapInstance(
        int(ptr),
        QWidget
    )


class NExMainWindow(QWidget):

    def __init__(
        self,
        parent=None
    ):

        if parent is None:
            parent = maya_main_window()

        super().__init__(
            parent
        )

        self.setWindowTitle(
            "NEx"
        )

        self.setMinimumWidth(
            280
        )

        self.setWindowFlags(
            Qt.Tool
        )

        self.build_ui()
        self.create_connections()

    def build_ui(self):

        main_layout = QVBoxLayout(
            self
        )

        title = QLabel(
            "NEx - Node Editor Extras"
        )

        main_layout.addWidget(
            title
        )

        self.create_backdrop_btn = QPushButton(
            "Create Backdrop From Selection"
        )

        self.delete_selected_btn = QPushButton(
            "Delete Selected Backdrops"
        )

        main_layout.addWidget(
            self.create_backdrop_btn
        )

        main_layout.addWidget(
            self.delete_selected_btn
        )

        file_layout = QHBoxLayout()

        self.save_btn = QPushButton(
            "Save .nex"
        )

        self.load_btn = QPushButton(
            "Load .nex"
        )

        file_layout.addWidget(
            self.save_btn
        )

        file_layout.addWidget(
            self.load_btn
        )

        main_layout.addLayout(
            file_layout
        )

        self.clear_all_btn = QPushButton(
            "Clear All Backdrops"
        )

        main_layout.addWidget(
            self.clear_all_btn
        )

        self.reload_btn = QPushButton(
            "Dev Reload Modules"
        )

        main_layout.addWidget(
            self.reload_btn
        )

    def create_connections(self):

        self.create_backdrop_btn.clicked.connect(
            self.create_backdrop_from_selection
        )

        self.delete_selected_btn.clicked.connect(
            self.delete_selected_backdrops
        )

        self.save_btn.clicked.connect(
            self.save_all
        )

        self.load_btn.clicked.connect(
            self.load_all
        )

        self.clear_all_btn.clicked.connect(
            self.clear_all_backdrops
        )

        self.reload_btn.clicked.connect(
            self.reload_modules
        )

    def ensure_node_editor_open(self):

        try:
            cmds.NodeEditorWindow()

        except Exception:
            pass

        try:
            cmds.refresh(
                force=True
            )

        except Exception:
            pass

    def create_backdrop_from_selection(self):

        self.ensure_node_editor_open()

        QTimer.singleShot(
            150,
            self._create_backdrop_from_selection_deferred
        )

    def _create_backdrop_from_selection_deferred(self):


        try:

            api.create_backdrop_from_selection(
                "Backdrop"
            )

        except Exception as error:

            print(
                "NEx | Could not create backdrop:",
                error
            )

    def delete_selected_backdrops(self):

        try:

            api.delete_selected_backdrops()

        except Exception as error:

            print(
                "NEx | Could not delete backdrop:",
                error
            )

    def save_all(self):
        try:

            api.save_all_dialog()

        except Exception as error:

            print(
                "NEx | Could not save:",
                error
            )

    def load_all(self):
        try:

            api.load_all_dialog()

        except Exception as error:

            print(
                "NEx | Could not load:",
                error
            )

    def clear_all_backdrops(self):
        try:

            api.clear_all_backdrops()

        except Exception as error:

            print(
                "NEx | Could not clear:",
                error
            )

    def reload_modules(self):

        import NEx_SDBM.NEx_bootstrap as bootstrap

        bootstrap.reload_all()

        print(
            "NEx | Dev reload complete."
        )

    def clear_nex_selection(self):

        api.clear_nex_selection()