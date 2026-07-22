# NEx_SDBM/launcher.py

import __main__

from NEx_SDBM.ui.main_window import (
    NExMainWindow,
    maya_main_window
)


def show():

    try:

        __main__.NEX_WINDOW.close()
        __main__.NEX_WINDOW.deleteLater()

    except Exception:
        pass

    __main__.NEX_WINDOW = NExMainWindow(
        parent=maya_main_window()
    )

    __main__.NEX_WINDOW.show()
    __main__.NEX_WINDOW.raise_()
    __main__.NEX_WINDOW.activateWindow()
    __main__.NEX_WINDOW.raise_()


    try:

    import NEx_SDBM.core.scene_view as scene_view
    scene_view.install_nex_focus_filter()

    except Exception as error:

        print(
            "NEx | Could not install focus filter:",
            error
        )

    return __main__.NEX_WINDOW