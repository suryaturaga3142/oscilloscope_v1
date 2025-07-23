'''
File: roll_plt.py
Author: Surya Turaga
Date: 22 July 2025

A simple script to read data from a UART serial port and log it in real-time using matplotlib.
It works best for frequency ranges of 100mHz to 50Hz.
'''

import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Configure serial port
ser = serial.Serial('COM8', 115200, timeout=10)

data = []

# Function to read data from the serial port
def read_serial():
    line = ser.readline().decode('utf-8').strip()
    try:
        value = float(line)
        return value
    except ValueError:
        return None

# Function to update the plot
def update(frame):
    value = read_serial()
    if value is not None:
        data.append(value)
        if len(data) > 100:
            data.pop(0)
        ax.clear()
        ax.plot(data)
        ax.set_title("Log Mode Oscilloscope")
        ax.set_ylabel("Voltage [V]")
        ax.set_xlabel("Sample Number")
        ax.set_ylim(-0.1, 3.5)  # Assuming a 3.3V system
        ax.grid(True)

if __name__ == "__main__":
    #plt.style.use('seaborn-darkgrid')
    fig, ax = plt.subplots()
    ani = FuncAnimation(fig, update, interval=1)
    plt.show()
    ser.close()