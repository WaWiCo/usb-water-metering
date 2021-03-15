##############################################
# Frequency Response of WaWiCo USB Sound Card 
#
# -- by WaWiCo 2021
# 
##############################################
#
import pyaudio
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np
import time,wave,datetime,os,csv,sys

##############################################
# function for FFT
##############################################
#
def fft_calc(data_vec):
    data_vec = data_vec*np.hanning(len(data_vec)) # hanning window
    N_fft = len(data_vec) # length of fft
    freq_vec = (float(samp_rate)*np.arange(0,int(N_fft/2)))/N_fft # fft frequency vector
    fft_data_raw = np.abs(np.fft.fft(data_vec)) # calculate FFT
    fft_data = fft_data_raw[0:int(N_fft/2)]/float(N_fft) # FFT amplitude scaling
    fft_data[1:] = 2.0*fft_data[1:] # single-sided FFT amplitude doubling
    return freq_vec,fft_data
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
def plotter():
    ##########################################
    # ---- time series and full-period FFT
    plt.style.use('ggplot')
    fig,ax = plt.subplots(figsize=(12,8)) # create figure
    ax.set_xscale('log') # log-scale for better visualization
    ax.set_yscale('log') # log-scale for better visualization
    ax.set_xlabel('Frequency [Hz]',fontsize=16)# frequency label
    ax.set_ylabel('Amplitude',fontsize=16) # amplitude label
    
    fig.canvas.draw()
    ax_bgnd = fig.canvas.copy_from_bbox(ax.bbox)
    line1, = ax.plot(freq_vec,fft_data)
    fig.show()
    return fig,ax,ax_bgnd,line1

def plot_updater():
    ##########################################
    # ---- time series and full-period FFT
    fig.canvas.restore_region(ax_bgnd)
    line1.set_ydata(fft_data)
    ax.draw_artist(line1)
    fig.canvas.blit(ax.bbox)
    fig.canvas.flush_events()
    return line1
#
##############################################
# function for grabbing data from buffer
##############################################
#
def data_grabber():
    stream.start_stream() # start data stream
    t_0 = datetime.datetime.now() # get datetime of recording start
    data,data_frames = [],[] # variables
    for frame in range(0,int((samp_rate*record_length)/CHUNK)):
        # grab data frames from buffer
        stream_data = stream.read(CHUNK,exception_on_overflow=False)
        data_frames.append(stream_data) # append data
        data.append(np.frombuffer(stream_data,dtype=buffer_format)/((2**15)-1))
    return data,data_frames,t_0
#
##############################################
# function for analyzing data
##############################################
#
def data_analyzer():
    freq_array,fft_array = [],[]
    t_spectrogram = []
    data_array = []
    t_ii = 0.0
    for frame in data_chunks:
        freq_ii,fft_ii = fft_calc(frame) # calculate fft for chunk
        freq_array.append(freq_ii) # append chunk freq data to larger array
        fft_array.append(fft_ii) # append chunk fft data to larger array
        t_vec_ii = np.arange(0,len(frame))/float(samp_rate) # time vector
        t_ii+=t_vec_ii[-1] 
        t_spectrogram.append(t_ii) # time step for time v freq. plot
        data_array.extend(frame) # full data array
    t_vec = np.arange(0,len(data_array))/samp_rate # time vector for time series
    freq_vec,fft_vec = fft_calc(data_array) # fft of entire time series
    return t_vec,data_array,freq_vec,fft_vec,freq_array,fft_array,t_spectrogram
#
##############################################
# Save data as .wav file and .csv file
##############################################
#
def data_saver(t_0):
    data_folder = './data/' # folder where data will be saved locally
    if os.path.isdir(data_folder)==False:
        os.mkdir(data_folder) # create folder if it doesn't exist
    filename = datetime.datetime.strftime(t_0,
                                          '%Y_%m_%d_%H_%M_%S_pyaudio') # filename based on recording time
    wf = wave.open(data_folder+filename+'.wav','wb') # open .wav file for saving
    wf.setnchannels(chans) # set channels in .wav file 
    wf.setsampwidth(audio.get_sample_size(pyaudio_format)) # set bit depth in .wav file
    wf.setframerate(samp_rate) # set sample rate in .wav file
    wf.writeframes(b''.join(data_frames)) # write frames in .wav file
    wf.close() # close .wav file
    return filename
#
##############################################
# Main Data Acquisition Procedure
##############################################
#   
if __name__=="__main__":
    #
    ###########################
    # acquisition parameters
    ###########################
    #
    CHUNK          = 4096  # frames to keep in buffer between reads
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
    record_length =  float(CHUNK)/float(samp_rate) # seconds to record
    plot_bool = 0 # boolean for first plot
    #
    while True:
        try:
            data_chunks,data_frames,t_0 = data_grabber() # grab the data
##            data_saver(t_0) # save the data as a .wav file
            #
            ###########################
            # analysis section
            ###########################
            #
            t_vec,data,freq_vec,fft_data,\
                    freq_array,fft_array,t_spectrogram = data_analyzer() # analyze recording
            fft_data/=np.sqrt(np.mean(np.power(data,2.0)))
            if plot_bool:
                line1 = plot_updater() # update frequency plot
            else:
                fig,ax,ax_bgnd,line1 = plotter() # first plot allocating params
                plot_bool = 1 # lets the loop know the first plot started
        except:
            break
            continue
        
    pyserial_end() # close the stream/pyaudio connection
