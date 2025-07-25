import sys
from collections import deque
import serial
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QSlider, QLabel
)
from PySide6.QtCore import QTimer, Qt
import pyqtgraph as pg

class UARTBufferTriggerPlotter(QWidget):
    def __init__(self, port="COM8", baud=115200):
        super().__init__()
        self.serial = serial.Serial(port, baud, timeout=0.05)
        self.buffer_len = 512
        self.trigger_value = 2048  # Default trigger value
        self.is_running = False   # Start/Stop determines plotting/freeze

        # Buffers: timestamp and value
        self.buffer_timestamps = deque(maxlen=self.buffer_len)
        self.buffer_values = deque(maxlen=self.buffer_len)

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial_and_handle_trigger)
        self.timer.start(10)

    def init_ui(self):
        # Plot setup
        self.plot_widget = pg.PlotWidget(title="Plotter Ch1: ADC Values vs Time")
        self.curve = self.plot_widget.plot(pen=pg.mkPen('g', width=2), name='Value')
        self.plot_widget.setYRange(0, 4095, padding=0)
        self.plot_widget.showGrid(x=True, y=True)

        # Start/Stop Button
        self.toggle_button = QPushButton("Start")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setStyleSheet("background-color: green; color: white; font-weight: bold; font-size: 14px;")
        self.toggle_button.toggled.connect(self.toggle_start_stop)

        # Buffer length slider + label
        self.buffer_slider_label = QLabel(f"Buffer length: {self.buffer_len}")
        self.buffer_slider = QSlider(Qt.Vertical)
        self.buffer_slider.setMinimum(32)
        self.buffer_slider.setMaximum(2048)
        self.buffer_slider.setSingleStep(32)
        self.buffer_slider.setPageStep(32)
        self.buffer_slider.setValue(self.buffer_len)
        self.buffer_slider.valueChanged.connect(self.change_buffer_length)

        # Trigger value slider + label
        self.trigger_slider_label = QLabel(f"Trigger: {self.trigger_value}")
        self.trigger_slider = QSlider(Qt.Vertical)
        self.trigger_slider.setMinimum(0)
        self.trigger_slider.setMaximum(4095)
        self.trigger_slider.setSingleStep(1)
        self.trigger_slider.setValue(self.trigger_value)
        self.trigger_slider.valueChanged.connect(self.change_trigger_value)

        # Left column: Start/Stop, sliders and labels
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.toggle_button)
        left_layout.addWidget(self.buffer_slider_label)
        left_layout.addWidget(self.buffer_slider)
        left_layout.addWidget(self.trigger_slider_label)
        left_layout.addWidget(self.trigger_slider)
        left_layout.addStretch()

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addWidget(self.plot_widget, stretch=1)
        self.setLayout(main_layout)

    def change_buffer_length(self, value):
        value = (value // 32) * 32
        self.buffer_len = value
        self.buffer_slider_label.setText(f"Buffer length: {value}")
        self.buffer_timestamps = deque(maxlen=self.buffer_len)
        self.buffer_values = deque(maxlen=self.buffer_len)
        self.curve.clear()
        self.plot_widget.setXRange(0, 1, padding=0.05)

    def change_trigger_value(self, value):
        self.trigger_value = value
        self.trigger_slider_label.setText(f"Trigger: {value}")

    def toggle_start_stop(self, checked):
        if checked:
            self.is_running = True
            self.toggle_button.setText("Stop")
            self.toggle_button.setStyleSheet("background-color: red; color: white; font-weight: bold; font-size: 14px;")
            self.clear_buffers()
            self.curve.clear()
            self.plot_widget.setXRange(0, 1, padding=0.05)
        else:
            self.is_running = False
            self.toggle_button.setText("Start")
            self.toggle_button.setStyleSheet("background-color: green; color: white; font-weight: bold; font-size: 14px;")
            # Freeze graph, keep collecting in buffers

    def clear_buffers(self):
        self.buffer_timestamps.clear()
        self.buffer_values.clear()

    def read_serial_and_handle_trigger(self):
        # Collect UART data, always appending to buffers
        try:
            while self.serial.in_waiting:
                line = self.serial.readline().decode(errors="ignore").strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) < 4:
                    continue
                try:
                    timestamp = float(parts[0])
                    value = float(parts[1])
                except ValueError:
                    continue
                self.buffer_timestamps.append(timestamp)
                self.buffer_values.append(value)

            # Trigger check operates only in Start (running) state, and only when buffer is full
            if self.is_running and len(self.buffer_values) == self.buffer_len:
                first_value = self.buffer_values[0]
                if int(first_value) >= self.trigger_value - 100 and int(first_value) <= self.trigger_value + 100:
                    x = list(self.buffer_timestamps)
                    y = list(self.buffer_values)
                    self.curve.setData(x, y)
                    if x:
                        self.plot_widget.setXRange(min(x), max(x), padding=0.05)
                    # After trigger event: clear buffers, freeze graph until next event
                    self.clear_buffers()

        except serial.SerialException:
            pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    plotter = UARTBufferTriggerPlotter()
    window.setCentralWidget(plotter)
    window.setWindowTitle("UART Trigger Plotter")
    window.resize(1100, 600)
    window.show()
    sys.exit(app.exec())
