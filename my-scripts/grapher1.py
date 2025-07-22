import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque

# Configure serial port
ser = serial.Serial('COM8', 115200, timeout=1)

BUFFER_SIZE = 100
data = deque([0]*BUFFER_SIZE, maxlen=BUFFER_SIZE)

fig, ax = plt.subplots()
line, = ax.plot(range(BUFFER_SIZE), data)
ax.set_title("Live UART Data")
ax.set_ylabel("Value")
ax.set_xlabel("Sample")
ax.set_xlim(0, BUFFER_SIZE-1)
ax.set_ylim(-1, 1)  # Adjust as needed for your data range

def init():
    line.set_ydata([0]*BUFFER_SIZE)
    return line,

def read_serial():
    line_data = ser.readline().decode('utf-8').strip()
    try:
        value = float(line_data)
        return value
    except ValueError:
        return None

def update(frame):
    value = read_serial()
    if value is not None:
        data.append(value)
        line.set_ydata(data)
    return line,

ani = FuncAnimation(
    fig, update, init_func=init, interval=1, blit=True:w
    
)
plt.show()

ser.close()

'''import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Configure serial port
ser = serial.Serial('COM8', 115200, timeout=1)

data = []

# Function to read serial data and process values
def read_serial():
    line = ser.readline().decode('utf-8').strip()
    try:
        value = float(line)
        return value
    except ValueError:
        return None

# Function to use by plt to update the frame with new data
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
ani = FuncAnimation(fig, update, interval=1)
plt.show()

ser.close()
'''