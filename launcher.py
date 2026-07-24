# NEx_SDBM/launcher.py
"""
NEW updates:
Updating the system now will take some time, but will ake it usable. At this point this shit is stable and cool, but is NOT
usable, it's SO slow it almost makes me want to switch to C for this project alone.
I will be doing, in the future:
 - Build a central SceneIndex cache so every system stops rescanning Maya’s Node Editor scene independently.
 - Cache hierarchy ownership ONCE (not per draw in movement and mouse release) per dirty geometry pass instead of recomputing parent/child containment everywhere.
 - Split minimap refresh into model refresh and cheap viewport-only refresh.
 - Stop rebuilding the full Outliner tree unless hierarchy structure actually changed.
 - Make drag operations fully cache-based so mouse-move never scans the scene.
 - Replace recursive update_z_hierarchy() parent checks with cached depth and z values.
 - Cache native Maya node maps conservatively instead of rebuilding node-name-to-graphics-item maps repeatedly.
 - Add dirty flags for geometry, style, title, selection, view, and tabs instead of broad items_changed.
 - Add a refresh scheduler that coalesces event storms into one controlled rebuild.
 - Make minimap painting dumb by drawing precomputed cached draw data only (mainly from SceneIndex).
 - Later, make the Outliner incremental instead of clearing and recreating every row.
 - Add per-tab lazy indexing so inactive Node Editor tabs do not pay active-tab refresh costs (althoguh not sure if that really makes any diference, still have to check the ).
"""
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