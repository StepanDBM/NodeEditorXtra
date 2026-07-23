# NEx_SDBM/ui/main_window.py

from maya import OpenMayaUI
from maya import cmds

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
        QLabel,
        QFrame,
        QSplitter
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
        QLabel,
        QFrame,
        QSplitter
    )


import NEx_SDBM.api as api
import NEx_SDBM.NEx_bootstrap as bootstrap
from NEx_SDBM.ui.focus_list import FocusListWidget
from NEx_SDBM.ui.minimap import MiniMapWidget

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
            "NEx - Node Editor Extras"
        )

        self.setMinimumWidth(
            280
        )
        
        self.setWindowFlags(
            Qt.Tool
            | Qt.Window
            | Qt.WindowTitleHint
            | Qt.WindowCloseButtonHint
        )

        self.build_ui()
        self.create_connections()

    def build_ui(self):

        main_layout = QVBoxLayout(
            self
        )


        # -------------------------------------------------
        # Main actions
        # -------------------------------------------------
        
        ActionsTitle = QLabel(
            "NEx - Actions"
        )

        main_layout.addWidget(
            ActionsTitle
        )
        actions_layout = QHBoxLayout()

        self.create_backdrop_btn = QPushButton("Create")
        self.create_comment_btn = QPushButton("Comment")
        self.create_image_btn = QPushButton("Image")
        self.clear_all_btn = QPushButton("Clear All")

        actions_layout.addWidget(self.create_backdrop_btn)
        actions_layout.addWidget(self.create_comment_btn)
        actions_layout.addWidget(self.create_image_btn)
        actions_layout.addWidget(self.clear_all_btn)

        main_layout.addLayout(actions_layout)

        # -------------------------------------------------
        # Scene MiniMap
        # -------------------------------------------------
        content_splitter = QSplitter(
            Qt.Vertical
        )

        mini_container = QWidget()
        mini_layout = QVBoxLayout(
            mini_container
        )

        mini_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        mini_layout.setSpacing(
            4
        )

        mini_header_layout = QHBoxLayout()

        mini_label = QLabel(
            "NEx - Mini Map"
        )

        self.minimap_zoom_out_btn = QPushButton(
            "-"
        )

        self.minimap_zoom_reset_btn = QPushButton(
            "1:1"
        )

        self.minimap_zoom_in_btn = QPushButton(
            "+"
        )

        mini_header_layout.addWidget(
            mini_label
        )

        mini_header_layout.addStretch()

        mini_header_layout.addWidget(
            self.minimap_zoom_out_btn
        )

        mini_header_layout.addWidget(
            self.minimap_zoom_reset_btn
        )

        mini_header_layout.addWidget(
            self.minimap_zoom_in_btn
        )

        mini_layout.addLayout(
            mini_header_layout
        )

        self.minimap = MiniMapWidget()

        mini_layout.addWidget(
            self.minimap
        )

        focus_container = QWidget()
        focus_layout = QVBoxLayout(
            focus_container
        )

        focus_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        focus_layout.setSpacing(
            4
        )

        # -------------------------------------------------
        # Scene FocusOnList
        # -------------------------------------------------
        focus_label = QLabel(
            "NEx - Outliner"
        )

        focus_layout.addWidget(
            focus_label
        )

        self.focus_list = FocusListWidget()

        focus_layout.addWidget(
            self.focus_list
        )

        content_splitter.addWidget(
            mini_container
        )

        content_splitter.addWidget(
            focus_container
        )

        content_splitter.setStretchFactor(
            0,
            1
        )

        content_splitter.setStretchFactor(
            1,
            2
        )

        content_splitter.setSizes(
            [
                180,
                320
            ]
        )

        main_layout.addWidget(
            content_splitter
        )
        # -------------------------------------------------
        # Scene persistence
        # -------------------------------------------------

        scene_layout = QHBoxLayout()

        self.save_scene_btn = QPushButton(
            "Save"
        )

        self.load_scene_btn = QPushButton(
            "Load"
        )

        scene_layout.addWidget(
            self.save_scene_btn
        )

        scene_layout.addWidget(
            self.load_scene_btn
        )

        main_layout.addLayout(
            scene_layout
        )

        # -------------------------------------------------
        # External .nex import/export
        # -------------------------------------------------

        file_layout = QHBoxLayout()

        self.save_btn = QPushButton(
            "Export"
        )

        self.load_btn = QPushButton(
            "Import"
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

        # -------------------------------------------------
        # Dev separator
        # -------------------------------------------------

        separator = QFrame()

        separator.setFrameShape(
            QFrame.HLine
        )

        separator.setFrameShadow(
            QFrame.Sunken
        )

        main_layout.addWidget(
            separator
        )

        dev_label = QLabel(
            "Development"
        )

        main_layout.addWidget(
            dev_label
        )

        self.reload_btn = QPushButton(
            "DevReloadModules"
        )

        main_layout.addWidget(
            self.reload_btn
        )

    def create_connections(self):
        self.minimap_zoom_out_btn.clicked.connect(
            self.minimap.zoom_out
        )

        self.minimap_zoom_reset_btn.clicked.connect(
            self.minimap.reset_zoom
        )

        self.minimap_zoom_in_btn.clicked.connect(
            self.minimap.zoom_in
        )

        
        self.create_backdrop_btn.clicked.connect(
            self._create_backdrop_from_selection_deferred
        )
        self.create_comment_btn.clicked.connect(
            self.create_comment
        )
        self.create_image_btn.clicked.connect(
            self.create_image
        )
        self.clear_all_btn.clicked.connect(
            self.clear_all_backdrops
        )

        self.save_scene_btn.clicked.connect(
            self.save_to_scene
        )

        self.load_scene_btn.clicked.connect(
            self.load_from_scene
        )

        self.save_btn.clicked.connect(
            self.save_all
        )

        self.load_btn.clicked.connect(
            self.load_all
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

    def create_comment(self):

        try:

            api.create_comment("Comment", "comment")

        except Exception as error:

            print(
                "NEx | Could not create comment:",
                error
            )
    def create_image(self):

        try:

            api.create_image()

        except Exception as error:

            print(
                "NEx | Could not create image:",
                error
            )

    def clear_all_backdrops(self):

        try:

            api.clear_all_NExItems()

        except Exception as error:

            print(
                "NEx | Could not clear:",
                error
            )

    def save_to_scene(self):

        try:

            api.save_to_scene()

        except Exception as error:

            print(
                "NEx | Could not save to scene:",
                error
            )

    def load_from_scene(self):

        try:

            api.load_from_scene(
                clear_existing=True
            )

        except Exception as error:

            print(
                "NEx | Could not load from scene:",
                error
            )

    def save_all(self):

        try:

            api.save_all_dialog()

        except Exception as error:

            print(
                "NEx | Could not export:",
                error
            )

    def load_all(self):

        try:

            api.load_all_dialog()

        except Exception as error:

            print(
                "NEx | Could not load .nex:",
                error
            )

    def reload_modules(self):

        bootstrap.run()

        print(
            "NEx | Dev reload complete."
        )

    def clear_nex_selection(self):

        api.clear_nex_selection()

    def closeEvent(
        self,
        event
    ):

        try:

            import __main__

            if getattr(
                __main__,
                "NEX_WINDOW",
                None
            ) is self:

                __main__.NEX_WINDOW = None

        except Exception:
            pass
        try:

            import __main__

            focus_filter = getattr(
                __main__,
                "NEX_FOCUS_FILTER",
                None
            )

            if focus_filter:

                focus_filter.uninstall()

                __main__.NEX_FOCUS_FILTER = None

        except Exception:
            pass


        try:

            import __main__

            tab_observer = getattr(
                __main__,
                "NEX_TAB_OBSERVER",
                None
            )

            if tab_observer:

                tab_observer.uninstall()

                __main__.NEX_TAB_OBSERVER = None

        except Exception:
            pass


        try:

            if hasattr(
                self,
                "minimap"
            ):

                self.minimap.uninstall_view_filter()

        except Exception:
            pass
        super().closeEvent(
            event
        )