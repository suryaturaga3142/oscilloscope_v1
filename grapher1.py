import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Configure serial port
ser = serial.Serial('COM8', 115200, timeout=1)

data = []

def read_serial():
    line = ser.readline().decode('utf-8').strip()
    try:
        value = float(line)
        return value
    except ValueError:
        return None

def update(frame):
    value = read_serial()
    if value is not None:
        data.append(value)
        if len(data) > 100:
            data.pop(0)
        ax.clear()
        ax.plot(data)
        ax.set_title("Live UART Data")
        ax.set_ylabel("Value")
        ax.set_xlabel("Sample")

fig, ax = plt.subplots()
ani = FuncAnimation(fig, update, interval=100)
plt.show()

ser.close()
