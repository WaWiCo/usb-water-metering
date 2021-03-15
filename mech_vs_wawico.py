##############################################
# Measuring water flow with mechanical flow
# meter for comparison against WaWiCo Acoustic
# flow detection
#
# -- by WaWiCo 2021
# 
##############################################
#
import time,sys,datetime
import signal as rpi_sig
import RPi.GPIO as gpio
import pyaudio
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
#
#####################################
# Functions for handling mechanical
# meter interrupts
#####################################
#
def signal_handler(sig,frame):
    gpio.cleanup()
    sys.exit(0)

def sensor_callback(chan):
    global counter
    counter+=1

##############################################
# function for FFT
##############################################
#
def fft_calc(data_vec):
    data_vec = butter_filt(data_vec)
    data_vec = data_vec*np.hanning(len(data_vec)) # hanning window
    N_fft = len(data_vec) # length of fft
    freq_vec = (float(samp_rate)*np.arange(0,int(N_fft/2)))/N_fft # fft frequency vector
    fft_data_raw = np.abs(np.fft.fft(data_vec)) # calculate FFT
    fft_data = fft_data_raw[0:int(N_fft/2)]/float(N_fft) # FFT amplitude scaling
    fft_data[1:] = 2.0*fft_data[1:] # single-sided FFT amplitude doubling
    return freq_vec,fft_data
##############################################
# Filtering Signal for Valid Bandpass
##############################################
#
def bandpass_coeffs():
    low_pt = frequency_bounds[0]/(0.5*samp_rate) # low freq cutoff relative to nyquist rate
    high_pt = frequency_bounds[1]/(0.5*samp_rate) # high freq cutoff relative to nyquist rate
    b,a = signal.butter(filt_order,[low_pt,high_pt],btype='band') # bandpass filter coeffs
    return b,a # return filter coefficients for bandpass

def butter_filt(data):
    b,a = bandpass_coeffs() # get filter coefficients
    data_filt = signal.lfilter(b,a,data) # data filter
    return data_filt
#
##############################################
# function for setting up pyserial
##############################################
#
def soundcard_finder(dev_indx=None,dev_name=None,dev_chans=1,dev_samprate=44100):
    ###############################
    # ---- look for USB sound card 
    audio = pyaudio.PyAudio() # create pyaudio instantiation
    for dev_ii in range(audio.get_device_count()): # loop through devices
        dev = audio.get_device_info_by_index(dev_ii)
        if len(dev['name'].split('USB'))>1: # look for USB device
            dev_indx = dev['index'] # device index
            dev_name = dev['name'] # device name
            dev_chans = dev['maxInputChannels'] # input channels
            dev_samprate = dev['defaultSampleRate'] # sample rate
            print('PyAudio Device Info - Index: {0}, '.format(dev_indx)+\
                  'Name: {0}, Channels: {1:2.0f}, '.format(dev_name,dev_chans)+\
                      'Sample Rate {0:2.0f}'.format(samp_rate))
    if dev_name==None:
        print("No WaWico USB Device Found")
        return None,None,None
    return audio,dev_indx,dev_chans # return pyaudio, USB dev index, channels
#
def pyserial_start():
    ##############################
    ### create pyaudio stream  ###
    # -- streaming can be broken down as follows:
    # -- -- format             = bit depth of audio recording (16-bit is standard)
    # -- -- rate               = Sample Rate (44.1kHz, 48kHz, 96kHz)
    # -- -- channels           = channels to read (1-2, typically)
    # -- -- input_device_index = index of sound device
    # -- -- input              = True (let pyaudio know you want input)
    # -- -- frmaes_per_buffer  = chunk to grab and keep in buffer before reading
    ##############################
    stream = audio.open(format = pyaudio_format,rate = samp_rate,channels = chans, \
                        input_device_index = dev_indx,input = True, \
                        frames_per_buffer=CHUNK)
    stream.stop_stream() # stop stream to prevent overload
    return stream

def pyserial_end():
    stream.close() # close the stream
    audio.terminate() # close the pyaudio connection
#
##############################################
# functions for plotting data
##############################################
#
def spec_plotter():
    ##########################################
    # ---- spectrogram plot
    fig,ax = plt.subplots(figsize=(12,8)) # create figure
    ax.set_yscale('log') # log-scale for better visualization
    ax.set_ylim(frequency_bounds) # set frequency limits
    ax.set_xlabel('Time [s]',fontsize=16)# frequency label
    ax.set_ylabel('Frequency [Hz]',fontsize=16) # amplitude label
    
    fig.canvas.draw() # draw 
    ax_bgnd = fig.canvas.copy_from_bbox(ax.bbox) # background for speedup
    spec1 = ax.pcolormesh(t_spectrogram,freq_array,fft_array,shading='auto') # plot
    fig.show() # show the figure
    return fig,ax,ax_bgnd,spec1

def plot_updater():
    ##########################################
    # ---- update spectrogram with new point
    fig.canvas.restore_region(ax_bgnd) # restore background
##    spec1.set_array(np.array(fft_array)[:-1,:-1].ravel()) # for shading='flat' 
    spec1.set_array(np.array(fft_array).ravel()) # for shading='gouraud'
    ax.draw_artist(spec1) # re-draw spectrogram
    fig.canvas.blit(ax.bbox) # blit
    fig.canvas.flush_events() # for plotting
    return spec1
#
##############################################
# function for grabbing data from buffer
##############################################
#
def data_grabber():
    stream.start_stream() # start data stream
    t_0 = datetime.datetime.now() # get datetime of recording start
    data,data_frames = [],[] # variables
    for frame in range(0,update_samples):
        # grab data frames from buffer
        stream_data = stream.read(CHUNK,exception_on_overflow=False)
        data_frames.append(stream_data) # append data
        data.append(np.frombuffer(stream_data,dtype=buffer_format)/((2**15)-1))
    stream.stop_stream()
    return data,data_frames,t_0
#
##############################################
# function for analyzing data
##############################################
#
def data_analyzer():
    data_array = []
    t_ii = 0.0
    for frame in data_chunks:
        freq_ii,fft_ii = fft_calc(frame) # calculate fft for chunk
        fft_ii/=np.sqrt(np.mean(np.power(frame,2.0)))
        freq_array.append(freq_ii) # append chunk freq data to larger array
        fft_array.append(fft_ii) # append chunk fft data to larger array
        t_vec_ii = np.arange(0,len(frame))/float(samp_rate) # time vector
        t_ii+=t_vec_ii[-1] 
        t_spectrogram.append(t_spectrogram[-1]) # time step for time v freq. plot
        data_array.extend(frame) # full data array
    t_vec = np.arange(0,len(data_array))/samp_rate # time vector for time series
    freq_vec,fft_vec = fft_calc(data_array) # fft of entire time series
    return t_vec,data_array,freq_vec,fft_vec,freq_array,fft_array,t_spectrogram

def corr_plot():
    #
    ###############################
    # Correlation Analysis between
    # Q and FFT data
    ###############################
    #
    x_vec = np.array(Q_corr_vec)
    y_vec = np.array(fft_corr_vec)
    y_vec_freq = np.array(freq_vec)

    xy_corr = []
    for ii in range(len(y_vec_freq)):
        xy_corr.append(np.sum((x_vec[:,ii]-np.mean(x_vec[:,ii]))*\
                              (y_vec[:,ii]-np.mean(y_vec[:,ii])))/\
                       (np.sqrt(np.sum(np.power(x_vec[:,ii]-np.mean(x_vec[:,ii]),2.0)))*\
                        np.sqrt(np.sum(np.power(y_vec[:,ii]-np.mean(y_vec[:,ii]),2.0)))))

    plt.style.use('ggplot')
    fig,ax = plt.subplots(figsize=(14,8))
    ax.scatter(y_vec_freq,xy_corr)
    ax.set_xscale('log')
    ax.set_xlim([1.0,samp_rate/2])
    ax.set_xlabel('Frequency [Hz]',fontsize=16)
    ax.set_ylabel(r'$\rho$',fontsize=16)
    return fig
#
##############################################
# Main Data Acquisition Procedure
##############################################
#   
if __name__=="__main__":
    #####################################
    # Mechanical Flow Meter Setup
    #####################################
    #
    counter = 0 # for counting and calculating frequency

    Q_prev = 0.0 # previous flow calculation (for total flow calc.) [L/s]

    conv_factor = 1.0/(5.5*60) # conversion factor to [L/s] from freq [1/s or Hz]
    vol_approx = 0.0 # initial approximation of volume [L]
    vol_prev   = 0.0 # for minimizing the prints to console
    
    #####################################
    # GPIO setup for mechanical interrupt
    #####################################
    #
    sensor_gpio = 23 # sensor GPIO pin
    gpio.setmode(gpio.BCM) # set for GPIO pin configuration
    gpio.setup(sensor_gpio,gpio.IN,pull_up_down=gpio.PUD_UP) # set interrupt
    #
    #####################################
    # Interrupt setup
    #####################################
    #
    gpio.add_event_detect(sensor_gpio,gpio.FALLING,callback=sensor_callback,
                          bouncetime=1) # setup interrupt for event detection 
    rpi_sig.signal(rpi_sig.SIGINT,signal_handler) # asynchronous interrupt handler
    #
    ################################
    # WaWiCo acquisition parameters
    ################################
    #
    CHUNK          = 2**12  # frames to keep in buffer between reads
    samp_rate      = 44100 # sample rate [Hz]
    pyaudio_format = pyaudio.paInt16 # 16-bit device
    buffer_format  = np.int16 # 16-bit for buffer
    #
    #############################
    # Find and Start Soundcard 
    #############################
    #
    audio,dev_indx,chans = soundcard_finder() # start pyaudio,get indx,channels
    if audio == None:
        sys.exit() # exit if no WaWiCo sound card is found
    #
    #############################
    # stream info and data saver
    #############################
    #
    stream = pyserial_start() # start the pyaudio stream
    time_window = 10 # seconds within spectrogram window
    window_samples =  int((samp_rate*time_window)/CHUNK) # chunks to record
    update_window = 0.1
    update_samples = int((samp_rate*update_window)/CHUNK)
    
    plot_bool = 0 # boolean for first plot
    #
    ##############################
    # Pre-allocations for plot
    ##############################
    #
    freq_array = (float(samp_rate)*np.arange(0,int(CHUNK/2)))/CHUNK
    t_spectrogram = np.arange(window_samples)*CHUNK/samp_rate
    t_spectrogram = [np.repeat(ii,len(freq_array)) for ii in t_spectrogram]
    freq_array = [freq_array for ii in range(0,np.shape(t_spectrogram[0])[0])]
    fft_array = list(np.zeros(np.shape(t_spectrogram)))
    #
    ##############################
    # Frequency Window Filtering
    ##############################
    #
    frequency_bounds = [500.0,10000.0] # low/high frequency cutoffs
    filt_order = 5
    #
    #####################################
    #
    ##############################
    # Main Loop
    ##############################
    #
    #####################################
    #
    fft_corr_vec,Q_corr_vec = [],[]
    print('Recording Data...')
    print('Press CTRL+C to Finish Recording and Plot The Resulting Correlation')
    while True:
        try:
            counter = 0 # reset counter
            t0 = time.time()
            # get audio data
            data_chunks,data_frames,t_0 = data_grabber() # grab the audio data

            # mechanical flow section
            t_elapsed = time.time()-t0
            Q = (conv_factor*(counter/t_elapsed)) # conversion to [Hz] then to [L/s]
            vol_approx+=(t_elapsed*((Q+Q_prev)/2.0)) # integrate over time for [L]
            
            Q_prev = float(Q) # set previous rate
##            print("Flow Rate: {0:2.3f}[L/s], Volume : {1:2.3f} L".format(Q,vol_approx))
            vol_prev = float(vol_approx)
            
            # audio analysis section
            t_vec,data,freq_vec,fft_data,\
                    freq_array,fft_array,t_spectrogram = data_analyzer() # analyze recording

            fft_corr_vec.append(fft_data)
            Q_corr_vec.append(np.repeat(Q,np.shape(freq_vec)))
            # uncomment below for visualizing the frequency spectrum over time
    ##        if np.shape(t_spectrogram)[0]>window_samples:
    ##            freq_array = freq_array[-window_samples:] # remove first point
    ##            fft_array = fft_array[-window_samples:] # remove first point
    ##            t_spectrogram = t_spectrogram[-window_samples:] # remove first point
    ##            if plot_bool:
    ##                spec1 = plot_updater() # update spectrogram
    ##            else:
    ##                fig,ax,ax_bgnd,spec1 = spec_plotter() # first plot allocating params
    ##                plot_bool = 1 # lets the loop know the first plot started

        except:
            print('Plotting Correlation...')
            pyserial_end() # close the stream/pyaudio connection
            fig = corr_plot()
            fig.savefig('wawico_mechanical_correlation.png',dpi=300,bbox_inches='tight',
                        facecolor='#FCFCFC')
            fig.savefig('./images/wawico_mechanical_correlation_white.png',dpi=300,bbox_inches='tight',
                        facecolor='#FFFFFF')
            plt.show()
            break

