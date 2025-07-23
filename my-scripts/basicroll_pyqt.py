'''
File: roll_pyqt.py
Author: Surya Turaga
Date: 23 July 2025

Roll mode of the oscilloscope using PyQt6 and pyqtgraph.
It reads data from a UART serial port and displays it in real-time.
'''

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QHBoxLayout
from collections import deque
import pyqtgraph as pg
import serial
from PySide6.QtCore import QTimer

class SerialPlotter(QWidget):
    def __init__(self, port='COM8', baud=115200, buffer_len=128):
        super().__init__()

        self.buffer = deque([0]*buffer_len, maxlen=buffer_len)
        self.serial = serial.Serial(port, baud, timeout=0.05)

        self.plot_widget = pg.PlotWidget(title="UART Live Buffer Plot")
        self.plot_curve = self.plot_widget.plot(list(self.buffer), pen=pg.mkPen('g', width=2))
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setYRange(-0.1, 3.5, padding=0)
        self.plot_widget.setXRange(0, buffer_len - 1, padding=0)
        self.plot_widget.setLabel('left', 'Voltage [V]')
        self.plot_widget.setLabel('bottom', 'Sample Number')

        # Pause button
        self.pause_button = QPushButton("Pause")
        self.pause_button.setCheckable(True)
        self.pause_button.toggled.connect(self.toggle_pause)

        # Layout: button + plot horizontally
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.pause_button)
        hlayout.addWidget(self.plot_widget)

        self.setLayout(hlayout)

        self.is_paused = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(40)  # update every 40 ms

    def update_plot(self):
        if self.is_paused:
            return

        while self.serial.in_waiting:
            try:
                line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    value = float(line)
                    self.buffer.append(value)
            except ValueError:
                continue
        self.plot_curve.setData(list(self.buffer))

    def toggle_pause(self, checked):
        if checked:
            self.is_paused = True
            self.pause_button.setText("Replay")
        else:
            self.is_paused = False
            self.buffer.clear()
            self.buffer.extend([0]*self.buffer.maxlen)
            self.pause_button.setText("Pause")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = QMainWindow()
    plotter = SerialPlotter(port='COM8', baud=115200, buffer_len=128)
    main_window.setCentralWidget(plotter)
    main_window.setWindowTitle("STM32 UART Real-Time Live Plot")
    main_window.resize(900, 400)
    main_window.show()
    sys.exit(app.exec())
