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


GEOMETRY_REASONS = set(
    [
        "geometry",
        "move",
        "resize",
        "position",
    ]
)

MODEL_REASONS = set(
    [
        "model",
        "hierarchy",
        "create",
        "delete",
        "load",
        "clear",
        "native_map",
        "tabs",
        "unknown",
    ]
)

STYLE_REASONS = set(
    [
        "style",
        "color",
    ]
)

TITLE_REASONS = set(
    [
        "title",
        "rename",
    ]
)

VIEW_REASONS = set(
    [
        "view",
        "viewport",
        "pan",
        "zoom",
        "focus",
    ]
)


def reason_dirties_scene_index(
    reason
):

    return (
        reason in GEOMETRY_REASONS
        or reason in MODEL_REASONS
    )


class NExEventBus(QObject):

    # Legacy signals.
    items_changed = Signal()
    item_changed = Signal(object)

    # Reason-aware signals.
    items_changed_detailed = Signal(object)
    item_changed_detailed = Signal(object, object)
    view_changed = Signal(object)

    tabs_changed = Signal()
    current_tab_changed = Signal(object)
    node_editor_closed = Signal()

    def __init__(self):

        super().__init__()

        self._items_changed_pending = False
        self._pending_reasons = set()
        self._pending_payloads = []


    def emit_items_changed(
        self,
        reason="unknown",
        payload=None
    ):

        if payload is None:

            payload = {}

        self._pending_reasons.add(
            reason
        )

        self._pending_payloads.append(
            payload
        )

        if self._items_changed_pending:
            return

        self._items_changed_pending = True

        # Slightly delay to coalesce event storms.
        QTimer.singleShot(
            50,
            self._flush_items_changed
        )


    def _flush_items_changed(self):

        self._items_changed_pending = False

        payload = {
            "reasons": list(
                self._pending_reasons
            ),
            "payloads": list(
                self._pending_payloads
            )
        }

        self._pending_reasons = set()
        self._pending_payloads = []

        self.items_changed_detailed.emit(
            payload
        )

        # Legacy compatibility.
        self.items_changed.emit()


    def emit_item_changed(
        self,
        item,
        reason="unknown",
        payload=None
    ):

        if payload is None:

            payload = {}

        detailed_payload = {
            "reason": reason,
            "payload": payload
        }

        self.item_changed_detailed.emit(
            item,
            detailed_payload
        )

        # Legacy compatibility.
        self.item_changed.emit(
            item
        )

        self.emit_items_changed(
            reason=reason,
            payload=payload
        )


    def emit_view_changed(
        self,
        reason="view",
        payload=None
    ):

        if payload is None:

            payload = {}

        detailed_payload = {
            "reason": reason,
            "payload": payload
        }

        self.view_changed.emit(
            detailed_payload
        )


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


def mark_scene_index_dirty_for_reason(
    reason
):

    if not reason_dirties_scene_index(
        reason
    ):
        return

    try:

        import NEx_SDBM.core.utilities.scene_index as scene_index

        scene_index.mark_scene_index_dirty()

    except Exception:
        pass


def emit_items_changed(
    reason="unknown",
    payload=None
):

    request_refresh(
        reason=reason,
        payload=payload
    )

    get_event_bus().emit_items_changed(
        reason=reason,
        payload=payload
    )


def emit_item_changed(
    item,
    reason="unknown",
    payload=None
):

    request_refresh(
        reason=reason,
        item=item,
        payload=payload
    )

    get_event_bus().emit_item_changed(
        item,
        reason=reason,
        payload=payload
    )


def emit_geometry_changed(
    item=None,
    payload=None
):

    if item is not None:

        emit_item_changed(
            item,
            reason="geometry",
            payload=payload
        )

    else:

        emit_items_changed(
            reason="geometry",
            payload=payload
        )


def emit_hierarchy_changed(
    payload=None
):

    emit_items_changed(
        reason="hierarchy",
        payload=payload
    )


def emit_title_changed(
    item,
    payload=None
):

    emit_item_changed(
        item,
        reason="title",
        payload=payload
    )


def emit_style_changed(
    item,
    payload=None
):

    emit_item_changed(
        item,
        reason="style",
        payload=payload
    )


def emit_view_changed(
    reason="view",
    payload=None
):

    request_refresh(
        reason=reason,
        payload=payload
    )

    get_event_bus().emit_view_changed(
        reason=reason,
        payload=payload
    )


def emit_tabs_changed():

    emit_items_changed(
        reason="tabs"
    )

    get_event_bus().tabs_changed.emit()


def emit_current_tab_changed(
    tab_info
):

    emit_items_changed(
        reason="tabs",
        payload={
            "tab_info": tab_info
        }
    )

    get_event_bus().current_tab_changed.emit(
        tab_info
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


def request_refresh(
    reason="unknown",
    item=None,
    payload=None
):

    try:

        import NEx_SDBM.core.utilities.refresh_scheduler as refresh_scheduler

        refresh_scheduler.request(
            reason=reason,
            item=item,
            payload=payload
        )

    except Exception:
        pass