# NEx_SDBM/core/scene_view.py

import __main__

try:
    from PySide2.QtCore import (
        QObject,
        QEvent,
        Qt,
        QTimer
    )

    from PySide2.QtWidgets import (
        QGraphicsView
    )

except ImportError:
    from PySide6.QtCore import (
        QObject,
        QEvent,
        Qt,
        QTimer
    )

    from PySide6.QtWidgets import (
        QGraphicsView
    )


import NEx_SDBM.core.node_editor as NEx


# ---------------------------------------------------------
# View helpers
# ---------------------------------------------------------

def get_view_for_scene(scene=None):

    if scene is None:

        scene = NEx.get_scene()

    try:

        views = scene.views()

    except RuntimeError:
        return None

    except Exception:
        return None

    if not views:
        return None

    views = sorted(
        views,
        key=NEx._view_score,
        reverse=True
    )

    return views[0]


def center_view_on_item(item):

    if item is None:
        return False

    try:

        scene = item.scene()

    except RuntimeError:
        return False

    except Exception:
        return False

    if not scene:
        return False

    view = get_view_for_scene(
        scene
    )

    if not view:
        return False

    try:

        item_rect = item.sceneBoundingRect()

    except RuntimeError:
        return False

    except Exception:
        return False

    try:

        view.centerOn(
            item_rect.center()
        )

    except RuntimeError:
        return False

    except Exception:
        return False

    return True


def frame_view_on_item(
    item,
    padding=80
):

    if item is None:
        return False

    try:

        scene = item.scene()

    except RuntimeError:
        return False

    except Exception:
        return False

    if not scene:
        return False

    view = get_view_for_scene(
        scene
    )

    if not view:
        return False

    try:

        item_rect = item.sceneBoundingRect()

    except RuntimeError:
        return False

    except Exception:
        return False

    try:

        frame_rect = item_rect.adjusted(
            -padding,
            -padding,
            padding,
            padding
        )

        view.fitInView(
            frame_rect,
            Qt.KeepAspectRatio
        )

    except RuntimeError:
        return False

    except Exception:
        return False

    return True


# ---------------------------------------------------------
# Maya Node Editor F-key integration
# ---------------------------------------------------------

class NExNodeEditorFocusFilter(QObject):

    def __init__(self):

        super().__init__()

        self.views = []


    def get_view_from_object(
        self,
        obj
    ):

        current = obj

        while current:

            if isinstance(
                current,
                QGraphicsView
            ):

                return current

            try:

                current = current.parent()

            except RuntimeError:
                return None

            except Exception:
                return None

        return None


    def get_selected_nex_items_from_scene(
        self,
        scene
    ):

        try:

            selected = scene.selectedItems()

        except RuntimeError:
            return []

        except Exception:
            return []

        return [
            item
            for item in selected
            if NEx.is_nex_item(
                item
            )
        ]


    def eventFilter(
        self,
        obj,
        event
    ):
        if event.type() == QEvent.Destroy:
            return False
        if event.type() != QEvent.KeyPress:
            return False

        if event.key() != Qt.Key_F:
            return False

        if event.modifiers() != Qt.NoModifier:
            return False

        view = self.get_view_from_object(
            obj
        )

        if not view:
            return False

        try:

            scene = view.scene()

        except RuntimeError:
            return False

        except Exception:
            return False

        if not scene:
            return False

        selected_nex_items = (
            self.get_selected_nex_items_from_scene(
                scene
            )
        )

        if not selected_nex_items:

            # Let Maya handle normal F behavior.
            return False

        frame_view_on_item(
            selected_nex_items[0]
        )

        event.accept()

        return True


    def install_on_view(
        self,
        view
    ):

        if not view:
            return

        if view in self.views:
            return

        try:

            view.installEventFilter(
                self
            )

            viewport = view.viewport()

            if viewport:

                viewport.installEventFilter(
                    self
                )

            self.views.append(
                view
            )

            try:

                view.destroyed.connect(
                    lambda *args, view=view: self.remove_dead_view(
                        view
                    )
                )

            except Exception:
                pass

            try:

                if viewport:

                    viewport.destroyed.connect(
                        lambda *args, view=view: self.remove_dead_view(
                            view
                        )
                    )

            except Exception:
                pass

        except RuntimeError:
            pass

        except Exception:
            pass


    def remove_dead_view(
        self,
        view
    ):

        cleaned = []

        for existing_view in list(
            self.views
        ):

            if existing_view is view:
                continue

            cleaned.append(
                existing_view
            )

        self.views = cleaned

    def uninstall(self):

        for view in list(
            self.views
        ):

            try:

                view.removeEventFilter(
                    self
                )

            except Exception:
                pass

            try:

                view.viewport().removeEventFilter(
                    self
                )

            except Exception:
                pass

        self.views = []


def install_nex_focus_filter():

    old_filter = getattr(
        __main__,
        "NEX_FOCUS_FILTER",
        None
    )

    if old_filter:

        try:

            old_filter.uninstall()

        except Exception:
            pass

    focus_filter = NExNodeEditorFocusFilter()

    root = NEx.get_search_root_widget()

    try:

        views = root.findChildren(
            QGraphicsView
        )

    except RuntimeError:
        views = []

    except Exception:
        views = []

    for view in views:

        try:

            if not view.scene():
                continue

        except Exception:
            continue

        focus_filter.install_on_view(
            view
        )

    __main__.NEX_FOCUS_FILTER = focus_filter

    print(
        "NEx | Installed Node Editor focus filter on {} view(s).".format(
            len(
                focus_filter.views
            )
        )
    )

    return focus_filter