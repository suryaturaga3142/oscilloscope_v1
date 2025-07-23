'''
File: logger_plt.py
Author: Surya Turaga
Date: 22 July 2025

A more robust script to plot data from a UART serial port as oscilloscope data with a given trigger.
Capable of handling higher frequencies due to larger buffer size.
'''

import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

MAX_BUFFER_SIZE = 128  # Maximum buffer size for plotting

# Initialize serial port
ser = serial.Serial('COM8', 115200, timeout=1)

buffer = []

def read_serial_value():
    """
    Read one line from serial, decode, convert to float.
    Returns float value or None if invalid.
    """
    try:
        line = ser.readline().decode('utf-8').strip()
        return float(line)
    except (UnicodeDecodeError, ValueError):
        return None

def update(frame):
    global buffer

    # Keep reading values until buffer is filled
    while len(buffer) < MAX_BUFFER_SIZE:
        value = read_serial_value()
        if value is not None:
            buffer.append(value)
        else:
            # No valid data, break to allow animation to update plot
            break

    if len(buffer) == MAX_BUFFER_SIZE:
        ax.clear()
        ax.plot(buffer)
        ax.set_title("Oscilloscope Normal Mode")
        ax.set_xlabel("Sample Number")
        ax.set_ylabel("Voltage [V]")
        ax.set_ylim(-0.1, 3.5)  # Assuming a 3.3V system
        ax.grid(True)

        # Clear buffer after plotting for next batch
        buffer = []


if __name__ == "__main__":
    fig, ax = plt.subplots()
    ani = FuncAnimation(fig, update, interval=1)
    plt.show()
    ser.close()