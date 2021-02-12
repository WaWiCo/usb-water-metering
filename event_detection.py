################################################################################
# WFD3.py  - Detect and document Water-Flow in a home water-pipe system.
# by gramax, WaWiCo
# Januar 2nd 2021
# Stand: Febr. 7th 2021
#-------------------------------------------------------------------------------
# Should work on any computer with a  Win 10, Mac OS 10.x or Linux OS
# Python 3.x  and the libraries pyaudio and numpy
# For testing it also works with a  build in microphone.
# For getting real data it needs the USB soundcard/Microphone combination
# ------------------------------------------------------------------------------
# Start: Python WFD3.py    Runs for ever End: "CTRL C".
# "Ctrl Z" ends Python and may result in loss of some data not yet stored in file
# The program creates following 3 files that can be opened/look at with any editor.
# "WWC_ALL.dat"  contains all recoed Water-Flow or  not
# ID TS          avg FB1    FB2  max FB1    FB2
# P3 1612734296       0       1       2       3
# P3 1612734297       2       4       9       9
# P3 1612734298    2170    3356    6165   12507
# P3 1612734299    2526    3168    4242    6465

# "WWC_WF.dat" contains only Water-Flow   Records
# Structure 100% identical with WWC_ALL.dat
# P3 1612734298    2170    3356    6165   12507
# P3 1612734299    2526    3168    4242    6465
# Both WWC_ALL.dat and WWC_WF.dat are planned as basis for an unlimited amount
# of further analysyis and statistics/graphics etc.  WWC_ALL.dat can alo be used
# for a gapless documentation of water usage over many years.

# "WWC_FP.dat"   contains  Flow Periods (= Cumulation of WF Records)
# ID start at   end at    Duration
# P3 13:45:00 - 13:45:07   7.0 sec
# P3 14:23:52 - 14:24:19  27.0 sec

# Reducing the size of WWC_ALL.dat and WWC_WF.dat; One option would be to
# write a timestamp only every ? second and the other fields every second
# with commata between them.
#
################################################################################

"""
List of modules and functions
# Initialisation: Global var and arrays, Parameter settings, Files, etc.
	 Initialize some global vars
# Notification Module
	 def notify(wf):
# Detect ongoing Water-Flow  (Open valve or Leak detection)
     def fwf(wfc):               # Detect ongoing water-flow
# Create  Flow Periods
	 def fp_1(ID, ts, power):    # Flow Period creation main
	 def fp_2():                 # Flow Period assembling of records
# Diverse function
	def check_time():           # Detect some points in Time, New Day, new hour etc
	def ctrl_C(signal, frame):  # terminate program with CTRL_C key
	def fR(str0,  CW):          # format data  to the right by colum size
	def fR_dt(dt):              # format dt to sec or min
# Development and Test function
	def dev_and_test():         # create/display individual Frequency Bins
# File handling globals and function
	def all_log(txt):           # write all events to PT_Log.dat
	def wf_log(txt):            # Writes only water-flow events to PT_WF.dat
    def fp_log(txt):            # Writes Flow Periods
# Goertzel DFT/FFT  module
    def goertzel(samples, sample_rate, *freqs):
# Main Modul
"""
################################################################################
# Python 3 code
# 1. Python internal modules (all same version as python)
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
# Paramter settings  now set for my environment (house/pipe system)
# This Paramter you may  get from running WFD2.py and they have to be set
# otherwise it will deliver meaningless data or no data at all.
# Frequency sample rate and resolution
RATE     =   44100;
freq_R   =       3;     # The wanted frequency Resolution
CHUNK    =  int(RATE/freq_R);   #  # --> resulting sample size for fR = 2 Hz
# Because we use the Goertzel algorithm CHUNK does not need to be a power of 2.
# frequency group (Band) 1
frg1_A   =  1585; #    # a 20 Hz range centered at 1595 Hz
frg1_B   =  1605; #
# frequency group (Band) 2
frg2_A   =  1900; #    # a 20 Hz range centered at 1910 Hz
frg2_B   =  1920; #
# Minimum Magnitude Level for being recognized as coming from Water_flow
FB1_ML   =   75    # for Frequency Band 1:
FB2_ML   =   75    # for Frequency Band 2:
FB12_f   =   0.67  # factor -->  FB12_f * (FB1_ML +FB2_ML)  # here 2/3 of sum
                   # if (FB1_avg + FB2_avg) >= (FB12_f*(FB1_ML + FB2_ML)):

WF_time_limit = 15 # The allowed continuous Water-Flow time in minutes,
                   # If Water runs longer without stop an alarm is triggered.

# Factors  for reducing Result values - might otherwise grow in some cases to astronomical values
factor1    = 100000;     # 100.000 in my case (my house, Sensor and Amplification level)
factor2    =   1;        # temporary set to 1 but  might need to be anywehre between 10 and 10.000
                         # Maybe we need a function as factor that does range and individual size specific reduction !!!
#------------------------------- END  parameter settings -------------------------------------

################################################################################
# File handling globals and function
################################################################################

# define path, files and open the files

path         =  "";
freq_all     =  "WWC_ALL.dat";           # all records WF or No WF, for further use
freq_wf_only =  "WWC_WF.dat";            # Water flow records only, for further use
flow_periods =  "WWC_FP.dat";            # Water Flow Periods in human readable form

file_path2  = path + freq_all
data_file2  = open(file_path2, 'a+');

file_path3  = path + freq_wf_only;
data_file3  = open(file_path3, 'a+');

file_path4  = path + flow_periods
data_file4  = open(file_path4, 'a+');

#-------------------------------------------------------------------------------
# write to files

def all_log(txt):        # write all events,
    # Purpose: To create a Zero time gap documentation;  1 per second  24/7
    data_file2.write(txt + "\n")  #
    data_file2.flush()
    os.fsync(data_file2)          # force write

#-------------------------------------------------------------------------------

def wf_log(txt):          # Writes only water-flow events
    # Purpose: Zero gap Water-Flow documentation;
    data_file3.write(txt + "\n")  # PT_WF.dat
    data_file3.flush()
    os.fsync(data_file3)          # force write

#-------------------------------------------------------------------------------

def fp_log(txt):           # Writes Flow Periods  (Water-Flow from, till)
    # Purpose:  Have a ready for use human readable List of all water usage
    data_file4.write(txt + "\n")  # PT_FP.dat
    data_file4.flush()
    os.fsync(data_file4)          # force write


################################################################################
# Notification Modulue
# 27.12.20 just a stubb - that prints to screen
# Should be an external module that can be used in other apps.
################################################################################

def notify(ts):    # notification (Alarm )
    # ts  is Timestamp when WF started
    ts0 = int(time.time());
    ts1 = datetime.datetime.fromtimestamp(ts0)
    ts2 = datetime.datetime.fromtimestamp(ts);  #
    txt = "Warning ! " + ts1.strftime('%H:%M:%S') + " Ongoing waterflow since: " + \
    ts2.strftime('%H:%M:%S') + "  = " + fR_dt(ts0 - ts);
    print(txt);
    """
    Should offer several; Notificatopn option
    switch/case loop with notify option to
    a) Local PC,  TV ?
       - PC  screen and Speaker
       - TV
       - ?
    b) Remote
       - remote server  (internet)
       - e-mail (internet)
       - telephone, voice, sms (via Internet to Telephone gateway))
    """

################################################################################
# Detect ongoing Water-Flow  (Open valve or Leak detection)
################################################################################

def owf_detect(wfc, ts):     # Detect ongoing water-flow in sequence
    """
	# OWF[0]  = Max  WF
	# OWF[1]  = No Water Flow
	# OWF[2]  = TS for No Water Flow
	# OWF[3]  = Water-Flow
	# OWF[4]  = TS of Water-Flow
	very clumsy!
	"""
    # OWF[0] = 10;  #TEST
    if wfc ==  -1:        # No WF
        OWF[1] += 1;
        OWF[2]  = ts;
    else:
        OWF[3] += 1;      # Water Flow
        OWF[4]  = ts;
        if OWF[3] == 1:
            OWF[5] = ts   # Set Start time
    if OWF[1] >= 3:           # There are 3 or more  "No Water-Flow" events
        wf_dt =	ts - OWF[4];  # Current TS - last TS for water-flow
        if wf_dt > 3:         # the last WF was more than 3 seconds ago so it is No WF
            OWF[3] = 0;       # Set ongoing water-flow to 0
    if OWF[1] >= 10:
        OWF[1] = 0;
    if OWF[3]  >=  OWF[0]:     # OWF[The max dt of water-flow in normal range = below set limit
        OWF[3] = 0;
        notify(OWF[5]);


################################################################################
# Create  Flow Periods
# 2 function: FP_1 (main) and FP_2 (create)
################################################################################

def fp_1(ID, ts, power):   # FP creation main module
    """
    ID    = identify from where the fu is called
    ts    = timestamp (TS_akt)
    power = Sound Magnitude of a WF frequency range
    Update an onging WF or send to FP_2 for writing an FP that ended
    """
    global WF,  WF_ptr, WF_ptr_max, FP,  FP_dt_min, FP_dur_min, FP_P, FP_P_ptr;

    #print("1. in fp_1: ", ID, ts, power);
    if ts != 0:   # Call from  main-module if there dt between 2 WF records above minimum !
        WF[WF_ptr][0] = ts;
        WF[WF_ptr][1] = power;
        WF_ptr += 1;
    if WF_ptr >= WF_ptr_max or ID  == 99:   # either reached  max ptr or call from  check_time()
    	# Create  WF-Periods from content in WF
        #print("1.1. in fp_1: ", WF_ptr, " ", ts, " ", power);
        TS_End = int(time.time());
        TS_Start = TS_End - TS_WFP;
        # Check if WF not empty then go through array
        i = 0;
        while i < WF_ptr_max:   # Now go through the WF array
            #print(WF[i][0]);
            if WF[i][0]== 0:    # reached End of entries in WF  array
                fp_2();
                break;
            elif WF[i][0] >= TS_Start:
                dt =  WF[i][0] -  WF[i-1][0];   # get dt between 2 entries
                if dt <  FP_dt_min:             # it is inside an ongoing FP
                    FP[2]   =  WF[i][0];        # TS End
                    FP_P[FP_P_ptr] =  WF[i][1];
                    FP_P_ptr += 1;
                    #print("UPD: ", FP_P_ptr)
                else:                        # The value belong to a new FP
                    fp_2();             # create FP and write to file
                    #print(4);
                    FP[1] =  WF[i][0];       # TS start
                    FP[2] =  FP[1];          # and also END
                    FP_P_ptr = 0;
                    FP_P[FP_P_ptr] =  WF[i][1];
            i += 1;
        # END while
        i = 0;
        while i < WF_ptr_max:     # set WF[][] back to 0
            WF[i][0] = 0;
            WF[i][1] = 0;
            i += 1;
        WF_ptr = 0;       # ditto ptr
    # END  creating FPs

#-------------------------------------------------------------------------------

def fp_2():     # Create FPs and write to file
    global FP, FP_dt_min, FP_dur_min, FP_P, FP_P_ptr, WF_ptr_max, Sensor_ID, FB1_ML, FB2_ML
    #print("2. in fp_2:");
    # FP[0] # not used,  # FP[1] = TS Start,  # FP[2] = TS End, # FP[3] = Duration, # FP[4] = Power
    FP[3] = FP[2] - FP[1];
    # copy FP_P for content not 0   till size FP_P_ptr; Needed to get median without Zeros at the end
    i = 0;
    AM_sum = 0;
    AM = np.zeros(FP_P_ptr+1, int)
    while i <= FP_P_ptr:
        AM[i] = FP_P[i];
        AM_sum += FP_P[i];
        i += 1;
    FP[5] = int(AM_sum/i);     # the mean average
    FP[4] = np.median(AM);     # get the median value;
    FP_P  = np.zeros((WF_ptr_max+1), int)   # then delete  array by recreating
    if FP[3] >= FP_dur_min and FP[4] >=  FB1_ML:     # It exceeds the minmum duration for a WF period and >= minimum power level
        ts1 = datetime.datetime.fromtimestamp(FP[1])
        ts2 = datetime.datetime.fromtimestamp(FP[2])
        ts3 = fR_dt(FP[3]);
        string  =  Sensor_ID + " " + (ts1.strftime('%H:%M:%S')) + " - " + (ts2.strftime('%H:%M:%S')) + " " + ts3;
        fp_log(string);
    while i <= 9:
        FP[i] = 0;   # set back to 0
        i += 1;


################################################################################
# Diverse function
# check_time():            # Detect some points in Time, New Day, new hour etc
# ctrl_C(signal, frame)    # terminate program with CTRL_C key
# fR(str0,  CW):           # format data  to the right by colum size
# fR_dt(dt):               # formt dt to either sec or min

################################################################################

def check_time():      # Detect some points in Time, New Day, new hour etc
    global TS_WFP
    txt = "0";
    TS_Temp = int(time.time());
    if TS_Temp % 86400 == 0:    # it is a new day
        txt = time.strftime('%Y-%m-%d %H:%M:%S')
    elif TS_Temp % 3600 == 0:    # it is a full hour
        txt = time.strftime('%H:%M:%S');
    if txt != "0":	# write to all 3 files
        all_log("DOC " + txt);
        wf_log("DOC " + txt);
        fp_log("DOC " + txt);
    if TS_Temp % TS_WFP == 0:    # Create Flow Period every dt now 15 minutes
        fp_1(99, 0, 0);

#-------------------------------------------------------------------------------

def ctrl_C(signal, frame):     # terminate program with CTRL_C key
    fp_1(99, 0, 0);      # Write to file what still might be in the WF array.
    string  = "DOC End   at : " + time.ctime() + " by CTRL-C"
    all_log(string);
    wf_log(string);
    fp_log(string);
    data_file2.close();
    data_file3.close();
    data_file4.close();
    print(string + " " + str(signal));
    sys.exit(0)

#-------------------------------------------------------------------------------

def fR(str0,  CW):                # format data  to the right by colum size
    dL = CW - len(str0)           # CW = columnn Width
    rw = " " * dL + str0
    return rw

# ------------------------------------------------------------------------------

def fR_dt(dt0):
    if dt0 < 60:
        rw = round(dt0,1);    # to 1.x
        rw = fR(str(rw),5) + " sec";
    else:
        rw = round(dt0/60,1); # to 1.x
        rw = fR(str(rw),5) + " min";
    return rw;

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
all_log(string);
wf_log(string);
fp_log(string);
# some globals
Sensor_ID   = "P3";    #  Type and which one
TS_Akt      = int(time.time())
TS_Last     = TS_Akt
TS_Live     = TS_Akt
TS_WFP      = 900;       # now 15 min Time duration to check for Flow Periods
TS_loop_dt  = 1;         # Process the collected dat every TS_loop_dt in second
day_Akt     = time.strftime('%a, %b, %d. %Y')
day_Last    = day_Akt

FB1_avg     = 0;  # Magnitute inb Freq. Band 1
FB2_avg     = 0;  # ditto band 2
FB1_max     = 0;  # Max Magnitute in Freq. Band 1
FB2_max     = 0;  # ditto band 2
FB1_frq     = 0;  # freq of Max Magnitute in Freq. Band 1
FB2_frq     = 0;  # ditto band 2

# Water Flow record Array  for creating Flow Periods
WF_ptr_max = 600;
WF         = np.zeros([WF_ptr_max+1, 2],dtype=int) # Water Flow events
WF_ptr     = 0;

FP_P       = np.zeros(WF_ptr_max+1)  # Flow Period Power array to get median  size aas WF
FP_P_ptr   = 0;


# Flow Periods
FP         = np.zeros(11);
FP_ptr     = 0;

# Flow Period Parameter
FP_dt_min  = 4;    # minimum time between 2 FPs in seconds to eliminate random signals in the WF range
FP_dur_min = 5;    # Minimum time duration to be seen as a Flow Period  (in seconds)


loop_ctr   =  0;   # global var for counting data read and goertzel fu call before writing

AF         = np.zeros([3,51],dtype=int)     # Magnitude per frequency Bin array

# Array to check for Ongoing Water-Flow
OWF        = np.zeros(7);  # Water Flow events
OWF[0]     = WF_time_limit * 60;       # in seconds
OWF[2]     = int(time.time());
OWF[4]     = OWF[0];
OWF[5]     = OWF[0];

# In case of FP only 1 time at the begin!
row_hd = "DOC     TS      avg FB1    FB2   max FB1   FB2"
all_log(row_hd);
print(row_hd)

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,channels=1,rate=RATE,input=True,
              frames_per_buffer=CHUNK)
stream.start_stream()
loop_ctr = 0;
while True:
    loop_ctr += 1;
    # ==========  read data from audio stream and Goertzel module ==============
    data     = np.frombuffer(stream.read(CHUNK, exception_on_overflow = False), dtype=np.int16);    # get chunks of data from soundstream
    data     = data * np.hanning(len(data))                                                         # smoothit by  windowing data
    freqs, results = goertzel(data, RATE, (frg1_A, frg1_B), (frg2_A, frg2_B));                      # Goertzel limited to 2 ranges
    # ==============================fft part end ===============================
    bin_nr = len(freqs);
    ii = 0;
    while ii < bin_nr:                           # Sum results in AF[0][0] to bin_nr]
        AF[0][ii] = int(results[ii]/factor1)
        ii += 1;
    check_time();                                # check/write new day or hour
    TS_Akt = int(time.time());
    if TS_Akt - TS_Last >= TS_loop_dt:           # Check Only every  ? second !
        FB1_max = FB2_max = 0
        FB1_avg = FB2_avg = 0;
        iB1 = iB2 = 0;
        frq_sum = 0;
        ii = 0;
        while ii < bin_nr:
            AF[1][ii] = int(AF[0][ii]/(loop_ctr*factor2));   # get mean average and reduce value by factor2
            frq_sum += AF[1][ii]
            if freqs[ii] <= frg1_B:            # in Frequecy Band 1
                FB1_avg +=  AF[1][ii];
                if AF[1][ii] > FB1_max:
                    FB1_max = AF[1][ii]
                    FB1_frq = freqs[ii];
                iB1 += 1;
            else:
                FB2_avg += AF[1][ii];
                if AF[1][ii] > FB2_max:
                    FB2_max = AF[1][ii]
                    FB2_frq = freqs[ii];
                iB2 +=1;
            ii += 1;
        FB1_avg    = int(FB1_avg/iB1);
        FB2_avg    = int(FB2_avg/iB2);
        str_TS     = str(TS_Akt)
        string = Sensor_ID + " " + str_TS + " " + fR(str(FB1_avg),7) + " " + fR(str(FB2_avg),7) + " " + fR(str(FB1_max),7) + " " + fR(str(FB2_max),7);
        all_log(string);     # write to file WWC_ALL.dat in both cases
        temp = "  NO WF " + str(int(OWF[1])) + "   WF " +  str(int(OWF[3]));
        print(string  + temp)
        owf_ctr = -1   #  -1 = No Water_flow
        #if (FB1_avg  >=  FB1_ML and FB2_avg > FB2_ML):        # Magnitude on both FBs are above minimum
        if (FB1_avg + FB2_avg) >= (FB12_f*(FB1_ML + FB2_ML)):   # sum of both is at least 2/3  of the he sum of both minimum values
            owf_ctr =  1;   # +1 = Water_flow
            wf_log(string);      # write to  WF.dat
            fp_1(0, TS_Akt, frq_sum); # check/create Flow Periods
        owf_detect(owf_ctr, TS_Akt);   # check for continuos WF
        string  = "";
        frq_sum =  0;
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
