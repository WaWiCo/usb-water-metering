################################################################################
# WFD2.py     Water Flow Detection;  Find/define the Frequency Bands in which
# sound from Water-Flow has a maximum.  I also automatically eliminates noise that
# may exist strongly in other Frequency ranges but only weakly in the Frequency
# Bands of # Water-Flow.
# by gramax, WaWiCo
# December 27th 2020
# Stand: Febr. 5th 2021
#-------------------------------------------------------------------------------
# Should work on any computer with a  Win 10, Mac OS 10.x or Linux OS
# Python 3.x  and the libraroes pyaudio and numpy
# For testing it also works with a  build in microphone.
# For getting real data it needs the USB soundcard/Microphone combination
#
# Creates file "WWC_ANA.dat" that look like this
# Frq. Band 1: 1585 - 1605 Hz  Frq. Band 2: 1900 - 1920 Hz  (Sample Freq: 44100 Hz  Frequency Resolution: 3 Hz  --> Sample Size (Chunk): 14700)
# ID          time   Frq Hz: 1584    1586    1590    1592    1596    1599    1602    1898    1902    1905    1908    1911    1914    1917     avg FB1/FB2    max FB1/F  max FB2/F smp/sec
# P3 1612716190 08:43:10        0       0       7       1       1       3      10       0       1       0       2       3       0       0        3 /     0     10/1602      3/1911  1
# P3 1612716191 08:43:11        3       1       1       3       5       5       1       0       0       0       0       1       1       0        2 /     0      5/1596      1/1911  3
# P3 1612716192 08:43:12        1       1       0       7       6       2       1       1       0       1       3       1       0       0        2 /     0      7/1592      3/1908  3
# This file can be used for further in depth analysis for Sensor/frequency/time pattern
################################################################################
"""
List of modules and functions
# Diverse function
	def check_time():           # Detect some points in Time, New Day, new hour etc
	def ctrl_C(signal, frame):  # terminate program with CTRL_C key
	def fR(str0,  CW):          # format data  to the right by colum size
# File handling globals and function
	def ana_log(txt):           # write all events to  WF_ANA.dat
# Goertzel DFT/FFT  module
    def goertzel(samples, sample_rate, *freqs):
# Main
"""
################################################################################
# Python 3 code
# 1. Python internal modules
import os, sys, signal
import time, datetime
import math
# 2. external libraries
import pyaudio         # pyaudio_ver  = pyaudio.__version__;
import numpy as np     # numpy_ver    = np.__version__;
# 3. Own py modules
# NONE at this date 27.12.20

################################################################################
# Initialisation: Global var and arrays, Parameter settings, Files, etc.
################################################################################
# Parameter settings  now set for my environment (house/pipe system)
# a) Frequency
RATE     =   44100;     # Fixed for my soundcard/Pc combo
freq_R   =       3;     # The wanted frequency Resolution
CHUNK    =  int(RATE/freq_R);   #  # --> resulting sample size for fR = 3 Hz
# frequency group 1
frg1_A   =  1585; #    # a 20 Hz range centered at 1595 Hz
frg1_B   =  1605; #
# frequency group 2
frg2_A   =  1900; #    # a 20 Hz range centered at 1910 Hz
frg2_B   =  1920; #
# This 2 bands with 3 Hz Resolution give 14 bins   with 2 Hz 21 bins

# b) factors  for reducing Magnitude values - might otherwise grow in some cases to astronomical values
factor1    = 100000;     # 100.000 in my case (my house, Sensor and Amplification level)
factor2    =   1;        # temporary set to 1 but  might need to be anywehre between 10 and 10.000
                         # Maybe we need a function as factor that does range and individual size specific reduction !!!

# 2 x 20 Hz bandwidth  = 40 Hz with 2 Hz freq Resolution = 21 Bins * 22.050 samples = 463.050 steps
#                              with 4 Hz freq Resolution = 11 Bins * 11.025 samples = 121.275 steps
# 1. Sample Frequency also called Sample Rate is fixed to 44.100 in case of USB soundcards
# 2. Sample Block Size also called Chunk is calculated by Sample Frequency / Frequency resolution
# 3. Frequency bands to investigate: now limited to 2
# 4. Frequency Resolution = Sample Frequency / Sample Block Size
#------------------------------- END  parameter settings -------------------------------------

################################################################################
# File handling
################################################################################
# define path, files and open/write to file
path         =  "";
freq_ana     =  "WWC_ANA.dat";     # For Development only;

file_path1  = path + freq_ana;
data_file1  = open(file_path1, 'a+');

def ana_log(txt):        #
    data_file1.write(txt + "\n")  #
    data_file1.flush()
    os.fsync(data_file1)          # force write

################################################################################
# Diverse function
# check_time():            # Detect some points in Time, New Day, new hour etc
# ctrl_C(signal)           # terminate program with CTRL_C key
# fR(str0,  CW):           # format data  to the right by colum size
################################################################################
def check_time():      # Detect some points in Time, New Day, new hour etc
    global TS_WFP
    txt = "0";
    TS_Temp = int(time.time());
    if TS_Temp % 86400 == 0:    # it is a new day
        txt = time.strftime('%Y-%m-%d %H:%M:%S')
    elif TS_Temp % 3600 == 0:    # it is a full hour
        txt = time.strftime('%H:%M:%S');
    if txt != "0":
        ana_log("DOC " + txt);

#-------------------------------------------------------------------------------

def ctrl_C(signal, frame):     # terminate program with CTRL_C key
    string  = "DOC End   at : " + time.ctime() + " by CTRL-C"
    ana_log(string);
    data_file1.close();
    print(string + " " + str(signal))
    sys.exit(0)

#-------------------------------------------------------------------------------

def fR(str0,  CW):                # format data  to the right by colum size
    dL = CW - len(str0)           # CW = columnn Width
    rw = " " * dL + str0
    return rw

################################################################################
# Goertzel DFT/FFT  module    From
# https://stackoverflow.com/questions/13499852/scipy-fourier-transform-of-a-few-selected-frequencies
################################################################################
def goertzel(samples, sample_rate, *freqs):
    window_size = len(samples)
    f_step = sample_rate / float(window_size)
    f_step_normalized = 1.0 / window_size

    # Calculate all the DFT bins we have to compute to include frequencies  in `freqs`.
    bins = set()
    for f_range in freqs:
        f_start, f_end = f_range
        k_start = int(math.floor(f_start / f_step))
        k_end   = int(math.ceil(f_end / f_step))
        bins    = bins.union(range(k_start, k_end))
	# For all the bins, calculate the DFT term
    n_range = range(0, window_size)
    freqs   = []
    results = []
    for k in bins:
        # Bin frequency and coefficients for the computation
        f = k * f_step_normalized
        w_real = 2.0 * math.cos(2.0 * math.pi * f)
        w_imag = math.sin(2.0 * math.pi * f)

        # Doing the calculation on the whole sample
        d1, d2 = 0.0, 0.0
        for n in n_range:       # 22.050 times at 2 Hz fR
            y  = samples[n] + w_real * d1 - d2
            d2, d1 = d1, y
        real_part = 0.5 * w_real * d1 - d2;
        imag_part = w_imag * d1;
        power     = d2**2 + d1**2 - w_real * d1 * d2;
        results.append(int(power));
        freqs.append(int(f * sample_rate))
    return freqs, results

################################################################################
# Main Modul
################################################################################
#vars and module activate, doc start
signal.signal(signal.SIGINT, ctrl_C)   # activare ctrl_C key

string = "DOC Start at : " + time.ctime();
ana_log(string);
# some globals
Sensor_ID   = "P3";    #  Type and which one
TS_Akt      = int(time.time())
TS_Last     = TS_Akt
TS_loop_dt  = 1;       # For this module it should be 1 second

FB1_avg     = 0;  # Magnitute inb Freq. Band 1
FB2_avg     = 0;  # ditto band 2
FB1_max     = 0;  # Max Magnitute in Freq. Band 1
FB2_max     = 0;  # ditto band 2
FB1_frq     = 0;  # freq of Max Magnitute in Freq. Band 1
FB2_frq     = 0;  # ditto band 2

#  Row with column header
row_hd     = "Frq. Band 1: " +  str(frg1_A) + " - " + str(frg1_B) + " Hz  " + \
             "Frq. Band 2: " +  str(frg2_A) + " - " + str(frg2_B) + " Hz "  + \
             " (Sample Freq: " + str(RATE)  +  " Hz  Frequency Resolution: " + str(freq_R) + " Hz"  + \
             "  --> Sample Size (Chunk): " + str(CHUNK) + ")\n"  + 	 "ID          time   Frq Hz:" ;
row_ctr    =  0;   # global var for counting row prints before a new columngeader is printed
loop_ctr   =  0;   # global var for counting data read and goertzel fu call before writing
row_hd_fl  =  False;

AF         = np.zeros([3,51],dtype=int)     # Magnitude per frequency Bin array

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,channels=1,rate=RATE,input=True,
              frames_per_buffer=CHUNK)
stream.start_stream()
loop_ctr = 0;
while True:
    loop_ctr += 1;
    # ======================== Frequency analysys Goertzel Version ========================
    data     = np.frombuffer(stream.read(CHUNK, exception_on_overflow = False), dtype=np.int16);    # get chunks of data from soundstream
    data     = data * np.hanning(len(data))                                                         # smoothit by  windowing data
    freqs, results = goertzel(data, RATE, (frg1_A, frg1_B), (frg2_A, frg2_B));                      # 2 ranges
    # ==============================fft part end ===============================
    bin_nr = len(freqs);
    ii = 0;
    while ii < bin_nr:                           # Sum results in AF[0][0] to bin_nr]
        AF[0][ii] = int(results[ii]/factor1)     # AF for display freq bin and creatung mean average
        ii += 1;
    TS_Akt = int(time.time());
    if TS_Akt - TS_Last >= TS_loop_dt:           # Check and write Only every ? second - now 1 second
	    # ------- start
        FB1_max = FB2_max = 0
        FB1_avg = FB2_avg = 0;
        iB1 = iB2 = 0;
        frq_sum = 0;
        ii = 0;
        while ii < bin_nr:
            AF[1][ii] = int(AF[0][ii]/(loop_ctr*factor2));   # get mean average and reduce value by factor2
            frq_sum += AF[1][ii]
            if freqs[ii] <= frg1_B:               # it is inside Frequency Group 1
                FB1_avg +=  AF[1][ii];
                if AF[1][ii] > FB1_max:
                    FB1_max = AF[1][ii]
                    FB1_frq = freqs[ii];
                iB1 += 1;
            else:                                 # otherwise it is Group 2
                FB2_avg += AF[1][ii];
                if AF[1][ii] > FB2_max:
                    FB2_max = AF[1][ii]
                    FB2_frq = freqs[ii];
                iB2 +=1;
            ii += 1;
        FB1_avg    = int(FB1_avg/iB1);
        FB2_avg    = int(FB2_avg/iB2);
		# ------
        str_TS     = str(TS_Akt)
        check_time();          # check/write new day or hour
        #  // Start old Test_and_Dev()
        if row_hd_fl == False:   # create header one time
            ii = 0;
            while ii < bin_nr:  # not bin_nr itself because we start with 0
                row_hd += fR(str(int(freqs[ii])),5) + "   ";   # 0 to above 1,000,000
                ii += 1;
            row_hd += "     avg FB1/FB2/sum   max FB1/F / max FB2/F / sum smp/sec";
            row_hd_fl = True;
        # endif
        row_ctr +=1;
        if row_ctr >= 30:
            row_ctr = 1;
        if row_ctr == 1:
            ana_log("\n" + row_hd);
            print("\n" + row_hd)
        WF_flag = "  ";
        row_string = "";
        ii = 0;
        while ii < bin_nr:   # < bin_nr because we start with 0
            row_string  += fR(str(AF[1][ii]),7) + " ";
            ii += 1;
        str_TS = str(int(time.time()));
        str_TD = time.strftime('%H:%M:%S' + " ")
        string = Sensor_ID + " " + str_TS + " " + str_TD + " " + row_string + "   " +  \
                 fR(str(FB1_avg),5) +  "  " + fR(str(FB2_avg),5) + "  " + fR(str(FB1_avg + FB2_avg),5) + " " + \
                 fR(str(FB1_max) +  " " + str(FB1_frq),10) + "  " + \
                 fR(str(FB2_max) +  " " + str(FB2_frq),10) + "  " + fR(str(FB1_max + FB2_max),5) + "   " + \
                 str(loop_ctr);
        ana_log(string);
        print(string);     # // end old Test_and_Dev()
        i = 0;
        while i < bin_nr:
            AF[0][i] = 0     # Zero the Freq Power array for next loop
            AF[1][i] = 0
            i += 1;
        string  = "";
        frq_sum = 0;
        loop_ctr = 0;
        TS_Last = int(time.time());
    # END if
# END while
stream.stop_stream()
stream.close()
p.terminate()
exit(0)
# ------------------------------------------------------------------------------
# EOF
