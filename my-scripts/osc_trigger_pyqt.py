import sys
from collections import deque
import serial
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QHBoxLayout, QPushButton, QSlider
)
from PySide6.QtCore import QTimer, Qt
import pyqtgraph as pg


class UARTTriggerPlotter(QWidget):
    def __init__(self, port="COM8", baud=115200):
        super().__init__()

        self.serial = serial.Serial(port, baud, timeout=0.05)
        self.buffer_len = 1024
        self.trigger_threshold = 2048

        self.buffer_timestamps = deque(maxlen=self.buffer_len)
        self.buffer_values = deque(maxlen=self.buffer_len)

        self.is_armed = False
        self.show_live = False  # Controls if plot is live-updating

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.read_and_update)
        self.timer.start(30)

    def init_ui(self):
        self.plot_widget = pg.PlotWidget(title="UART Value vs Timestamp")
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen('g', width=2))
        self.plot_widget.setYRange(0, 4095, padding=0)

        self.indicator_label = QLabel("ready")
        self.indicator_label.setAlignment(Qt.AlignCenter)
        self.indicator_label.setStyleSheet("font-weight: bold; font-size: 16px;")

        self.buffer_slider_label = QLabel(f"Buffer length: {self.buffer_len}")
        self.buffer_slider = QSlider(Qt.Vertical)
        self.buffer_slider.setMinimum(32)
        self.buffer_slider.setMaximum(2048)
        self.buffer_slider.setSingleStep(32)
        self.buffer_slider.setPageStep(32)
        self.buffer_slider.setValue(self.buffer_len)
        self.buffer_slider.valueChanged.connect(self.change_buffer_length)

        self.trigger_slider_label = QLabel(f"Trigger threshold: {self.trigger_threshold}")
        self.trigger_slider = QSlider(Qt.Vertical)
        self.trigger_slider.setMinimum(0)
        self.trigger_slider.setMaximum(4095)
        self.trigger_slider.setSingleStep(1)
        self.trigger_slider.setValue(self.trigger_threshold)
        self.trigger_slider.valueChanged.connect(self.change_trigger_threshold)

        self.arm_button = QPushButton("Arm")
        self.arm_button.setCheckable(True)
        self.arm_button.toggled.connect(self.toggle_arm_disarm)

        sliders_layout = QHBoxLayout()
        sliders_left_layout = QVBoxLayout()
        sliders_left_layout.addWidget(self.arm_button)
        sliders_left_layout.addWidget(self.buffer_slider_label)
        sliders_left_layout.addWidget(self.buffer_slider)
        sliders_left_layout.addStretch()
        sliders_right_layout = QVBoxLayout()
        sliders_right_layout.addWidget(self.trigger_slider_label)
        sliders_right_layout.addWidget(self.trigger_slider)
        sliders_right_layout.addStretch()

        sliders_layout.addLayout(sliders_left_layout)
        sliders_layout.addLayout(sliders_right_layout)
        sliders_layout.addWidget(self.plot_widget)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.indicator_label)
        main_layout.addLayout(sliders_layout)

        self.setLayout(main_layout)

    def change_buffer_length(self, value):
        value = (value // 32) * 32
        self.buffer_len = value
        self.buffer_slider_label.setText(f"Buffer length: {value}")

        keep_len = min(len(self.buffer_values), value)
        new_timestamps = deque(list(self.buffer_timestamps)[-keep_len:], maxlen=value)
        new_values = deque(list(self.buffer_values)[-keep_len:], maxlen=value)
        self.buffer_timestamps = new_timestamps
        self.buffer_values = new_values

        if self.buffer_timestamps:
            self.plot_widget.setXRange(min(self.buffer_timestamps),
                                      max(self.buffer_timestamps),
                                      padding=0.05)
        else:
            self.plot_widget.setXRange(0, 1, padding=0.05)

    def change_trigger_threshold(self, value):
        self.trigger_threshold = value
        self.trigger_slider_label.setText(f"Trigger threshold: {value}")

    def toggle_arm_disarm(self, checked):
        if checked:
            self.is_armed = True
            self.show_live = True
            self.arm_button.setText("Disarm")
            self.indicator_label.setText("waiting")
            self.clear_buffer()
            self.plot_curve.clear()
        else:
            self.is_armed = False
            self.show_live = False
            self.arm_button.setText("Arm")
            self.indicator_label.setText("ready")
            # Buffer is NOT cleared, new UART data keeps being collected, but plot does not update

    def clear_buffer(self):
        self.buffer_timestamps.clear()
        self.buffer_values.clear()

    def read_and_update(self):
        try:
            while self.serial.in_waiting:
                line = self.serial.readline().decode("utf-8", errors="ignore").strip()
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

                # "Trigger" check only when armed and buffer full
                if self.is_armed and len(self.buffer_values) == self.buffer_len:
                    mid_index = self.buffer_len // 2
                    middle_value = self.buffer_values[mid_index]
                    if middle_value > self.trigger_threshold:
                        self.is_armed = False
                        self.show_live = False
                        self.arm_button.setChecked(False)
                        self.arm_button.setText("Arm")
                        self.indicator_label.setText("triggered")
                        self.plot_full_buffer()
                        break

            # Always update live plot only when show_live is set
            if self.show_live and self.buffer_values and self.buffer_timestamps:
                self.plot_live()
        except serial.SerialException:
            pass

    def plot_live(self):
        x_data = list(self.buffer_timestamps)
        y_data = list(self.buffer_values)
        self.plot_curve.setData(x_data, y_data)
        if x_data:
            self.plot_widget.setXRange(min(x_data), max(x_data), padding=0.05)

    def plot_full_buffer(self):
        x_data = list(self.buffer_timestamps)
        y_data = list(self.buffer_values)
        self.plot_curve.setData(x_data, y_data)
        if x_data:
            self.plot_widget.setXRange(min(x_data), max(x_data), padding=0.05)


def main():
    app = QApplication(sys.argv)
    window = QMainWindow()
    plotter = UARTTriggerPlotter()
    window.setCentralWidget(plotter)
    window.setWindowTitle("UART Trigger Plotter")
    window.resize(1100, 600)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
