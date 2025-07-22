import sys
import serial
from PySide6 import QtWidgets, QtCore
import pyqtgraph as pg

class UARTPlotter(QtWidgets.QMainWindow):
    def __init__(self, port='COM8', baudrate=115200, max_points=200):
        super().__init__()
        self.setWindowTitle("Live UART Data Plot")

        # Open serial port
        try:
            self.ser = serial.Serial(port, baudrate, timeout=0.01)
        except serial.SerialException as e:
            QtWidgets.QMessageBox.critical(self, "Serial Port Error", str(e))
            sys.exit(1)

        self.data = []  # store recent samples
        self.max_points = max_points

        # Setup pyqtgraph PlotWidget
        self.plot_widget = pg.PlotWidget()
        self.setCentralWidget(self.plot_widget)
        self.plot_widget.setBackground('w')
        self.plot_widget.setTitle("UART Real-Time Data", color='black', size='14pt')
        styles = {'color': 'black', 'font-size': '12pt'}
        self.plot_widget.setLabel('left', 'Value', **styles)
        self.plot_widget.setLabel('bottom', 'Sample', **styles)
        self.plot_widget.showGrid(x=True, y=True)

        pen = pg.mkPen(color=(255, 0, 0), width=2)
        # Create the plot curve once
        self.curve = self.plot_widget.plot(pen=pen)

        # Timer for periodic plotting ~100Hz
        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)  # 10ms = 100Hz
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

    def read_uart_line(self):
        """Read one line from UART, decode and convert to float if possible."""
        try:
            line = self.ser.readline().decode('utf-8').strip()
            if line:
                return float(line)
        except (ValueError, UnicodeDecodeError):
            return None

    def update_plot(self):
        val = self.read_uart_line()
        if val is not None:
            self.data.append(val)
            if len(self.data) > self.max_points:
                self.data.pop(0)
            # Efficiently update curve data without clearing the plot
            self.curve.setData(self.data)
        else:
            # No data; optionally skip updating to reduce flicker
            pass

    def closeEvent(self, event):
        if self.ser.is_open:
            self.ser.close()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = UARTPlotter(port='COM8', baudrate=115200, max_points=200)
    win.resize(800, 500)
    win.show()
    sys.exit(app.exec())