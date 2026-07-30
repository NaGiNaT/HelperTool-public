from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QMouseEvent


class BaseWindow(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.dragging = False
        self.drag_position = QPoint()

        self.margin = 8
        self.resize_direction = None
        self.resize_start_pos = None
        self.resize_start_geometry = None

        self.is_maximized = False

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            self.resize_direction = self._get_resize_direction(pos)

            if self.resize_direction:
                self.resize_start_pos = event.globalPos()
                self.resize_start_geometry = self.geometry()
                self.setMouseTracking(True)
            elif pos.y() <= 35:
                self.dragging = True
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.resize_direction and self.resize_start_pos is not None:
            delta = event.globalPos() - self.resize_start_pos
            new_geometry = self.resize_start_geometry

            if 'left' in self.resize_direction:
                new_geometry.setLeft(new_geometry.left() + delta.x())
            if 'right' in self.resize_direction:
                new_geometry.setRight(new_geometry.right() + delta.x())
            if 'top' in self.resize_direction:
                new_geometry.setTop(new_geometry.top() + delta.y())
            if 'bottom' in self.resize_direction:
                new_geometry.setBottom(new_geometry.bottom() + delta.y())

            if new_geometry.width() > 400 and new_geometry.height() > 300:
                self.setGeometry(new_geometry)

        elif event.buttons() == Qt.LeftButton and self.dragging:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

        else:
            direction = self._get_resize_direction(event.pos())
            if direction:
                self.setCursor(self._get_cursor_for_direction(direction))
            else:
                self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resize_direction = None
            self.resize_start_pos = None
            self.resize_start_geometry = None
            self.setMouseTracking(False)
            self.setCursor(Qt.ArrowCursor)
            event.accept()

    def _get_resize_direction(self, pos):
        m = self.margin
        w, h = self.width(), self.height()
        left = pos.x() <= m
        right = pos.x() >= w - m
        top = pos.y() <= m
        bottom = pos.y() >= h - m

        if left and top: return 'left_top'
        if left and bottom: return 'left_bottom'
        if right and top: return 'right_top'
        if right and bottom: return 'right_bottom'
        if left: return 'left'
        if right: return 'right'
        if top: return 'top'
        if bottom: return 'bottom'
        return None

    def _get_cursor_for_direction(self, direction):
        cursors = {
            'left_top': Qt.SizeFDiagCursor,
            'right_bottom': Qt.SizeFDiagCursor,
            'right_top': Qt.SizeBDiagCursor,
            'left_bottom': Qt.SizeBDiagCursor,
            'left': Qt.SizeHorCursor,
            'right': Qt.SizeHorCursor,
            'top': Qt.SizeVerCursor,
            'bottom': Qt.SizeVerCursor,
        }
        return cursors.get(direction, Qt.ArrowCursor)

    def toggle_maximize(self, maximize_btn=None):
        if self.is_maximized:
            self.showNormal()
            self.is_maximized = False
            if maximize_btn:
                maximize_btn.setText("□")
        else:
            self.showMaximized()
            self.is_maximized = True
            if maximize_btn:
                maximize_btn.setText("❐")