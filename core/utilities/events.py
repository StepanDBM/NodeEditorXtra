# NEx_SDBM/core/events.py

import __main__

try:
    from PySide2.QtCore import (
        QObject,
        Signal,
        QTimer
    )

except ImportError:
    from PySide6.QtCore import (
        QObject,
        Signal,
        QTimer
    )


class NExEventBus(QObject):

    tabs_changed = Signal()
    current_tab_changed = Signal(object)
    items_changed = Signal()
    item_changed = Signal(object)

    node_editor_closed = Signal()

    def __init__(self):

        super().__init__()

        self._items_changed_pending = False

    def emit_items_changed(self):

        if self._items_changed_pending:
            return

        self._items_changed_pending = True

        QTimer.singleShot(
            0,
            self._flush_items_changed
        )

    def _flush_items_changed(self):

        self._items_changed_pending = False

        self.items_changed.emit()

    def emit_item_changed(
        self,
        item
    ):

        self.item_changed.emit(
            item
        )

        self.emit_items_changed()

def emit_tabs_changed():

    get_event_bus().tabs_changed.emit()


def emit_current_tab_changed(
    tab_info
):

    get_event_bus().current_tab_changed.emit(
        tab_info
    )

    emit_items_changed()

def get_event_bus():

    bus = getattr(
        __main__,
        "NEX_EVENT_BUS",
        None
    )

    if bus is None:

        bus = NExEventBus()

        __main__.NEX_EVENT_BUS = bus

    return bus


def emit_items_changed():

    try:

        import NEx_SDBM.core.utilities.scene_index as scene_index

        scene_index.mark_scene_index_dirty()

    except Exception:
        pass

    get_event_bus().emit_items_changed()


def emit_item_changed(
    item
):

    try:

        import NEx_SDBM.core.utilities.scene_index as scene_index

        scene_index.mark_scene_index_dirty()

    except Exception:
        pass

    get_event_bus().emit_item_changed(
        item
    )

def emit_node_editor_closed():

    get_event_bus().node_editor_closed.emit()

def reset_event_bus():

    old_bus = getattr(
        __main__,
        "NEX_EVENT_BUS",
        None
    )

    if old_bus is not None:

        try:

            old_bus.deleteLater()

        except Exception:
            pass

    __main__.NEX_EVENT_BUS = NExEventBus()

    return __main__.NEX_EVENT_BUS