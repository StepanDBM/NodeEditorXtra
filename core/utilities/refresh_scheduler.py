# NEx_SDBM/core/utilities/refresh_scheduler.py

import __main__
import weakref


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
        "unknown"
    ]
)


GEOMETRY_REASONS = set(
    [
        "geometry",
        "move",
        "resize",
        "position",
        "geometry_commit"
    ]
)


LIVE_GEOMETRY_REASONS = set(
    [
        "geometry_live",
        "drag",
        "drag_live"
    ]
)


VIEW_REASONS = set(
    [
        "view",
        "viewport",
        "pan",
        "zoom",
        "focus"
    ]
)


STYLE_REASONS = set(
    [
        "style",
        "color"
    ]
)


TITLE_REASONS = set(
    [
        "title",
        "rename"
    ]
)


SELECTION_REASONS = set(
    [
        "selection"
    ]
)


def item_is_live(
    item
):

    try:

        return (
            item is not None
            and item.scene() is not None
        )

    except RuntimeError:
        return False

    except Exception:
        return False


class NExRefreshScheduler(QObject):

    def __init__(self):

        super().__init__()

        self._flush_pending = False
        self._pending_reasons = set()
        self._pending_items = set()
        self._pending_payloads = []

        self._minimap_refs = []
        self._outliner_refs = []

        self.flush_delay_ms = 50


    # -----------------------------------------------------
    # Registration
    # -----------------------------------------------------

    def register_minimap(
        self,
        minimap
    ):

        self._register_ref(
            self._minimap_refs,
            minimap
        )


    def unregister_minimap(
        self,
        minimap
    ):

        self._unregister_ref(
            self._minimap_refs,
            minimap
        )


    def register_outliner(
        self,
        outliner
    ):

        self._register_ref(
            self._outliner_refs,
            outliner
        )


    def unregister_outliner(
        self,
        outliner
    ):

        self._unregister_ref(
            self._outliner_refs,
            outliner
        )


    def _register_ref(
        self,
        ref_list,
        obj
    ):

        if obj is None:
            return

        for existing_ref in list(
            ref_list
        ):

            existing_obj = existing_ref()

            if existing_obj is obj:
                return

        ref_list.append(
            weakref.ref(
                obj
            )
        )


    def _unregister_ref(
        self,
        ref_list,
        obj
    ):

        clean = []

        for existing_ref in list(
            ref_list
        ):

            existing_obj = existing_ref()

            if existing_obj is None:
                continue

            if existing_obj is obj:
                continue

            clean.append(
                existing_ref
            )

        ref_list[:] = clean


    def _iter_live_refs(
        self,
        ref_list
    ):

        clean = []

        for existing_ref in list(
            ref_list
        ):

            obj = existing_ref()

            if obj is None:
                continue

            try:

                obj.objectName()

            except RuntimeError:
                continue

            except Exception:
                pass

            clean.append(
                existing_ref
            )

            yield obj

        ref_list[:] = clean

    # -----------------------------------------------------
    # Request / flush
    # -----------------------------------------------------

    def request(
        self,
        reason="unknown",
        item=None,
        payload=None
    ):

        if payload is None:

            payload = {}

        self._pending_reasons.add(
            reason
        )

        if item is not None:

            self._pending_items.add(
                item
            )

        self._pending_payloads.append(
            payload
        )

        if self._flush_pending:
            return

        self._flush_pending = True

        QTimer.singleShot(
            self.flush_delay_ms,
            self.flush
        )


    def request_immediate(
        self,
        reason="unknown",
        item=None,
        payload=None
    ):

        if payload is None:

            payload = {}

        self._pending_reasons.add(
            reason
        )

        if item is not None:

            self._pending_items.add(
                item
            )

        self._pending_payloads.append(
            payload
        )

        if self._flush_pending:
            return

        self._flush_pending = True

        QTimer.singleShot(
            0,
            self.flush
        )


    def flush(self):

        self._flush_pending = False

        reasons = set(
            self._pending_reasons
        )

        items = [
            item
            for item in self._pending_items
            if item_is_live(
                item
            )
        ]

        payloads = list(
            self._pending_payloads
        )

        self._pending_reasons = set()
        self._pending_items = set()
        self._pending_payloads = []

        if not reasons:

            return

        self.process(
            reasons,
            items,
            payloads
        )


    # -----------------------------------------------------
    # Processing
    # -----------------------------------------------------

    def process(
        self,
        reasons,
        items,
        payloads
    ):

        self.process_scene_index(
            reasons
        )

        self.process_minimaps(
            reasons
        )

        self.process_outliners(
            reasons,
            items
        )


    def process_scene_index(
        self,
        reasons
    ):

        needs_dirty = bool(
            reasons.intersection(
                MODEL_REASONS
            )
            or reasons.intersection(
                GEOMETRY_REASONS
            )
        )

        if not needs_dirty:
            return

        try:

            import NEx_SDBM.core.utilities.scene_index as scene_index

            scene_index.mark_scene_index_dirty()

        except Exception:
            pass


    def process_minimaps(
        self,
        reasons
    ):

        for minimap in self._iter_live_refs(
            self._minimap_refs
        ):

            try:

                if reasons.intersection(
                    MODEL_REASONS
                ):

                    minimap.schedule_model_refresh()
                    continue

                if reasons.intersection(
                    GEOMETRY_REASONS
                ):

                    minimap.schedule_geometry_refresh()
                    continue

                if reasons.intersection(
                    LIVE_GEOMETRY_REASONS
                ):

                    minimap.schedule_geometry_refresh()
                    continue

                if reasons.intersection(
                    VIEW_REASONS
                ):

                    minimap.schedule_viewport_refresh()
                    continue

                if reasons.intersection(
                    STYLE_REASONS
                    | TITLE_REASONS
                ):

                    minimap.update()
                    continue

            except RuntimeError:
                pass

            except Exception:
                pass


    def process_outliners(
        self,
        reasons,
        items
    ):

        for outliner in self._iter_live_refs(
            self._outliner_refs
        ):

            try:

                if reasons.intersection(
                    MODEL_REASONS
                ):

                    outliner.schedule_tree_refresh()
                    continue

                if reasons.intersection(
                    GEOMETRY_REASONS
                ):

                    outliner.schedule_tree_refresh()
                    continue

                if reasons.intersection(
                    LIVE_GEOMETRY_REASONS
                ):

                    # Live dragging should not rebuild the outliner.
                    continue

                if reasons.intersection(
                    TITLE_REASONS
                    | STYLE_REASONS
                ):

                    for item in items:

                        outliner.update_tree_item_for_scene_item(
                            item
                        )

                    outliner.schedule_filter_refresh()
                    continue

                if reasons.intersection(
                    SELECTION_REASONS
                ):

                    # Placeholder for future selection highlighting.
                    continue

                if reasons.intersection(
                    VIEW_REASONS
                ):

                    # View changes should never affect Outliner.
                    continue

            except RuntimeError:
                pass

            except Exception:
                pass


# ---------------------------------------------------------
# Global access
# ---------------------------------------------------------

def get_scheduler():

    scheduler = getattr(
        __main__,
        "NEX_REFRESH_SCHEDULER",
        None
    )

    if scheduler is None:

        scheduler = NExRefreshScheduler()

        __main__.NEX_REFRESH_SCHEDULER = scheduler

    return scheduler


def request(
    reason="unknown",
    item=None,
    payload=None
):

    get_scheduler().request(
        reason=reason,
        item=item,
        payload=payload
    )


def request_immediate(
    reason="unknown",
    item=None,
    payload=None
):

    get_scheduler().request_immediate(
        reason=reason,
        item=item,
        payload=payload
    )


def register_minimap(
    minimap
):

    get_scheduler().register_minimap(
        minimap
    )


def unregister_minimap(
    minimap
):

    get_scheduler().unregister_minimap(
        minimap
    )


def register_outliner(
    outliner
):

    get_scheduler().register_outliner(
        outliner
    )


def unregister_outliner(
    outliner
):

    get_scheduler().unregister_outliner(
        outliner
    )


def reset_scheduler():

    old_scheduler = getattr(
        __main__,
        "NEX_REFRESH_SCHEDULER",
        None
    )

    if old_scheduler is not None:

        try:

            old_scheduler.deleteLater()

        except Exception:
            pass

    __main__.NEX_REFRESH_SCHEDULER = NExRefreshScheduler()

    return __main__.NEX_REFRESH_SCHEDULER