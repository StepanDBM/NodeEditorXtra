# NEx_SDBM/core/tab_watcher.py

import __main__

try:
    from PySide2.QtCore import (
        QObject,
        QTimer
    )

except ImportError:
    from PySide6.QtCore import (
        QObject,
        QTimer
    )


import NEx_SDBM.core.node_editor as NEx
import NEx_SDBM.core.utilities.events as events


class NExTabWatcher(QObject):

    def __init__(
        self,
        interval=1500
    ):

        super().__init__()

        self.current_tab_key = None
        self.tab_signature = None
        self._checking = False

        self.timer = QTimer(
            self
        )

        self.timer.setInterval(
            interval
        )

        self.timer.timeout.connect(
            self.check_tabs
        )

    def start(self):

        self.capture_state()

        self.timer.start()

    def stop(self):

        self.timer.stop()

    def get_tab_signature(self):

        try:

            tab_infos = NEx.get_tab_infos()

        except Exception:

            return None

        return tuple(
            (
                tab.get(
                    "index"
                ),
                tab.get(
                    "name"
                ),
                tab.get(
                    "key"
                )
            )
            for tab in tab_infos
        )

    def get_current_key_and_info(self):

        try:

            current_tab = NEx.get_current_tab_info()

            if not current_tab:
                return None, None

            return (
                current_tab.get(
                    "key"
                ),
                current_tab
            )

        except Exception:

            return None, None

    def capture_state(self):

        current_key, current_tab = (
            self.get_current_key_and_info()
        )

        self.current_tab_key = current_key

        self.tab_signature = (
            self.get_tab_signature()
        )

    def check_tabs(self):

        if self._checking:
            return

        self._checking = True

        try:

            current_key, current_tab = (
                self.get_current_key_and_info()
            )

            if current_key != self.current_tab_key:

                self.current_tab_key = current_key

                events.emit_current_tab_changed(
                    current_tab
                )

            new_signature = (
                self.get_tab_signature()
            )

            if new_signature != self.tab_signature:

                self.tab_signature = new_signature

                events.emit_tabs_changed()

        finally:

            self._checking = False


def install_tab_watcher():

    old_watcher = getattr(
        __main__,
        "NEX_TAB_WATCHER",
        None
    )

    if old_watcher:

        try:

            old_watcher.stop()

        except Exception:
            pass

    watcher = NExTabWatcher()
    watcher.start()

    __main__.NEX_TAB_WATCHER = watcher

    print(
        "NEx | Tab watcher installed."
    )

    return watcher