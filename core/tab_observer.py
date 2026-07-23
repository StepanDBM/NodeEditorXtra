# NEx_SDBM/core/tab_observer.py

import __main__


try:
    from PySide2.QtCore import (
        QObject,
        QEvent,
        QTimer
    )

except ImportError:
    from PySide6.QtCore import (
        QObject,
        QEvent,
        QTimer
    )


import NEx_SDBM.core.node_editor as NEx
import NEx_SDBM.core.utilities.events as events


class NExTabObserver(QObject):

    def __init__(self):

        super().__init__()

        self.node_editor_widget = None
        self.search_root_widget = None
        self.tab_bar = None
        self.stack = None

        self.current_tab_key = None
        self.tab_signature = None

        self._check_pending = False

    # -----------------------------------------------------
    # Install / uninstall
    # -----------------------------------------------------

    def install(self):

        self.uninstall()

        try:

            self.node_editor_widget = (
                NEx.get_node_editor_widget()
            )

        except Exception:

            self.node_editor_widget = None

        try:

            self.search_root_widget = (
                NEx.get_search_root_widget()
            )

        except Exception:

            self.search_root_widget = None

        self.refresh_targets()

        self.capture_state()

        self.install_filters()

        self.connect_signals()

        self.schedule_check()

        print(
            "NEx | Tab observer installed."
        )

    def uninstall(self):

        self.disconnect_signals()
        self.remove_filters()

        self.node_editor_widget = None
        self.search_root_widget = None
        self.tab_bar = None
        self.stack = None

    def refresh_targets(self):

        try:

            self.tab_bar = NEx.get_tab_bar()

        except Exception:

            self.tab_bar = None

        try:

            self.stack = NEx.get_stack()

        except Exception:

            self.stack = None

    def install_filters(self):

        targets = [
            self.node_editor_widget,
            self.search_root_widget,
            self.tab_bar,
            self.stack
        ]

        for target in targets:

            if not target:
                continue

            try:

                target.installEventFilter(
                    self
                )

            except Exception:
                pass

    def remove_filters(self):

        targets = [
            self.node_editor_widget,
            self.search_root_widget,
            self.tab_bar,
            self.stack
        ]

        for target in targets:

            if not target:
                continue

            try:

                target.removeEventFilter(
                    self
                )

            except Exception:
                pass

    def connect_signals(self):

        if self.tab_bar:

            try:

                self.tab_bar.currentChanged.connect(
                    self.on_qt_current_changed
                )

            except Exception:
                pass

        if self.stack:

            try:

                self.stack.currentChanged.connect(
                    self.on_qt_current_changed
                )

            except Exception:
                pass

    def disconnect_signals(self):

        if self.tab_bar:

            try:

                self.tab_bar.currentChanged.disconnect(
                    self.on_qt_current_changed
                )

            except Exception:
                pass

        if self.stack:

            try:

                self.stack.currentChanged.disconnect(
                    self.on_qt_current_changed
                )

            except Exception:
                pass

    # -----------------------------------------------------
    # State
    # -----------------------------------------------------

    def get_current_tab_key_and_info(self):

        try:

            tab_info = NEx.get_current_tab_info()

            if not tab_info:
                return None, None

            return (
                tab_info.get(
                    "key"
                ),
                tab_info
            )

        except Exception:

            return None, None

    def get_tab_signature(self):

        try:

            tab_infos = NEx.get_tab_infos()

        except Exception:

            return None

        return tuple(
            (
                item.get(
                    "index"
                ),
                item.get(
                    "name"
                ),
                item.get(
                    "key"
                )
            )
            for item in tab_infos
        )

    def capture_state(self):

        current_key, tab_info = (
            self.get_current_tab_key_and_info()
        )

        self.current_tab_key = current_key

        self.tab_signature = self.get_tab_signature()

    # -----------------------------------------------------
    # Debounced check
    # -----------------------------------------------------

    def schedule_check(self):

        if self._check_pending:
            return

        self._check_pending = True

        QTimer.singleShot(
            50,
            self.check_tabs
        )

    def check_tabs(self):

        self._check_pending = False

        # Maya can rebuild/replace widgets, so reacquire them.
        old_tab_bar = self.tab_bar
        old_stack = self.stack

        self.refresh_targets()

        if (
            self.tab_bar is not old_tab_bar
            or self.stack is not old_stack
        ):

            self.disconnect_signals()
            self.remove_filters()

            self.install_filters()
            self.connect_signals()

        current_key, tab_info = (
            self.get_current_tab_key_and_info()
        )

        if current_key != self.current_tab_key:

            self.current_tab_key = current_key

            events.emit_current_tab_changed(
                tab_info
            )

        new_signature = self.get_tab_signature()

        if new_signature != self.tab_signature:

            self.tab_signature = new_signature

            events.emit_tabs_changed()

    # -----------------------------------------------------
    # Qt callbacks
    # -----------------------------------------------------

    def on_qt_current_changed(
        self,
        index
    ):

        self.schedule_check()

    def eventFilter(
        self,
        obj,
        event
    ):

        event_type = event.type()

        watched_events = (
            QEvent.MouseButtonRelease,
            QEvent.MouseButtonDblClick,
            QEvent.KeyRelease,
            QEvent.ChildAdded,
            QEvent.ChildRemoved,
            QEvent.LayoutRequest,
            QEvent.Show,
            QEvent.Hide,
            QEvent.Resize
        )

        if event_type in watched_events:

            self.schedule_check()

        # Important:
        # Never consume Maya events.
        return False


def install_tab_observer():

    old_observer = getattr(
        __main__,
        "NEX_TAB_OBSERVER",
        None
    )

    if old_observer:

        try:

            old_observer.uninstall()

        except Exception:
            pass

    observer = NExTabObserver()
    observer.install()

    __main__.NEX_TAB_OBSERVER = observer

    return observer