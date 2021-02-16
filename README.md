# USB Water Metering 
Python-based codes that read audio from the WaWiCo USB adapter to determine whether water is flowing through a household pipe

### JUMP TO:
<a href="#start">- Operating System Installs</a><br>
<a href="#realtime">- Real-Time Frequency Visualization</a><br>
<a href="#flow">- Water Flow Detection</a><br>
<a href="#event">- Event Detection and Documentation</a><br>

The USB Water Metering library can be downloaded using git:

    git clone https://github.com/wawico/usb-water-metering
    
Keep in mind — the libraries and installs to follow are still required for utilizing the library.

<a id="start"></a>
# - Operating System Installs -
The set of Python codes presented in this repository require 'pyaudio' as a library, which can be quite an involved install depending on the system (Mac, Linux, Windows). To install pyaudio, follow the procedures outlined below for your OS:

##### Raspberry Pi (Linux)
In the terminal, input the following:

    sudo apt-get install libportaudio0 libportaudio2 libportaudiocpp0 portaudio19-dev
    sudo pip3 install pyaudio

##### Ubuntu
Again in the terminal, input the following:

    sudo apt-get install libasound-dev portaudio19-dev libportaudio2 libportaudiocpp0
    sudo pip3 install pyaudio
    
##### Mac OS
For Mac, XCode first needs to be downloaded from the App Store. Then, brew needs to be installed:

    ruby -e "$(curl -fsSl https://raw.githubusercontent.com/Homebrew/install/master/install)"
    
Finally, the pyaudio installs:

    brew install portaudio
    pip3 install pyaudio
    
##### Windows 10
For Windows, things get a bit more complicated with pyaudio. Download Microsoft C++ Build Tools and run the .exe (if they are not already on the system):
- https://visualstudio.microsoft.com/visual-cpp-build-tools/

In the install window, make sure ‘C++ build tools’ is checked before clicking ‘Install’ - this is quite a large install (~6.5GB), but is the simplest method.

Once the install completes, download the pyaudio wheel from the following site for the respective Python 3.x version:

- https://www.lfd.uci.edu/~gohlke/pythonlibs/

Once the .whl file is downloaded to the Downloads folder, navigate to that folder in a terminal and type the following:

    python3 -m pip install PyAudio-0.2.11-cp38-cp38-win_amd64.whl

NOTE: the file above (PyAudio-0.2.11-cp38-cp38-win_amd64.whl) should be substituted for your Python version (cp38 = Python3.8) and OS version (win_amd64 = Windows 64-bit).

<a id="realtime"></a>

# - Real-Time Frequency Visualization -
The following script runs a real-time visualization to help identify the frequency response of the MEMS microphone placed in proximity to the piping system:
> realtime_freq.py

Example output plot from the real-time frequency analysis:

![real-time freq plot](/images/realtime_freq_plot.png)

<a id="flow"></a>

# - Spectrogram Visualization -
A spectrogram is a time vs. frequency plot that allows users to see the frequency variability of the microphone response over time. The following script plots a real-time spectrogram:
> realtime_spectrogram.py

An example spectrogram is shown below for reference:

![real-time spectrogram sample](/images/usb_wawico_spectrogram.png)

Notice the large jump in values - this is the point where the faucet was turned on, resulting in the jump in frequency response in the 5kHz - 8kHz region.

# - Water Flow Detection -
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

Below is an example output from the flow_detection.py script:

![flow detection output](/images/wawico_flow_detection_output.png)

<a id="event"></a>
# - Event Detection and Documentation -
The following code is meant to monitor water flow based on the frequencies determined above during flow periods and save them to a local file: 
> event_detection.py

Should work on any computer with a  Win 10, Mac OS 10.x or Linux OS
Python 3.x  and the libraries pyaudio and numpy
For testing it also works with a  build in microphone.
For getting real data it needs the USB soundcard/Microphone combination

Start: Python WFD3.py    Runs for ever End: "CTRL C".
"Ctrl Z" ends Python and may result in loss of some data not yet stored in file
The program creates following 3 files that can be opened/look at with any editor.
"WWC_ALL.dat"  contains all recoed Water-Flow or  not
ID TS          avg FB1    FB2  max FB1    FB2
P3 1612734296       0       1       2       3
P3 1612734297       2       4       9       9
P3 1612734298    2170    3356    6165   12507
P3 1612734299    2526    3168    4242    6465

"WWC_WF.dat" contains only Water-Flow   Records
Structure 100% identical with WWC_ALL.dat
P3 1612734298    2170    3356    6165   12507
P3 1612734299    2526    3168    4242    6465
Both WWC_ALL.dat and WWC_WF.dat are planned as basis for an unlimited amount
of further analysyis and statistics/graphics etc.  WWC_ALL.dat can alo be used
for a gapless documentation of water usage over many years.

"WWC_FP.dat"   contains  Flow Periods (= Cumulation of WF Records)
ID start at   end at    Duration
P3 13:45:00 - 13:45:07   7.0 sec
P3 14:23:52 - 14:24:19  27.0 sec

Reducing the size of WWC_ALL.dat and WWC_WF.dat; One option would be to
write a timestamp only every ? second and the other fields every second
with commata between them.



List of modules and functions
Initialisation: Global var and arrays, Parameter settings, Files, etc.
	 - Initialize some global vars
	 
Notification Module
	- def notify(wf):
	
Detect ongoing Water-Flow  (Open valve or Leak detection)
     	- def fwf(wfc):               # Detect ongoing water-flow
	
Create  Flow Periods
	- def fp_1(ID, ts, power):    # Flow Period creation main
	- def fp_2():                 # Flow Period assembling of records
	
Diverse function
	- def check_time():           # Detect some points in Time, New Day, new hour etc
	- def ctrl_C(signal, frame):  # terminate program with CTRL_C key
	- def fR(str0,  CW):          # format data  to the right by colum size
	- def fR_dt(dt):              # format dt to sec or min
	
Development and Test function
	- def dev_and_test():         # create/display individual Frequency Bins
	
File handling globals and function
	- def all_log(txt):           # write all events to PT_Log.dat
	- def wf_log(txt):            # Writes only water-flow events to PT_WF.dat
    	- def fp_log(txt):            # Writes Flow Periods
	
Goertzel DFT/FFT  module
    	- def goertzel(samples, sample_rate, *freqs):
	
Main Module

