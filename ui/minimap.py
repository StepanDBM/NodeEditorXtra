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

        # Wheel on actual Maya Node Editor:
        # viewport changed, not item geometry.
        if event_type == QEvent.Wheel:

            try:

                self.minimap.schedule_viewport_refresh()

                QTimer.singleShot(
                    16,
                    self.minimap.schedule_viewport_refresh
                )

                QTimer.singleShot(
                    50,
                    self.minimap.schedule_viewport_refresh
                )

            except Exception:
                pass

            return False

        # Mouse move in Node Editor may mean:
        # - viewport pan
        # - native node drag
        # - NEx item drag
        #
        # So update cached geometry cheaply.
        if event_type == QEvent.MouseMove:

            try:

                self.minimap.schedule_geometry_refresh()

            except Exception:
                pass

            return False

        if event_type in (
            QEvent.MouseButtonPress,
            QEvent.MouseButtonRelease,
            QEvent.Resize,
            QEvent.Show,
            QEvent.Hide
        ):

            try:

                self.minimap.schedule_viewport_refresh()

            except Exception:
                pass

            if event_type == QEvent.MouseButtonRelease:

                try:

                    self.minimap.schedule_geometry_refresh()

                except Exception:
                    pass

            return False

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

        
        """
        separate minimap Model vs Viewport Refresh split:
        Model refresh:
            Rebuild cached NEx/native draw data and scene bounds.

        Viewport refresh:
            Only update the green viewport rectangle and repaint.
        """
        self.viewport_scene_rect = None

        self.draw_native_entries = []
        self.draw_nex_container_entries = []
        self.draw_nex_leaf_entries = []

        self._model_refresh_pending = False
        self._viewport_refresh_pending = False
        self._geometry_refresh_pending = False

        self.view_filter = MiniMapViewFilter(
            self
        )

        #self._refresh_pending = False
        self._dragging = False

        self._minimap_panning = False
        self._minimap_pan_start_pos = QPointF(
            0,
            0
        )
        self._minimap_pan_start_bounds = None

        self._drag_scene_offset = QPointF(
            0,
            0
        )

        self.padding = 8

        self.minimap_zoom = 1.0
        self.minimap_zoom_min = 0.25
        self.minimap_zoom_max = 8.0
        self.minimap_zoom_step = 1.25

        self.fit_mode = "all"

        self._hit_items = []

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
        self.schedule_model_refresh()

    # -----------------------------------------------------
    # Events / lifecycle
    # -----------------------------------------------------

    def get_cached_entry_for_item(
        self,
        item
    ):

        try:

            scene_rect = item.sceneBoundingRect()

        except RuntimeError:
            return None

        except Exception:
            return None

        try:

            if scene_rect.isNull() or scene_rect.isEmpty():
                return None

        except Exception:
            return None

        return (
            item,
            scene_rect
        )

    def connect_events(self):

        bus = events.get_event_bus()

        bus.items_changed.connect(
            self.schedule_model_refresh
        )

        bus.item_changed.connect(
            self.schedule_model_refresh
        )

        bus.tabs_changed.connect(
            self.on_tabs_changed
        )

        bus.current_tab_changed.connect(
            self.on_current_tab_changed
        )

    def on_tabs_changed(self):

        self.reconnect_view()
        self.schedule_model_refresh()

    def on_current_tab_changed(
        self,
        tab_info
    ):

        self.reconnect_view()
        self.schedule_model_refresh()

    def schedule_refresh(self):

        # Backward-compatible alias.
        self.schedule_model_refresh()


    def schedule_model_refresh(self):

        if self._model_refresh_pending:
            return

        self._model_refresh_pending = True

        QTimer.singleShot(
            0,
            self.refresh_model
        )


    def schedule_viewport_refresh(self):

        if self._viewport_refresh_pending:
            return

        self._viewport_refresh_pending = True

        QTimer.singleShot(
            0,
            self.refresh_viewport
        )

    def schedule_geometry_refresh(self):

        if self._geometry_refresh_pending:
            return

        self._geometry_refresh_pending = True

        QTimer.singleShot(
            16,
            self.refresh_geometry
        )


    def refresh_geometry(self):

        self._geometry_refresh_pending = False

        self.refresh_cached_entry_rects()

        base_bounds = self.compute_scene_bounds_from_cache()

        self.scene_bounds = self.apply_minimap_zoom_to_bounds(
            base_bounds
        )

        self.refresh_viewport()

        self.update()


    def refresh_cached_entry_rects(self):

        self.draw_native_entries = self.refresh_entry_list_rects(
            self.draw_native_entries
        )

        self.draw_nex_container_entries = self.refresh_entry_list_rects(
            self.draw_nex_container_entries
        )

        self.draw_nex_leaf_entries = self.refresh_entry_list_rects(
            self.draw_nex_leaf_entries
        )


    def refresh_entry_list_rects(
        self,
        entries
    ):

        refreshed = []

        for item, old_rect in entries:

            entry = self.get_cached_entry_for_item(
                item
            )

            if entry:

                refreshed.append(
                    entry
                )

        return refreshed


    def refresh_model(self):

        self._model_refresh_pending = False

        self.rebuild_draw_cache()

        base_bounds = self.compute_scene_bounds_from_cache()

        self.scene_bounds = self.apply_minimap_zoom_to_bounds(
            base_bounds
        )

        self.refresh_viewport()

        self.update()


    def refresh_viewport(self):

        self._viewport_refresh_pending = False

        self.viewport_scene_rect = self.get_viewport_scene_rect()

        self.update()

    def rebuild_draw_cache(self):

        self.draw_native_entries = []
        self.draw_nex_container_entries = []
        self.draw_nex_leaf_entries = []

        native_items = self.get_native_node_items()

        for item in native_items:

            entry = self.get_cached_entry_for_item(
                item
            )

            if entry:

                self.draw_native_entries.append(
                    entry
                )

        nex_items = self.get_nex_items()

        for item in nex_items:

            entry = self.get_cached_entry_for_item(
                item
            )

            if not entry:
                continue

            if self.is_nex_container_item(
                item
            ):

                self.draw_nex_container_entries.append(
                    entry
                )

            else:

                self.draw_nex_leaf_entries.append(
                    entry
                )
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
        self.viewport_scene_rect = None

        self.draw_native_entries = []
        self.draw_nex_container_entries = []
        self.draw_nex_leaf_entries = []

        try:

            self.update()

        except Exception:
            pass

    # -----------------------------------------------------
    # Scene collection
    # -----------------------------------------------------

    def get_selected_scene_items(self):

        if not self.scene:
            return []

        try:

            selected_items = self.scene.selectedItems()

        except RuntimeError:
            return []

        except Exception:
            return []

        result = []

        for item in selected_items:

            try:

                if item.scene() is None:
                    continue

            except Exception:
                continue

            result.append(
                item
            )

        return result


    def get_bounds_from_scene_items(
        self,
        items,
        include_viewport=False
    ):

        rects = []

        for item in items:

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

        if include_viewport:

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
    #just in case I forget any calls
    def compute_scene_bounds(self):

        return self.compute_scene_bounds_from_cache()
    
    def get_items_from_entries(
        self,
        entries
    ):

        return [
            item
            for item, scene_rect in entries
        ]


    def get_bounds_from_entries(
        self,
        entries,
        include_viewport=False
    ):

        rects = [
            scene_rect
            for item, scene_rect in entries
        ]

        if include_viewport:

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


    def compute_scene_bounds_from_cache(self):

        if self.fit_mode == "nex":

            bounds = self.get_bounds_from_entries(
                self.draw_nex_container_entries
                + self.draw_nex_leaf_entries,
                include_viewport=False
            )

            if bounds:
                return bounds

        if self.fit_mode == "selection":

            selected_items = self.get_selected_scene_items()

            if selected_items:

                return self.get_bounds_from_scene_items(
                    selected_items,
                    include_viewport=False
                )

        return self.get_bounds_from_entries(
            self.draw_native_entries
            + self.draw_nex_container_entries
            + self.draw_nex_leaf_entries,
            include_viewport=True
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

    def get_event_local_pos(
        self,
        event
    ):

        try:

            return QPointF(
                event.position()
            )

        except Exception:

            return QPointF(
                event.pos()
            )


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

    def set_fit_mode(
        self,
        fit_mode
    ):

        self.fit_mode = fit_mode

        self.minimap_zoom = 1.0

        self.schedule_refresh()


    def fit_all(self):

        self.set_fit_mode(
            "all"
        )


    def fit_nex(self):

        self.set_fit_mode(
            "nex"
        )


    def fit_selection(self):

        self.set_fit_mode(
            "selection"
        )

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

        old_zoom = self.minimap_zoom

        new_zoom = self.clamp_minimap_zoom(
            zoom
        )

        if new_zoom == old_zoom:
            return

        zoom_factor = (
            new_zoom
            / old_zoom
        )

        center_pos = QPointF(
            self.rect().center()
        )

        anchor_scene_pos = self.map_to_scene_point(
            center_pos
        )

        self.minimap_zoom = new_zoom

        self.zoom_scene_bounds_around_point(
            anchor_scene_pos,
            zoom_factor
        )


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

    def clamp_minimap_zoom(
        self,
        zoom
    ):

        return max(
            self.minimap_zoom_min,
            min(
                zoom,
                self.minimap_zoom_max
            )
        )


    def zoom_scene_bounds_around_point(
        self,
        anchor_scene_pos,
        zoom_factor
    ):

        if not self.scene_bounds:
            return

        if zoom_factor == 0:
            return

        old_bounds = QRectF(
            self.scene_bounds
        )

        old_width = old_bounds.width()
        old_height = old_bounds.height()

        if (
            old_width <= 0
            or old_height <= 0
        ):
            return

        relative_x = (
            anchor_scene_pos.x()
            - old_bounds.left()
        ) / old_width

        relative_y = (
            anchor_scene_pos.y()
            - old_bounds.top()
        ) / old_height

        new_width = (
            old_width
            / zoom_factor
        )

        new_height = (
            old_height
            / zoom_factor
        )

        new_left = (
            anchor_scene_pos.x()
            - relative_x
            * new_width
        )

        new_top = (
            anchor_scene_pos.y()
            - relative_y
            * new_height
        )

        self.scene_bounds = QRectF(
            new_left,
            new_top,
            new_width,
            new_height
        )

        self.update()


    def zoom_minimap_at_map_pos(
        self,
        map_pos,
        zoom_in=True
    ):

        if not self.scene_bounds:

            self.schedule_model_refresh()
            return

        old_zoom = self.minimap_zoom

        if zoom_in:

            new_zoom = self.clamp_minimap_zoom(
                self.minimap_zoom
                * self.minimap_zoom_step
            )

        else:

            new_zoom = self.clamp_minimap_zoom(
                self.minimap_zoom
                / self.minimap_zoom_step
            )

        if new_zoom == old_zoom:
            return

        zoom_factor = (
            new_zoom
            / old_zoom
        )

        anchor_scene_pos = self.map_to_scene_point(
            map_pos
        )

        self.minimap_zoom = new_zoom

        self.zoom_scene_bounds_around_point(
            anchor_scene_pos,
            zoom_factor
        )


    def zoom_minimap_at_center(
        self,
        zoom_in=True
    ):

        center_pos = QPointF(
            self.rect().center()
        )

        self.zoom_minimap_at_map_pos(
            center_pos,
            zoom_in=zoom_in
        )
    # -----------------------------------------------------
    # Viewport minimap helpers
    # -----------------------------------------------------

    def get_viewport_minimap_rect(self):

        viewport_rect = self.viewport_scene_rect

        if not viewport_rect:

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

        for item, scene_rect in self.draw_native_entries:

            map_rect = self.scene_to_map_rect(
                scene_rect
            )

            self._hit_items.append(
                (
                    map_rect,
                    item
                )
            )

            painter.drawRoundedRect(
                map_rect,
                2,
                2
            )

    def paint_single_nex_item(
        self,
        painter,
        item,
        scene_rect
    ):

        map_rect = self.scene_to_map_rect(
            scene_rect
        )

        self._hit_items.append(
            (
                map_rect,
                item
            )
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

        for item, scene_rect in self.draw_nex_container_entries:

            self.paint_single_nex_item(
                painter,
                item,
                scene_rect
            )

    def paint_nex_leaf_items(
        self,
        painter
    ):

        for item, scene_rect in self.draw_nex_leaf_entries:

            self.paint_single_nex_item(
                painter,
                item,
                scene_rect
            )

    def paint_viewport(
        self,
        painter
    ):

        map_rect = self.get_viewport_minimap_rect()

        if not map_rect:
            return

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

        painter = QPainter(self)

        self._hit_items = []

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

        self.schedule_viewport_refresh()

    def mouseDoubleClickEvent(
        self,
        event
    ):

        if event.button() != Qt.LeftButton:

            event.accept()
            return

        click_pos = QPointF(
            event.pos()
        )

        # Reverse because later-painted items are visually on top.
        for map_rect, scene_item in reversed(
            self._hit_items
        ):

            try:

                if not map_rect.contains(
                    click_pos
                ):
                    continue

            except Exception:
                continue

            try:

                scene_view.frame_view_on_item(
                    scene_item
                )
                self.schedule_viewport_refresh()

                QTimer.singleShot(
                    50,
                    self.schedule_viewport_refresh
                )

                QTimer.singleShot(
                    150,
                    self.schedule_viewport_refresh
                )

            except Exception:
                pass

            event.accept()
            return

        event.accept()


    def mousePressEvent(
        self,
        event
    ):

        if event.button() == Qt.MiddleButton:

            if self.start_minimap_pan(
                event
            ):

                event.accept()
                return

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

        if self._minimap_panning:

            self.update_minimap_pan(
                event
            )

            event.accept()
            return

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

        if (
            event.button() == Qt.MiddleButton
            and self._minimap_panning
        ):

            self.end_minimap_pan()

            event.accept()
            return

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

    #--------------------------------------------
    # WHEEL EVENTS ON ZOOM
    #--------------------------------------------




    def wheelEvent(
        self,
        event
    ):

        try:

            delta = event.angleDelta().y()

        except Exception:

            delta = 0

        if delta == 0:

            event.accept()
            return

        map_pos = self.get_event_local_pos(
            event
        )

        if delta > 0:

            self.zoom_minimap_at_map_pos(
                map_pos,
                zoom_in=True
            )

        else:

            self.zoom_minimap_at_map_pos(
                map_pos,
                zoom_in=False
            )

        event.accept()


    def start_minimap_pan(
        self,
        event
    ):

        if not self.scene_bounds:
            return False

        self._minimap_panning = True

        self._minimap_pan_start_pos = QPointF(
            event.pos()
        )

        self._minimap_pan_start_bounds = QRectF(
            self.scene_bounds
        )

        try:

            self.setCursor(
                Qt.ClosedHandCursor
            )

        except Exception:
            pass

        return True


    def update_minimap_pan(
        self,
        event
    ):

        if not self._minimap_panning:
            return

        if not self._minimap_pan_start_bounds:
            return

        mapping = self.get_scale_and_offset()

        if not mapping:
            return

        scale, offset_x, offset_y = mapping

        if scale == 0:
            return

        current_pos = QPointF(
            event.pos()
        )

        map_delta = (
            current_pos
            - self._minimap_pan_start_pos
        )

        scene_delta = QPointF(
            map_delta.x()
            / scale,
            map_delta.y()
            / scale
        )

        start_bounds = self._minimap_pan_start_bounds

        # Grab-paper behavior:
        # Drag right/down moves minimap contents right/down,
        # so the represented scene bounds move left/up.
        self.scene_bounds = QRectF(
            start_bounds.left()
            - scene_delta.x(),
            start_bounds.top()
            - scene_delta.y(),
            start_bounds.width(),
            start_bounds.height()
        )

        self.update()


    def end_minimap_pan(self):

        self._minimap_panning = False
        self._minimap_pan_start_bounds = None

        try:

            self.setCursor(
                Qt.ArrowCursor
            )

        except Exception:
            pass
