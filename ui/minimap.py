# NEx_SDBM/ui/minimap.py

try:
    from PySide2.QtCore import (
        QObject,
        QPointF,
        QRectF,
        Qt,
        QEvent,
        QTimer
    )

    from PySide2.QtGui import (
        QColor,
        QBrush,
        QPen,
        QPainter
    )

    from PySide2.QtWidgets import (
        QWidget,
        QSizePolicy
    )

except ImportError:
    from PySide6.QtCore import (
        QObject,
        QPointF,
        QRectF,
        Qt,
        QEvent,
        QTimer
    )

    from PySide6.QtGui import (
        QColor,
        QBrush,
        QPen,
        QPainter
    )

    from PySide6.QtWidgets import (
        QWidget,
        QSizePolicy
    )


import NEx_SDBM.core.node_editor as NEx
import NEx_SDBM.core.scene_view as scene_view
import NEx_SDBM.core.utilities.events as events


class MiniMapViewFilter(QObject):

    def __init__(
        self,
        minimap
    ):

        super().__init__(
            minimap
        )

        self.minimap = minimap

    def eventFilter(
        self,
        obj,
        event
    ):

        event_type = event.type()

        if event_type == QEvent.Destroy:

            try:

                self.minimap.on_node_editor_view_destroyed()

            except Exception:
                pass

            return False

        watched_events = (
            QEvent.MouseButtonPress,
            QEvent.MouseButtonRelease,
            QEvent.MouseMove,
            QEvent.Wheel,
            QEvent.Resize,
            QEvent.Show,
            QEvent.Hide
        )

        if event_type in watched_events:

            try:

                self.minimap.schedule_refresh()

            except Exception:
                pass

        return False


class MiniMapWidget(QWidget):

    def __init__(
        self,
        parent=None
    ):

        super().__init__(
            parent
        )

        self.scene = None
        self.view = None
        self.scene_bounds = None

        self.view_filter = MiniMapViewFilter(
            self
        )

        self._refresh_pending = False
        self._dragging = False

        self._drag_scene_offset = QPointF(
            0,
            0
        )

        self.padding = 8

        self.minimap_zoom = 1.0
        self.minimap_zoom_min = 0.25
        self.minimap_zoom_max = 8.0
        self.minimap_zoom_step = 1.25

        # 1.0 = exact minimap position.
        # Lower values make dragging feel softer/slower.
        self.pan_drag_strength = 0.25

        self.setMinimumHeight(
            100
        )

        self.setMaximumHeight(
            10000
        )

        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.setMouseTracking(
            True
        )

        self.connect_events()
        self.reconnect_view()
        self.schedule_refresh()

    # -----------------------------------------------------
    # Events / lifecycle
    # -----------------------------------------------------

    def connect_events(self):

        bus = events.get_event_bus()

        bus.items_changed.connect(
            self.schedule_refresh
        )

        bus.item_changed.connect(
            self.schedule_refresh
        )

        bus.tabs_changed.connect(
            self.on_tabs_changed
        )

        bus.current_tab_changed.connect(
            self.on_current_tab_changed
        )

    def on_tabs_changed(self):

        self.reconnect_view()
        self.schedule_refresh()

    def on_current_tab_changed(
        self,
        tab_info
    ):

        self.reconnect_view()
        self.schedule_refresh()

    def schedule_refresh(self):

        if self._refresh_pending:
            return

        self._refresh_pending = True

        QTimer.singleShot(
            0,
            self.refresh
        )

    def refresh(self):

        self._refresh_pending = False

        base_bounds = self.compute_scene_bounds()

        self.scene_bounds = self.apply_minimap_zoom_to_bounds(
            base_bounds
        )

        self.update()

    # -----------------------------------------------------
    # View binding
    # -----------------------------------------------------

    def reconnect_view(self):

        self.uninstall_view_filter()

        self.scene = None
        self.view = None
        self.scene_bounds = None

        try:

            self.scene = NEx.get_scene()

        except Exception:

            self.scene = None

        try:

            self.view = scene_view.get_view_for_scene(
                self.scene
            )

        except Exception:

            self.view = None

        self.install_view_filter()


    def install_view_filter(self):

        if not self.view:
            return

        try:

            self.view.installEventFilter(
                self.view_filter
            )

        except Exception:
            pass

        try:

            viewport = self.view.viewport()

            if viewport:

                viewport.installEventFilter(
                    self.view_filter
                )

        except Exception:
            pass

        try:

            self.view.destroyed.connect(
                self.on_node_editor_view_destroyed
            )

        except Exception:
            pass

        try:

            viewport = self.view.viewport()

            if viewport:

                viewport.destroyed.connect(
                    self.on_node_editor_view_destroyed
                )

        except Exception:
            pass


    def uninstall_view_filter(self):

        view = self.view

        if not view:
            return

        try:

            view.removeEventFilter(
                self.view_filter
            )

        except Exception:
            pass

        try:

            viewport = view.viewport()

            if viewport:

                viewport.removeEventFilter(
                    self.view_filter
                )

        except Exception:
            pass


    def on_node_editor_view_destroyed(
        self,
        *args
    ):

        try:

            self.uninstall_view_filter()

        except Exception:
            pass

        self.view = None
        self.scene = None
        self.scene_bounds = None

        try:

            self.update()

        except Exception:
            pass

    # -----------------------------------------------------
    # Scene collection
    # -----------------------------------------------------

    def get_scene_items(self):

        if not self.scene:
            return []

        try:

            return self.scene.items()

        except RuntimeError:
            return []

        except Exception:
            return []

    def get_native_node_items(self):

        result = []

        for item in self.get_scene_items():

            if NEx.is_nex_item(
                item
            ):
                continue

            try:

                node_name = NEx.get_node_name(
                    item
                )

            except Exception:

                node_name = None

            if not node_name:
                continue

            result.append(
                item
            )

        return result

    def get_nex_items(self):

        result = []

        for item in self.get_scene_items():

            if not NEx.is_nex_item(
                item
            ):
                continue

            result.append(
                item
            )

        return self.sort_nex_items_for_minimap(
            result
        )

    def is_nex_container_item(
        self,
        item
    ):

        return bool(
            getattr(
                item,
                "nex_container",
                False
            )
        )

    def get_nex_hierarchy_depth(
        self,
        item
    ):

        depth = 0

        try:

            parent = item.get_parent_container()

        except RuntimeError:
            return depth

        except Exception:
            return depth

        while parent:

            depth += 1

            try:

                parent = parent.get_parent_container()

            except RuntimeError:
                break

            except Exception:
                break

        return depth

    def get_nex_minimap_sort_key(
        self,
        item
    ):

        depth = self.get_nex_hierarchy_depth(
            item
        )

        item_type = getattr(
            item,
            "nex_item_type",
            ""
        )

        is_container = self.is_nex_container_item(
            item
        )

        try:

            z_value = item.zValue()

        except RuntimeError:

            z_value = 0

        except Exception:

            z_value = 0

        title = getattr(
            item,
            "title",
            ""
        ).lower()

        return (
            depth,
            0 if is_container else 1,
            z_value,
            item_type,
            title
        )

    def sort_nex_items_for_minimap(
        self,
        items
    ):

        return sorted(
            items,
            key=self.get_nex_minimap_sort_key
        )

    def get_nex_container_items(self):

        return [
            item
            for item in self.get_nex_items()
            if self.is_nex_container_item(
                item
            )
        ]

    def get_nex_leaf_items(self):

        return [
            item
            for item in self.get_nex_items()
            if not self.is_nex_container_item(
                item
            )
        ]

    def compute_scene_bounds(self):

        rects = []

        for item in (
            self.get_native_node_items()
            + self.get_nex_items()
        ):

            try:

                rect = item.sceneBoundingRect()

            except RuntimeError:
                continue

            except Exception:
                continue

            if rect.isNull() or rect.isEmpty():
                continue

            rects.append(
                rect
            )

        viewport_rect = self.get_viewport_scene_rect()

        if viewport_rect:

            rects.append(
                viewport_rect
            )

        if not rects:
            return None

        bounds = rects[0]

        for rect in rects[1:]:

            bounds = bounds.united(
                rect
            )

        return bounds.adjusted(
            -100,
            -100,
            100,
            100
        )

    def get_viewport_scene_rect(self):

        if not self.view:
            return None

        try:

            return self.view.mapToScene(
                self.view.viewport().rect()
            ).boundingRect()

        except RuntimeError:
            return None

        except Exception:
            return None

    def get_viewport_scene_center(self):

        viewport_rect = self.get_viewport_scene_rect()

        if not viewport_rect:
            return None

        return viewport_rect.center()

    # -----------------------------------------------------
    # Mapping
    # -----------------------------------------------------

    def get_draw_rect(self):

        rect = self.rect()

        return QRectF(
            rect.left() + self.padding,
            rect.top() + self.padding,
            rect.width() - self.padding * 2,
            rect.height() - self.padding * 2
        )

    def get_scale_and_offset(self):

        if not self.scene_bounds:
            return None

        draw_rect = self.get_draw_rect()

        if (
            self.scene_bounds.width() <= 0
            or self.scene_bounds.height() <= 0
        ):
            return None

        scale_x = (
            draw_rect.width()
            / self.scene_bounds.width()
        )

        scale_y = (
            draw_rect.height()
            / self.scene_bounds.height()
        )

        scale = min(
            scale_x,
            scale_y
        )

        content_width = (
            self.scene_bounds.width()
            * scale
        )

        content_height = (
            self.scene_bounds.height()
            * scale
        )

        offset_x = (
            draw_rect.left()
            + (
                draw_rect.width()
                - content_width
            )
            * 0.5
        )

        offset_y = (
            draw_rect.top()
            + (
                draw_rect.height()
                - content_height
            )
            * 0.5
        )

        return (
            scale,
            offset_x,
            offset_y
        )

    def scene_to_map_point(
        self,
        point
    ):

        mapping = self.get_scale_and_offset()

        if not mapping:
            return QPointF(
                0,
                0
            )

        scale, offset_x, offset_y = mapping

        return QPointF(
            offset_x
            + (
                point.x()
                - self.scene_bounds.left()
            )
            * scale,
            offset_y
            + (
                point.y()
                - self.scene_bounds.top()
            )
            * scale
        )

    def scene_to_map_rect(
        self,
        scene_rect
    ):

        top_left = self.scene_to_map_point(
            scene_rect.topLeft()
        )

        bottom_right = self.scene_to_map_point(
            scene_rect.bottomRight()
        )

        return QRectF(
            top_left,
            bottom_right
        ).normalized()

    def map_to_scene_point(
        self,
        point
    ):

        mapping = self.get_scale_and_offset()

        if not mapping or not self.scene_bounds:
            return QPointF(
                0,
                0
            )

        scale, offset_x, offset_y = mapping

        if scale == 0:
            return QPointF(
                0,
                0
            )

        return QPointF(
            self.scene_bounds.left()
            + (
                point.x()
                - offset_x
            )
            / scale,
            self.scene_bounds.top()
            + (
                point.y()
                - offset_y
            )
            / scale
        )
    # -----------------------------------------------------
    # Extra Minimap Zoom
    # -----------------------------------------------------

    def get_minimap_zoom_center(
        self,
        bounds
    ):

        viewport_center = self.get_viewport_scene_center()

        if viewport_center is not None:
            return viewport_center

        if bounds:
            return bounds.center()

        return QPointF(
            0,
            0
        )


    def apply_minimap_zoom_to_bounds(
        self,
        bounds
    ):

        if not bounds:
            return None

        zoom = max(
            self.minimap_zoom_min,
            min(
                self.minimap_zoom,
                self.minimap_zoom_max
            )
        )

        if zoom == 1.0:
            return bounds

        center = self.get_minimap_zoom_center(
            bounds
        )

        width = (
            bounds.width()
            / zoom
        )

        height = (
            bounds.height()
            / zoom
        )

        return QRectF(
            center.x() - width * 0.5,
            center.y() - height * 0.5,
            width,
            height
        )


    def set_minimap_zoom(
        self,
        zoom
    ):

        self.minimap_zoom = max(
            self.minimap_zoom_min,
            min(
                zoom,
                self.minimap_zoom_max
            )
        )

        self.schedule_refresh()


    def zoom_in(self):

        self.set_minimap_zoom(
            self.minimap_zoom
            * self.minimap_zoom_step
        )


    def zoom_out(self):

        self.set_minimap_zoom(
            self.minimap_zoom
            / self.minimap_zoom_step
        )


    def reset_zoom(self):

        self.set_minimap_zoom(
            1.0
        )
    # -----------------------------------------------------
    # Viewport minimap helpers
    # -----------------------------------------------------

    def get_viewport_minimap_rect(self):

        viewport_rect = self.get_viewport_scene_rect()

        if not viewport_rect:
            return None

        return self.scene_to_map_rect(
            viewport_rect
        )

    def minimap_pos_is_inside_viewport(
        self,
        pos
    ):

        map_rect = self.get_viewport_minimap_rect()

        if not map_rect:
            return False

        return map_rect.contains(
            QPointF(
                pos
            )
        )

    # -----------------------------------------------------
    # Painting helpers
    # -----------------------------------------------------

    def get_nex_color(
        self,
        item
    ):

        color = getattr(
            item,
            "background_color",
            QColor(
                80,
                120,
                255,
                160
            )
        )

        return QColor(
            color.red(),
            color.green(),
            color.blue(),
            170
        )

    def paint_background(
        self,
        painter
    ):

        painter.setRenderHint(
            QPainter.Antialiasing
        )

        painter.setBrush(
            QBrush(
                QColor(
                    22,
                    22,
                    22,
                    230
                )
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    90,
                    90,
                    90,
                    180
                ),
                1
            )
        )

        painter.drawRoundedRect(
            self.rect().adjusted(
                1,
                1,
                -1,
                -1
            ),
            6,
            6
        )

    def paint_empty_state(
        self,
        painter
    ):

        painter.setPen(
            QColor(
                180,
                180,
                180,
                180
            )
        )

        painter.drawText(
            self.rect(),
            Qt.AlignCenter,
            "No Node Editor data"
        )

    def paint_native_nodes(
        self,
        painter
    ):

        painter.setBrush(
            QBrush(
                QColor(
                    120,
                    120,
                    120,
                    150
                )
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    200,
                    200,
                    200,
                    130
                ),
                1
            )
        )

        for item in self.get_native_node_items():

            try:

                scene_rect = item.sceneBoundingRect()

            except Exception:
                continue

            map_rect = self.scene_to_map_rect(
                scene_rect
            )

            painter.drawRoundedRect(
                map_rect,
                2,
                2
            )

    def paint_single_nex_item(
        self,
        painter,
        item
    ):

        try:

            scene_rect = item.sceneBoundingRect()

        except Exception:
            return

        map_rect = self.scene_to_map_rect(
            scene_rect
        )

        color = self.get_nex_color(
            item
        )

        painter.setBrush(
            QBrush(
                color
            )
        )

        painter.setPen(
            QPen(
                QColor(
                    255,
                    255,
                    255,
                    160
                ),
                1
            )
        )

        painter.drawRoundedRect(
            map_rect,
            2,
            2
        )

    def paint_nex_containers(
        self,
        painter
    ):

        for item in self.get_nex_container_items():

            self.paint_single_nex_item(
                painter,
                item
            )

    def paint_nex_leaf_items(
        self,
        painter
    ):

        for item in self.get_nex_leaf_items():

            self.paint_single_nex_item(
                painter,
                item
            )

    def paint_viewport(
        self,
        painter
    ):

        viewport_rect = self.get_viewport_scene_rect()

        if not viewport_rect:
            return

        map_rect = self.scene_to_map_rect(
            viewport_rect
        )

        painter.setBrush(
            Qt.NoBrush
        )

        painter.setPen(
            QPen(
                QColor(
                    90,
                    255,
                    130,
                    240
                ),
                2
            )
        )

        painter.drawRoundedRect(
            map_rect,
            3,
            3
        )

    def paintEvent(
        self,
        event
    ):

        painter = QPainter(
            self
        )

        self.paint_background(
            painter
        )

        if not self.scene_bounds:

            self.paint_empty_state(
                painter
            )

            painter.end()
            return

        self.paint_nex_containers(
            painter
        )

        self.paint_native_nodes(
            painter
        )

        self.paint_nex_leaf_items(
            painter
        )

        self.paint_viewport(
            painter
        )

        painter.end()

    # -----------------------------------------------------
    # Mouse navigation
    # -----------------------------------------------------

    def center_view_from_minimap_pos(
        self,
        pos,
        use_drag_offset=True,
        soften=True
    ):

        if not self.view or not self.scene_bounds:
            return

        scene_pos = self.map_to_scene_point(
            QPointF(
                pos
            )
        )

        if use_drag_offset:

            scene_pos = (
                scene_pos
                - self._drag_scene_offset
            )

        if soften:

            current_center = self.get_viewport_scene_center()

            if current_center is not None:

                strength = getattr(
                    self,
                    "pan_drag_strength",
                    1.0
                )

                scene_pos = QPointF(
                    current_center.x()
                    + (
                        scene_pos.x()
                        - current_center.x()
                    )
                    * strength,
                    current_center.y()
                    + (
                        scene_pos.y()
                        - current_center.y()
                    )
                    * strength
                )

        try:

            self.view.centerOn(
                scene_pos
            )

        except Exception:
            return

        self.schedule_refresh()

    def mousePressEvent(
        self,
        event
    ):

        if event.button() != Qt.LeftButton:

            event.accept()
            return

        self._dragging = True

        mouse_scene_pos = self.map_to_scene_point(
            QPointF(
                event.pos()
            )
        )

        viewport_center = self.get_viewport_scene_center()

        if (
            viewport_center is not None
            and self.minimap_pos_is_inside_viewport(
                event.pos()
            )
        ):

            self._drag_scene_offset = (
                mouse_scene_pos
                - viewport_center
            )

            use_drag_offset = True
            soften = True

        else:

            self._drag_scene_offset = QPointF(
                0,
                0
            )

            # Clicking outside viewport should feel like a clean jump.
            use_drag_offset = False
            soften = False

        self.center_view_from_minimap_pos(
            event.pos(),
            use_drag_offset=use_drag_offset,
            soften=soften
        )

        event.accept()

    def mouseMoveEvent(
        self,
        event
    ):

        if not self._dragging:
            return

        self.center_view_from_minimap_pos(
            event.pos(),
            use_drag_offset=True,
            soften=True
        )

        event.accept()

    def mouseReleaseEvent(
        self,
        event
    ):

        if self._dragging:

            self._dragging = False

            self.center_view_from_minimap_pos(
                event.pos(),
                use_drag_offset=True,
                soften=True
            )

            self._drag_scene_offset = QPointF(
                0,
                0
            )

            event.accept()
            return

        event.accept()

    def wheelEvent(
        self,
        event
    ):

        try:

            delta = event.angleDelta().y()

        except Exception:

            delta = 0

        if delta > 0:

            self.zoom_in()

        elif delta < 0:

            self.zoom_out()

        event.accept()