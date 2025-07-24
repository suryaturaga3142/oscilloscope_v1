import sys
from collections import deque
import serial
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QPushButton, QSlider, QCheckBox
)
from PySide6.QtCore import QTimer, Qt
import pyqtgraph as pg

# Class for roll mode plotter
class UARTMultiChannelPlotter(QWidget):
    # Initialize the UARTMultiChannelPlotter
    def __init__(self, port="COM8", baud=115200):
        super().__init__()

        self.serial = serial.Serial(port, baud, timeout=0.05)
        self.buffer_len = 1024
        self.buffer_len_min = 32
        self.buffer_len_max = 2048
        self.buffer_len_step = 32

        self.trigger_threshold = 2048  # Not used directly here but can be extended

        # Buffers for timestamp and 3 values
        self.buffer_timestamps = deque(maxlen=self.buffer_len)
        self.buffer_values1 = deque(maxlen=self.buffer_len)
        self.buffer_values2 = deque(maxlen=self.buffer_len)
        self.buffer_values3 = deque(maxlen=self.buffer_len)

        self.is_running = False  # True when plotting, false when frozen

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial_and_update)
        self.timer.start(10)

    # Initialize the UI components
    def init_ui(self):
        self.plot_widget = pg.PlotWidget(title="Roll Mode: ADC Values vs Time")
        self.curve1 = self.plot_widget.plot(pen=pg.mkPen('r', width=2), name='Value 1')
        self.curve2 = self.plot_widget.plot(pen=pg.mkPen('g', width=2), name='Value 2')
        self.curve3 = self.plot_widget.plot(pen=pg.mkPen('b', width=2), name='Value 3')
        self.plot_widget.setYRange(0, 4095, padding=0)

        # Start/Stop button
        self.start_stop_button = QPushButton("Start")
        self.start_stop_button.setCheckable(True)
        self.start_stop_button.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        self.start_stop_button.toggled.connect(self.toggle_start_stop)

        # Buffer length slider + label
        self.buffer_slider_label = QLabel(f"Buffer length: {self.buffer_len}")
        self.buffer_slider = QSlider(Qt.Vertical)
        self.buffer_slider.setMinimum(self.buffer_len_min)
        self.buffer_slider.setMaximum(self.buffer_len_max)
        self.buffer_slider.setSingleStep(self.buffer_len_step)
        self.buffer_slider.setPageStep(self.buffer_len_step)
        self.buffer_slider.setValue(self.buffer_len)
        self.buffer_slider.valueChanged.connect(self.change_buffer_length)

        # Checkboxes to toggle curves
        self.chk_val1 = QCheckBox("Value 1")
        self.chk_val2 = QCheckBox("Value 2")
        self.chk_val3 = QCheckBox("Value 3")
        self.chk_val1.setChecked(True)
        self.chk_val2.setChecked(True)
        self.chk_val3.setChecked(True)

        # Left layout: Start/Stop + buffer slider + checkboxes
        left_layout = QVBoxLayout()
        top_row = QHBoxLayout()
        top_row.addWidget(self.start_stop_button)
        top_row.addStretch()
        left_layout.addLayout(top_row)
        left_layout.addWidget(self.buffer_slider_label)
        left_layout.addWidget(self.buffer_slider)
        left_layout.addWidget(self.chk_val1)
        left_layout.addWidget(self.chk_val2)
        left_layout.addWidget(self.chk_val3)
        left_layout.addStretch()

        # Main layout horizontal: left controls + plot on right
        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout)
        main_layout.addWidget(self.plot_widget, stretch=1)

        self.setLayout(main_layout)

    # Change the buffer length
    def change_buffer_length(self, value):
        value = (value // self.buffer_len_step) * self.buffer_len_step
        self.buffer_len = value
        self.buffer_slider_label.setText(f"Buffer length: {value}")

        keep_len = min(len(self.buffer_values1), value)
        new_timestamps = deque(list(self.buffer_timestamps)[-keep_len:], maxlen=value)
        new_values1 = deque(list(self.buffer_values1)[-keep_len:], maxlen=value)
        new_values2 = deque(list(self.buffer_values2)[-keep_len:], maxlen=value)
        new_values3 = deque(list(self.buffer_values3)[-keep_len:], maxlen=value)
        self.buffer_timestamps = new_timestamps
        self.buffer_values1 = new_values1
        self.buffer_values2 = new_values2
        self.buffer_values3 = new_values3

        if self.buffer_timestamps:
            self.plot_widget.setXRange(min(self.buffer_timestamps),
                                        max(self.buffer_timestamps),
                                        padding=0.05)
        else:
            self.plot_widget.setXRange(0, 1, padding=0.05)

    # Toggle start/stop button
    def toggle_start_stop(self, checked):
        if checked:
            # Start pressed
            self.is_running = True
            self.start_stop_button.setText("Stop")
            self.start_stop_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
            self.clear_buffers()
            self.plot_widget.clear()
            # recreate curves to assign to plot
            self.curve1 = self.plot_widget.plot(pen=pg.mkPen('r', width=2), name='Value 1')
            self.curve2 = self.plot_widget.plot(pen=pg.mkPen('g', width=2), name='Value 2')
            self.curve3 = self.plot_widget.plot(pen=pg.mkPen('b', width=2), name='Value 3')
        else:
            # Stop pressed
            self.is_running = False
            self.start_stop_button.setText("Start")
            self.start_stop_button.setStyleSheet("background-color: green; color: white; font-weight: bold;")
            # Keep buffers collecting, but plot frozen (no plotting updates)

    # Clear all buffers
    def clear_buffers(self):
        self.buffer_timestamps.clear()
        self.buffer_values1.clear()
        self.buffer_values2.clear()
        self.buffer_values3.clear()

    # Read serial data and update buffers
    def read_serial_and_update(self):
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
                    v1 = float(parts[1])
                    v2 = float(parts[2])
                    v3 = float(parts[3])
                except ValueError:
                    continue

                self.buffer_timestamps.append(timestamp)
                self.buffer_values1.append(v1)
                self.buffer_values2.append(v2)
                self.buffer_values3.append(v3)

            if self.is_running and self.buffer_timestamps:
                self.update_plot()

        except serial.SerialException:
            pass

    # Update the plot with the current buffer data
    def update_plot(self):
        x = list(self.buffer_timestamps)
        if self.chk_val1.isChecked():
            self.curve1.setData(x, list(self.buffer_values1))
        else:
            self.curve1.clear()
        if self.chk_val2.isChecked():
            self.curve2.setData(x, list(self.buffer_values2))
        else:
            self.curve2.clear()
        if self.chk_val3.isChecked():
            self.curve3.setData(x, list(self.buffer_values3))
        else:
            self.curve3.clear()

        self.plot_widget.setYRange(0, 4095, padding=0)
        if x:
            self.plot_widget.setXRange(min(x), max(x), padding=0.05)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    plotter = UARTMultiChannelPlotter()
    window.setCentralWidget(plotter)
    window.setWindowTitle("UART Multi-Channel Plotter")
    window.resize(1200, 600)
    window.show()
    sys.exit(app.exec())
