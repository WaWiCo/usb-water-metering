#===============================================================================
# PTC_fixed.py
# Read audiostream, detect Water-Flow and write results to files
# WaWiCo gramax
# start 21.07.18
# stand 23.01.21
#===============================================================================
#
################################################################################
# Python v.3.7.6
# 1. Python internal modules (all same version as python)
import os, sys, signal
import time, datetime
import math
# 2. external libraries
import pyaudio         # pyaudio_ver  = pyaudio.__version__;
import numpy as np     # numpy_ver    = np.__version__;
# Not using FFT but I use the numpy style arrays
# 3. Own .py modules
# NONE at this date 27.12.20
################################################################################
# diverse primary parameter, files,  general functions
################################################################################

p0 = datetime.datetime.now().strftime("%H:%M:%S.%f")
print("Program started at:", p0[0:10], ".....")

# 1. Setting global parameter
# ---------------------------
# Could also be loaded from a paramter file

# fr    # frequency resolution
# sf    # Sample frequency  Now fixed, not changeable
# sz    # Sample size, changable
# Relation: fr = sf/sz   sf = fr * sz  and  sz = sf/fr
SID         = "P01";       # Sensor ID  might be necessary in some situations
FP_check_dt = 15*60;       # Check every 15 minutes for Leaks and creating FPs
FP_FP_dt    =  3;          # Minimum time between 2 FPs
WF_WF_dt    =  3;          # Time interval writing records to the WF File
fr          =  7;          # Frequency  resolution  in Hz (1 to ?)
sf          = 44100;       # Sample frequency
sz          = int(sf/fr);  # sample size

factor1  = 0.0001;      # now 1/10.000    (Resize the Magnitude values)
factor2  = 1.0;         # now 1/10        ditto

# The Frequency bands/areas of interest (to look at).
# values are for my house (single home, PVC 1" and copper 1/2" pipe system)
fb1_A   = 1370;
fb1_B   = 1430;
fb2_A   = 1850;
fb2_B   = 1940;
fb3_A   = 2200;   # not used
fb3_B   = 2400;   # ditto
#Group 2:  1.370 to 1.430 Hz  with a maximum  between 1.380 - 1.410 Hz 1396-1400 low random noise
#Group 3:  1.720 to 1.940 Hz  with a maximum  between 1.790 - 1.850 Hz 1802-1830 low random noise
# factors to reduce or amplify Amplitude values  0
# Place Frequency Bands in an  array for easier handling
FBA  = np.zeros([5,7],dtype=int)
FBA[1][0] = 1;            # not used
FBA[1][1] = fb1_A;
FBA[1][2] = fb1_B;
FBA[2][0] = 1;            # not used
FBA[2][1] = fb2_A;
FBA[2][2] = fb2_B;
fba_nr    = 2;     # number of Frequncy Bands to look at;  minimum 1  max 4 !
Band1_mag_min = 30; # Minimum value for Magnitude to be recognized as coming from Water Flow.
Band2_mag_min = 30; # ditto
Mod_info  = "\n\n";
Mod_info += "DOC Program start at : " +  time.ctime() + "\n";
Mod_info += "DOC Current Settings from January 15th 2021:\n";
Mod_info += "DOC gramax;  Set values  fit my House in Seaside, CA\n";
Mod_info += "DOC SID: " + SID + ",  Record Interval: " + str(WF_WF_dt) + " sec" + "\n";
Mod_info += "DOC Frequency resolution (fr): " + str(fr) + " Hz" + "\n";
Mod_info += "DOC Sample Frequency fixed (sf): " + str(sf) + " Hz ---> Sample Size (sz): " + str(sz) + "\n";
Mod_info += "DOC Magnitude Factor 1: " + str(factor1) + ", Magnitude Factor 2: " + str(factor2) + "\n";
Mod_info += "DOC Amount of Frequency Bands to look at: " + str(fba_nr) + "\n";
Mod_info += "DOC Frequency Bands: " + str(FBA[1][1]) + "-" + str(FBA[1][2]) + " Hz  " +  \
               str(FBA[2][1]) + "-" + str(FBA[2][2]) + " Hz" + "\n";
Mod_info += "DOC FB1 Magnitude min: " + str(Band1_mag_min) +  \
               "    FB2 Magnitude min: " + str(Band2_mag_min) + "\n";

#-------------------------------------------------------------------------------

# Files etc.

FP  = "";     # File Path   none for now
WF0_file = open(FP + "WF_ALL_REC.dat", 'a+');    #   All records WF or NO WF
WF1_file = open(FP + "WF_RECORDS.dat", 'a+');    #   Only WF_Records
WF2_file = open(FP + "WF_FP.dat", 'a+');         #   Flow Periods  - NOT used in this module

#-------------------------------------------------------------------------------

def wf0_log(txt):               # Writes all events to WF_ALL_REC.dat
    WF0_file.write(txt + "\n")  #
    WF0_file.flush()
    os.fsync(WF0_file)          # force write
#-------------------------------------------------------------------------------
def wf1_log(txt):               # Writes only water-flow events to WF_RECORDS.dat
    WF1_file.write(txt + "\n")  #
    WF1_file.flush()
    os.fsync(WF1_file)          # force write
#-------------------------------------------------------------------------------
def fp_log(txt):                # Writes WF Periods  to WF_FP.dat
    WF2_file.write(txt + "\n")  #
    WF2_file.flush()
    os.fsync(WF2_file)          # force write

#-------------------------------------------------------------------------------
def fR(str0,  CW):                # format data  to the right by colum size
    dL = CW - len(str0)           # CW = columnn Width
    rw = " " * dL + str0
    return rw

#-------------------------------------------------------------------------------

def fR_sm(dt):     # seconds to minutes with 1 decimal
    if dt <= 59:
        rw = fR(str(dt),5) + " sec";
    else:
        rw = round(dt/60,2);
        rw = fR(str(rw),5) + " min"
    return rw;

#-------------------------------------------------------------------------------

def day_hour():
    TS_Temp = int(time.time());
    if TS_Temp % 86400 == 0:     # it is a new day
        temp =  "\n" + (time.asctime(time.localtime())) + "\n";
        fp_log(temp);
    elif TS_Temp % 3600 == 0:                        # it is a full hour
        temp = "DOC new Hour:  " + time.strftime('%H:%M:%S') + "\n";
    WF0_log.write(temp);
    WF1_log.write(temp);
    print(temp);

#-------------------------------------------------------------------------------

def ctrl_C(signal, frame):     # terminate
    FP_from_WF();
    temp  += "DOC End   at : " + time.ctime() + " by CTRL-C" + "\n";
    WF0_file.write(temp)
    WF1_file.write(temp)
    WF0_file.close()
    WF1_file.close()
    WF2_file.close()
    print(temp)
    sys.exit(0)

# and activate
signal.signal(signal.SIGINT, ctrl_C)


################################################################################
#  Check for Ongoing Water-Flow  - Leak-/or any unwanted Water-Flow detection
################################################################################

# Warning Flag for continuos Water-Flow
WFC          = np.zeros(3);
WFC_limit    = 900   # 15 minutes

#-------------------------------------------------------------------------------

def wfc_check(wf_fl):     # Detect ongoing water-flow and create alarm
    global  WFC, WF_WF_dt
	# 0 not used # 1 wf  # 2 no wf    # we have to use WF_WF_dt as dt  and not 1
    if wf_fl ==  1:
        WFC[1] += WF_WF_dt;   # [1] = WF
    else:   # -
        WFC[2] += WF_WF_dt;   # [2] = NO WF
    #print("wf_fl ", wf_fl, WFC[1], WFC[2]);
    if  WFC[2] >= (2*WF_WF_dt):   # If the No Waterflow Counter  exceeds 2  then both are set back to Zero
        WFC[1] = 0
        WFC[2] = 0
    if WFC[1] >=  WFC_limit:
        wfc_notify(WFC[1])
    #print("wf_fl ", wf_fl, WFC[1], WFC[2]);
#-------------------------------------------------------------------------------

def wfc_notify(wf):     # Local (sound, optical), Remote (server, e-mail, telephone)
	# wf = amount of seconds since ongoing WF exists
    print("Ongoing waterflow for: " + str(wf) + " seconds")

################################################################################
#  Check WFA array for creating Flow Periods
################################################################################
# Water Flow  and Flow Periods Inis
WFA_max    = 900;  # Size of array
WFA_ptr    = 0;
WFA        = np.zeros([WFA_max+1, 4],dtype=int);  # Water Flow events to create FP's from

#-------------------------------------------------------------------------------

def FP_from_WF():                #  called by  Task_timer() and CTRL_C
    global WFA, WFA_ptr, FP_FP_dt
    # local vars:  dt_WFR = dt bewteen 2 records WFA, dt_FP =  dt of a WFP  start to End
    #print("\n", WFA_ptr, "\n");
    WFA_ptr = WFA_ptr -1;
    i =  0;
    ii = 0;
    FP_start = WFA[i][0] - int(FP_FP_dt/2);   # The WF must have started before
    FP_end   = WFA[i][0];                     # so lets subtract FP_FP_dt/2
    FP_M1    = WFA[i][1];
    FP_M2    = WFA[i][2];
    while i <= WFA_ptr:
        i += 1;
        dt_WFR = WFA[i][0] -  WFA[i-1][0];    # The dt between 2 Water Flow Records
        print(dt_WFR,"\n")
        if dt_WFR <= (2*FP_FP_dt):
            ii +=1;                 # inside an ongoing WFP
            FP_end   = WFA[i][0];
            FP_M1   += WFA[i][1];
            FP_M2   += WFA[i][2];
        if dt_WFR > (2*FP_FP_dt) or i ==  WFA_ptr:    #  WF belongs to a new FP or it is End of array
            # 1. end and create/write FP
            dt_FP = FP_end - FP_start          # Length of WF Period
            print(dt_FP, "\n")
            if dt_FP  >= (2*FP_FP_dt):    # Process only if dt => Minimum duration
                ii +=1;
                t1 = datetime.datetime.fromtimestamp(FP_start).strftime("%H:%M:%S");
                t2 = datetime.datetime.fromtimestamp(FP_end).strftime("%H:%M:%S");
                t3 = fR_sm(dt_FP);   # format to seconds or minutes
                t4 = int(FP_M1/ii);
                t5 = int(FP_M2/ii);
                t6 =  FP_calc(FP_start, dt_FP, t4, t5);  # calc volume, gpm and user
                temp = str(t1) + " - " + str(t2) + " " + t3 +  " " +  t6;
                       # fR(str(t4),7) + " " +  fR(str(t5),7) ;
                fp_log(temp)     # Write to fP file
                print(temp)
            # in any case fp_log or not
            # 2. Start a new FP or End Loop
            if i == WFA_ptr:
                break;     # end loop
            else:
                ii = 0;
                FP_start = WFA[i][0];   #
                FP_end   = WFA[i][0];
                FP_M1    = WFA[i][1];
                FP_M2    = WFA[i][2];
            # END if/else
        # END if
    # End while
    ii = 0;
    while ii <=  WFA_ptr:
        WFA[i][0] = 0;
        WFA[i][1] = 0;
        WFA[i][2] = 0;
        ii += 1;
    WFA_ptr = 0;
    # END FP_from_WF()

#-------------------------------------------------------------------------------

def FP_calc(tA, dt, M1, M2):   # Define the Volume and the possible water-user by anlyzing  the data
    # tA = Start TS,   dt= flow Duration,  M1/M2 - Magnitude in FB 1/FB 2
    txt = "NYD";
    return txt;

################################################################################
#  Goertzel_part 2   Compares sample values with certain Frequency bands only
################################################################################

def Goertzel_part2():
    # 7. Calculate magnitude of Sound samples for the selected frequency bands of interest
    nr_SA  = range(0, sz);
    #FRA    = [];      # Freqency
    #MAA    = [];      # Magnitude for that Frequency
    for k in bins:
        # Bin frequency and coefficienPT for the computation
        f = k * f_step_N
        w_real = 2.0 * math.cos(2.0 * math.pi * f)
        w_imag = math.sin(2.0 * math.pi * f)
        # Doing the calculation on the SA data array  only power NOT real and imag.
        d1, d2 = 0.0, 0.0
        for n in nr_SA:
            y  = SA[n] + w_real * d1 - d2
            d2 = d1
            d1 = y
        magnitude  = int(d2**2 + d1**2 - w_real * d1 * d2);
        frequency  = int(f * sf)
        magnitude  = int(magnitude * factor1);
        #FBA_update(frequency, magnitude)    # fill FBA
        # now placed here limited to 2 Freqency bands    #### Needs to be rewritten !!!
        # print("A ",  FBA[1][3], FBA[2][3], " ",  magnitude)
        if frequency >= FBA[2][1]:
            FBA[2][3] += magnitude;
        else:
            FBA[1][3] += magnitude;
        # print("B ", FBA[1][3], FBA[2][3])
        #MAA.append(magnitude);
        #FRA.append(frequency);
    # END for going through bins
    FBA[2][3] = int((FBA[2][3]/nr_Bin) * factor2);
    FBA[1][3] = int((FBA[1][3]/nr_Bin) * factor2);
    # maa_l = len(MAA);

################################################################################
#  Main Module   Goertzel part1 inside this module
################################################################################
#  All paramter moved to befin of file for easy access to change them
# print the Paramter set
wf0_log(Mod_info);          #
wf1_log(Mod_info);          #
print(Mod_info);

TS_Akt   = int(time.time());    # Actual (current) TimeStamp
TS_Last  = TS_Akt;   # Last TimeStamp,
SA       = [];      # Sample array  from pyaudio
# ------------------------------------------------------------------------------
# 2. Goertzel Part 1: Creating the Frequency bands parameters like steps and bins etc.
f_step_S          = sf/float(sz)        # step in sample array
f_step_N          = 1.0/sz              # step in ?
Mod_info= "DOC f_step_S : " + str(f_step_S) + " f_step_N ???: " +  str(f_step_N) + "\n";
bins = set()
fba_ii = 1
while fba_ii <= fba_nr:     # Go through all given frequency bands and add to bins
    f_start = FBA[fba_ii][1]
    f_end   = FBA[fba_ii][2]
    k_start = int(math.floor(f_start / f_step_S))
    k_end   = int(math.ceil(f_end / f_step_S))
    Mod_info +=  "DOC fba_ii: " + str(fba_ii) + "\n" + \
              "DOC f_start: " + str(f_start) + " f_end: " + str(f_end)  + "\n" \
              "DOC k_start: " + str(k_start) + " k_end: " + str(k_end)  + "\n";
    bin_pr = range(k_start, k_end)  # part range  from  till
    Mod_info += "DOC bin_part_range: " +  str(bin_pr) + "\n"
    bins   = bins.union(bin_pr)  # add to total bin set
    fba_ii += 1;
# End while
nr_Bin = len(bins);
Mod_info+= "DOC Nr of Bins: " + str(nr_Bin) + "\n";
Mod_info+= "DOC Bins" + str(bins);
# End Goertzel Part
# ------------------------------------------------------------------------------
temp2 =  "DOC TimeStamp FB1 Mag FB2 Mag  (#)";
wf0_log(Mod_info+ "\n" + temp2);          #
wf1_log(Mod_info+ "\n" + temp2);          #
# header for screen printout  FB = Frequency Band   Mag = Magnitude
#  # /  sec"  =  Amount of analysis runs /  Time duration per run in sec
temp2 = " time       FB 1       Mag       FB 2       Mag    # /  sec"
print(Mod_info);
print(temp2);

# 3. Create and start reading from Audio Stream   using pyAudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16,channels=1,rate=sf,input=True,
              frames_per_buffer=sz)
stream.start_stream()
# 3. Start endless Loop for read and analyze soundstream
TS_Loop_Start = time.time();
WFA_ptr = 0;
ct = 0;     # ct is number of cycles consisting of stream.read() and frequency/Magnitude checking per write
while True:
	# 4. Read from Audiostream and window the data
    ct += 1;
    SA = np.frombuffer(stream.read(sz, exception_on_overflow = False), dtype=np.int16);       # get chunks of data from soundstream
    SA = SA * np.hanning(len(SA))      # smooth it by  windowing the data
    # original Fu
    #FRA, MAA = goertzel(SA, sf, (frq1_A, frq1_B), (frq2_A, frq2_B));
    TS = time.time()
    Goertzel_part2();  #  New  reduced version\
    TD = str(time.time() - TS)
    #### ===== alternativly Goertzel_part2 inside here in the main
    TS_Akt   = int(time.time())
    # print("C ",  ct , " ",  FBA[1][3], FBA[2][3])
    if TS_Akt/2 == 0:   # Every 2 seconds
        day_hour();
    if TS_Akt - TS_Last >= WF_WF_dt:
        FBA[1][3] = int(FBA[1][3]/ct);     # Resulting Magnitude for frequency Band 1
        FBA[2][3] = int(FBA[2][3]/ct);     # ditto band 2
        p0 = datetime.datetime.fromtimestamp(TS_Akt).strftime("%H:%M:%S");   # Integer to h:m:
        # a) just write to screen
        print(p0, FBA[1][1], "-", FBA[1][2],fR(str(FBA[1][3]),5), \
              "  ", FBA[2][1], "-", FBA[2][2], fR(str(FBA[2][3]),5),  " ", fR(str(ct),2), "/", TD[:5]);
        # b) write to file;
        temp = SID + " " + str(TS_Akt)  + " " + fR(str(FBA[1][3]),5) + "   " + \
               fR(str(FBA[2][3]),5)  + "  ("  + fR(str(ct),2) + ") ";
        wf0_log(temp);
        if  FBA[1][3] >= Band1_mag_min and  FBA[2][3] >= Band2_mag_min:   # There is Water Flow
            wf1_log(temp);                  # store values for later use (proof, reuse( ))
            WFA[WFA_ptr][0] = TS_Akt;       # WF array to create FP's  from
            WFA[WFA_ptr][1] = FBA[1][3];
            WFA[WFA_ptr][2] = FBA[2][3];
            WFA_ptr += 1;
            wfc_check(1);         # detect continuos Water_Flow
        else:
            wfc_check(0);
        TS_Last = TS_Akt
        FBA[1][3] = 0;
        FBA[2][3] = 0;
        ct = 0;
    # if END
    if TS_Akt %  FP_check_dt == 0:    # Check if FPs need to be created
       FP_from_WF()
    TS_Loop_End = time.time();
#  while END  by CTRL_C or Error
tmp1  = "Program  End   at : " + time.ctime() + " by CTRL-C"
print(tmp1 + " " + str(signal))

#-------------------------------------------------------------------------------
# EOF
