import sys
import ctypes
import win32gui
import win32con
from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtCore import Qt
from mainwindow import Ui_Dialog  # Generated with PyQt6
import keyboard
import pyautogui

class CrosshairOverlay(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Crosshair Overlay")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Screen center
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        self.screen_center = QtCore.QPoint(screen.width() // 2, screen.height() // 2)

        # Crosshair properties
        self.shape = "X"
        self.size = 50
        self.color_index = 0
        self.colors = [
            QtGui.QColor(0, 255, 255),  # Light blue
            QtGui.QColor(0, 0, 255),    # Dark blue
            QtGui.QColor(255, 0, 255),  # Light purple
            QtGui.QColor(128, 0, 128),  # Dark purple
            QtGui.QColor(255, 255, 0),  # Neon yellow
            QtGui.QColor(0, 255, 0),    # Neon green
            QtGui.QColor(0, 0, 0),      # Black
            QtGui.QColor(255, 255, 255) # White
        ]
        self.overlay_enabled = True

        # Resize state (for mouse-based resizing)
        self.resizing = False
        self.start_x = None

        # Adjust window size and position
        self.resize(self.size, self.size)
        self.move(self.screen_center.x() - self.size // 2, self.screen_center.y() - self.size // 2)

    def paintEvent(self, event):
        if not self.overlay_enabled:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtGui.QPen(self.colors[self.color_index], 2))

        center = QtCore.QPoint(self.width() // 2, self.height() // 2)
        rect = QtCore.QRect(0, 0, self.size, self.size)
        if self.shape == "Circle":
            painter.drawEllipse(rect)
        elif self.shape == "Square":
            painter.drawRect(rect)
        elif self.shape == "Triangle":
            points = [
                QtCore.QPoint(self.size // 2, 0),
                QtCore.QPoint(0, self.size),
                QtCore.QPoint(self.size, self.size)
            ]
            painter.drawPolygon(QtGui.QPolygon(points))
        elif self.shape == "X":
            painter.drawLine(0, 0, self.size, self.size)
            painter.drawLine(self.size, 0, 0, self.size)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and keyboard.is_pressed('ctrl'):
            self.resizing = True
            self.start_x = event.globalPosition().x()  # Use global mouse position

    def mouseMoveEvent(self, event):
        if self.resizing:
            current_x = event.globalPosition().x()
            delta = current_x - self.start_x
            self.size = max(10, self.size + int(delta / 5))  # Scale delta for smoother resizing
            self.resize(self.size, self.size)
            self.move(self.screen_center.x() - self.size // 2, self.screen_center.y() - self.size // 2)
            self.start_x = current_x  # Update start_x for continuous dragging
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = False
            self.start_x = None

class MainWindow(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # Initialize overlay
        self.overlay = CrosshairOverlay()

        # Connect radio buttons
        self.ui.radioButton.toggled.connect(lambda: self.set_shape("X"))
        self.ui.radioButton_2.toggled.connect(lambda: self.set_shape("Triangle"))
        self.ui.radioButton_3.toggled.connect(lambda: self.set_shape("Square"))
        self.ui.radioButton_4.toggled.connect(lambda: self.set_shape("Circle"))

        # Connect sliders
        self.ui.horizontalSlider.setMinimum(10)
        self.ui.horizontalSlider.setMaximum(200)
        self.ui.horizontalSlider.setValue(self.overlay.size)
        self.ui.horizontalSlider.valueChanged.connect(self.set_size)

        self.ui.horizontalSlider_2.setMinimum(0)
        self.ui.horizontalSlider_2.setMaximum(len(self.overlay.colors) - 1)
        self.ui.horizontalSlider_2.setValue(self.overlay.color_index)
        self.ui.horizontalSlider_2.valueChanged.connect(self.set_color)

        # Keyboard shortcuts (removed Ctrl+Shift+I)
        keyboard.add_hotkey('ctrl+shift+o', self.toggle_overlay)
        keyboard.add_hotkey('ctrl+o', self.toggle_foreground)

        # Ensure overlay is shown
        self.overlay.show()

    def set_shape(self, shape):
        self.overlay.shape = shape
        self.overlay.update()

    def set_size(self, value):
        self.overlay.size = value
        self.overlay.resize(self.overlay.size, self.overlay.size)
        self.overlay.move(self.overlay.screen_center.x() - self.overlay.size // 2,
                         self.overlay.screen_center.y() - self.overlay.size // 2)
        self.overlay.update()

    def set_color(self, value):
        self.overlay.color_index = value
        self.overlay.update()

    def toggle_overlay(self):
        self.overlay.overlay_enabled = not self.overlay.overlay_enabled
        self.overlay.update()

    def toggle_foreground(self):
        if self.isVisible():
            self.hide()
            # Keep overlay visible
            self.overlay.show()
        else:
            self.show()
            self.overlay.show()
            self.activateWindow()

    def closeEvent(self, event):
        keyboard.unhook_all()
        self.overlay.close()
        event.accept()

def make_clickthrough(hwnd):
    try:
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT)
    except Exception as e:
        print(f"Error setting clickthrough: {e}")

def main():
    # Set DPI awareness
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)  # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE
    except Exception as e:
        print(f"Failed to set DPI awareness: {e}")

    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()

    # Set clickthrough for overlay
    hwnd = window.overlay.windowHandle().winId()
    make_clickthrough(hwnd)

    # Move mouse to center to avoid accidental clicks
    pyautogui.moveTo(window.overlay.screen_center.x(), window.overlay.screen_center.y())

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
