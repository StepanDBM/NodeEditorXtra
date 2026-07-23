# NEx_SDBM/launcher.py

import __main__

from NEx_SDBM.ui.main_window import (
    NExMainWindow,
    maya_main_window
)


def show():
    import NEx_SDBM.core.utilities.events as events
    import NEx_SDBM.core.scene_view as scene_view
    import NEx_SDBM.core.tab_observer as tab_observer

    try:
        __main__.NEX_WINDOW.close()
        __main__.NEX_WINDOW.deleteLater()

    except Exception:
        pass

    try:
        events.reset_event_bus()
    except Exception as error:
        print(
            "NEx | Could not reset event bus:",
            error
        )

    __main__.NEX_WINDOW = NExMainWindow(parent=maya_main_window())

    __main__.NEX_WINDOW.show()
    __main__.NEX_WINDOW.raise_()
    __main__.NEX_WINDOW.activateWindow()
    __main__.NEX_WINDOW.raise_()


    try:
        scene_view.install_nex_focus_filter()
    except Exception as error:
        print(
            "NEx | Could not install focus filter:",
            error
        )
    try:
        tab_observer.install_tab_observer()
    except Exception as error:
        print(
            "NEx | Could not install tab observer:",
            error
        )
    return __main__.NEX_WINDOW