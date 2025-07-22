import serial
import pyqtgraph as pg
from PySide6.QtWidgets import QApplication  # Use PyQt5 or your installed binding
from pyqtgraph.Qt import QtCore
from collections import deque

# Configure serial port
ser = serial.Serial('COM8', 115200, timeout=1)

BUFFER_SIZE = 100
data = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)

app = QApplication([])
win = pg.GraphicsLayoutWidget(title="Live UART Data")
plot = win.addPlot(title="Live UART Data")
curve = plot.plot(list(data), pen='y')
plot.setLabel('left', 'Value')
plot.setLabel('bottom', 'Sample')
plot.setYRange(0, 4096)  # Adjust as needed

def update():
    line_data = ser.readline().decode('utf-8').strip()
    try:
        value = float(line_data)
        data.append(value)
        curve.setData(list(data))
    except ValueError:
        pass

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(1)  # Update every 1 ms

win.show()
app.exec_()
ser.close()