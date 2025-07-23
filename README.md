# oscilloscope_v1

The only LCD display I have is a tiny one attached to my FPGA, and it's hard to program to interface with my microcontroller. It's also not very practical to go through tons of pixels and what not through verilog just to show some graphs.

Printing data through UART back to the laptop only gets you so far. Using python scripts to process this data, however, can open up lots of new doors in projects. This project is my experimentation on using scripting to graph ADC data from my STM32F767, making a rudimentary oscilloscope of sorts.

The goal is to add a good amount of functionality to the microcontroller as well as the python scripts. The data should be entirely processed in the STM32 so it can function as an independant unit.

There are a lot of applications for this sort of project. If it's sophisticated enough, this one alone can carry out quite a few tasks that would make debugging a lot easier in future projects. For example, data can be logged over time or viewed as typical oscilloscope data on screen. Even DSP algorithms used by the microcontroller can be checked more easily, such as FFT.

## About the project
This project uses the DAC and ADCs of the controller, synchronized by a timer to send and receive signals through DMA.

There are three modes of operation in this rudimentary oscilloscope; roll, normal, and single. These are the main time based functions used on a standard desktop oscilloscope. Some non-time based functions are FRAs and FFTs.

Roll mode collects data at a slow rate, plotting it as a graph over time. Normal mode uses a selected trigger voltage level to collect a fixed number of samples and display them. Single waits for a trigger and immediately captures a single screenshot.

I have used AI to help me work on this project. I used it for troubleshooting and understanding the use of pyqtgraph. I pretty much stuck to Perplexity for the most part, it helps with compiling all information regarding STM32 documentation and python libraries and what not.