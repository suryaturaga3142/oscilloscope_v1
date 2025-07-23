import sys
from collections import deque
import serial
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QSlider, QLabel
)
from PySide6.QtCore import QTimer, Qt
import pyqtgraph as pg

class BatchSerialPlotter(QWidget):
    def __init__(self, port='COM8', baud=115200, buffer_len=1024):
        super().__init__()
        self.buffer_len = buffer_len
        self.buffer = deque(maxlen=buffer_len)
        self.is_paused = False

        # Set up Serial
        self.serial = serial.Serial(port, baud, timeout=0.05)

        # Create plot widget
        self.plot_widget = pg.PlotWidget(title="Batch UART Plot")
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen('b', width=2))
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setYRange(-0.1, 3.5, padding=0)
        self.plot_widget.setXRange(0, buffer_len - 1, padding=0)
        self.plot_widget.setLabel('left', 'Voltage [V]')
        self.plot_widget.setLabel('bottom', 'Sample Number')

        # Pause / Replay button
        self.pause_button = QPushButton("Pause")
        self.pause_button.setCheckable(True)
        self.pause_button.toggled.connect(self.toggle_pause)

        # Button layout (optional if you want to style/align more buttons later)
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.pause_button)
        button_layout.addStretch()  # Push button to top if more widgets are added

        # Buffer size slider
        self.slider_label = QLabel("Buffer: 1024")
        self.buffer_slider = QSlider(Qt.Vertical)
        self.buffer_slider.setMinimum(32)
        self.buffer_slider.setMaximum(2048)
        self.buffer_slider.setSingleStep(32)
        self.buffer_slider.setPageStep(32)
        self.buffer_slider.setValue(self.buffer_len)
        self.buffer_slider.valueChanged.connect(self.change_buffer_length)

        # ------------------- Left Panel Layout -------------------
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.pause_button)
        left_layout.addSpacing(20)
        left_layout.addWidget(self.slider_label)
        left_layout.addWidget(self.buffer_slider)
        left_layout.addStretch()

        # Main horizontal layout: button on the left, plot on the right
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout)          # Buttons and slider on the left
        main_layout.addWidget(self.plot_widget)     # Plot on the right
        self.setLayout(main_layout)

        # Timer for reading and plotting
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_and_plot)
        self.timer.start(20)  # 50 Hz polling

    def read_and_plot(self):
        if self.is_paused:
            return

        # Read incoming UART data
        while self.serial.in_waiting:
            try:
                line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    value = float(line)
                    self.buffer.append(value)
            except ValueError:
                continue  # Skip malformed data

        # When buffer is full, plot and clear
        if len(self.buffer) >= self.buffer_len:
            self.plot_curve.setData(list(self.buffer))
            self.buffer.clear()

    def toggle_pause(self, checked):
        if checked:
            self.is_paused = True
            self.pause_button.setText("Replay")
        else:
            self.is_paused = False
            self.buffer.clear()
            self.pause_button.setText("Pause")

    def change_buffer_length(self, value):
        # Round to nearest multiple of 32 just in case
        value = int(value / 32) * 32
        self.buffer_len = value
        self.slider_label.setText(f"Buffer: {value}")
        
        # Clear and resize the buffer
        self.buffer = deque(maxlen=value)
        self.plot_widget.setXRange(0, value - 1, padding=0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    plotter = BatchSerialPlotter()
    window.setCentralWidget(plotter)
    window.setWindowTitle("Batch UART Plot with Pause/Replay")
    window.resize(900, 400)
    window.show()
    sys.exit(app.exec())
