# USB Water Metering 
Python-based codes that read audio from the WaWiCo USB adapter to determine whether water is flowing through a household pipe

#
### - Getting Started -
The set of Python codes presented in this repository require 'pyaudio' as a library, which can be quite an involved install depending on the system (Mac, Linux, Windows). To install pyaudio, follow the procedures outlined below for your OS:

###### Raspberry Pi (Linux)
In the terminal install the following:
    sudo apt-get install libportaudio0
#
### - Real-Time Frequency Visualization -
The following script runs a real-time visualization to help identify the frequency response of the MEMS microphone placed in proximity to the piping system:
> realtime_freq.py

#
### - Water Flow Detection -
The following code is meant to identify water flow based on the frequencies produced during flow through the piping: 
> water_metering.py

The signal amplitude coming from the microphone and the frequency bands are the
2 variable to which the paramter need to be adapted.  Especially the amplitude
differes in a wide range so an all PEX pipe system may create a very weak signal
or even requires amplification before it can be used while an old galvanvized
steel pipe system may be  very loud.

Checks (now) 2 changeable frequency bands for  signals from Water-Flow and
writes them (now) to 2 files  "WF_ALL_REC.dat" and "WF_RECORDS.dat" as well as
to the screen. The Fu that creates Flow Periods will be finnish soon.

It now reads from a MEMS/USB Soundcard combo and the most important settings
are the amplification of the soundcard (on a Mac no problem) and factor1 and 2
to get reasonable Magnitude values.

The idea is to have the most processing intense parts (the goertzel DFT) as
part of the main program and not as a function call.
All vars needed  and declared  on this level would be global but at at the same
time local = access to all vars will be fast.
Frequncy resolution fR = Sample frequenze / sample size  fR = sf/sz
1. sf = fixed to 44.100
   selectable are sz and fR
   e.g: wanted: an fR of 3 Hz   ---> sf/fR= sz  44100/3 = 14700

2. The smaller the sample size and the frequency band to look at,  the faster the module

3. The smaller we can define the frequency band to look at,  the higher we can
   choose fR   and still get superfast runtime.

With the Arduino module we will be much more flexible because it eliminates the
fixed sample frequency of 44.100 of the USB Audio card.  Furthermore the Arduino
eliminates all possible trouble with ALSA, Portaudio and pyaudio working together.

Beside printing to the screen the Module creates 3 files and then appends to
these files each time the program is restarted.


1. WF_ALL_REC.dat
Contains events Water-Flow or Not, easy to use for further statistics/graphics
This could also be used as a 100%  documentation of all events on the water-pipe
system. Can be drastically reduced in size in many different ways.

DOC TimeStamp FB1 Mag FB2 Mag  (#)
P01 1611346669     0       0  (15)
P01 1611346672     0       2  (21)
P01 1611346675     0       0  (21)
P01 1611346678     0       0  (21)
P01 1611346681     0       0  (21)
P01 1611346684     3       2  (21)
P01 1611346687     1       1  (21)
.....

2. WF_RECORDSS.dat
Contains All Water-Flow events, easy to use for further statistics/graphics
DOC TimeStamp FB1 Mag FB2 Mag  (#)
P01 1611415422   294    3115  (23)
P01 1611415425   307    1980  (20)
P01 1611415428   871    1324  (21)
P01 1611415431   109    1948  (20)
P01 1611415434   114    1504  (19)
P01 1611415437   218    1922  (21)
.....
(1) and 2) The writing to this 2 files can be stopped without consequences to any
other part of the program).

3. WF_FP.dat
Contains  Water-Flow Periods; This file has human readable data and
can be easily read and edited with any Editor.
from        till     duration gallon gpm  water-user
18:24:47 - 18:24:53     6 sec NYD
19:02:13 - 19:02:35    22 sec NYD
20:30:34 - 20:30:59    25 sec NYD

Sat Jan 23 00:00:00 2021
07:21:03 - 07:24:03   3.0 min NYD
07:28:15 - 07:29:00    45 sec NYD
11:48:15 - 11:49:55  1.67 min NYD
12:09:27 - 12:10:52  1.42 min NYD
12:13:34 - 12:13:43     9 sec NYD
.....
"""
