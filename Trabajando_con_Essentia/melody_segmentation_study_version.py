import sys
import glob
import os
import numpy
from pylab import plot, show, figure, imshow
import matplotlib.pyplot as plt
import numpy as np
import essentia
from essentia.standard import MonoLoader, PredominantPitchMelodia, MonoWriter
# set plot sizes to something larger than default
plt.rcParams['figure.figsize'] = (15, 6)

sys.setrecursionlimit(20000)
###############################Melody detection#################################

# Create folder for segments

sample_rate = 44100
hS = 512
fS = 2048


# Extract the pitch curve
# PitchMelodia takes the entire audio signal as input (no frame-wise processing is required)


def audio_segments_generator(audio):
    pitch_extractor = PredominantPitchMelodia(frameSize=fS,
                                              hopSize=1024,
                                              filterIterations=3,
                                              # harmonic weighting parameter (weight decay ratio between two consequent harmonics, =1 for no decay)
                                              harmonicWeight=0.8,
                                              # spectral peak magnitude threshold (maximum allowed difference from the highest peak in dBs)
                                              magnitudeThreshold=40,
                                              guessUnvoiced=False,
                                              # the minimum allowed contour duration [ms]
                                              minDuration=10,
                                              numberHarmonics=20,
                                              timeContinuity=100,  # the maximum allowed gap duration for a pitch contour
                                              voiceVibrato=False,
                                              # allowed deviation below the average contour mean salience of all contours (fraction of the standard deviation)
                                              voicingTolerance=0.8,
                                              # 27.5625  pitch continuity cue (maximum allowed pitch change during 1 ms time period) [cents]
                                              pitchContinuity=27.5625,
                                              # 0.45 funcionó para bach partita de violin per-frame salience threshold factor (fraction of the highest peak salience in a frame))  # These are samples!!! To write in audio we need to use frames
                                              peakFrameThreshold=0.7)
    # Pitch is estimated on frames. Compute frame time positions
    pitch_values, _ = pitch_extractor(audio)
    prev_index = 0
    sample_indexes = []
    # Filter segments from data retrived
    for i in range(len(pitch_values)):
        num = pitch_values[i]
        if num > 0 and prev_index == 0:
            sample_indexes.append(i)
        prev_index = num
    # Convert the sample_indexes into samples
    sample_list = [n*hS for n in sample_indexes]
    audioSize = audio.size
    sample_list.insert(0, 0)
    sample_list.append(audioSize)
    return sample_list


# Load audio files from folder
def concat_audio(out_dir, frame_count, segment_count, segment_list, audio_list, file_index, output_data):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    print("frame, segment", frame_count, segment_count, file_index)
    if frame_count < len(segment_list[segment_count])-1:
        startFrame = segment_list[segment_count][frame_count]
        endFrame = segment_list[segment_count][frame_count + 1]
        filename = os.path.abspath(
            os.path.join(out_dir, str(file_index)+".wav"))
        length = endFrame - startFrame
        if length > 0:
            output_data.append(
                {"index": file_index,
                 "path": filename,
                 "start": startFrame,
                 "end": endFrame,
                 "length": length,
                 "length-seconds": (endFrame - startFrame)/sample_rate,
                 "sample_rate": sample_rate})
            MonoWriter(filename=filename,  format='wav', sampleRate=sample_rate)(
                audio_list[segment_count][startFrame:endFrame])
        concat_audio(out_dir, frame_count+1, segment_count,
                     segment_list, audio_list, file_index+1, output_data)
    else:
        if segment_count < len(segment_list)-1:
            concat_audio(out_dir, 0, segment_count+1, segment_list,
                         audio_list, file_index, output_data)
    return output_data


def process_file(out_dir, filename):
    allSampleList = []
    allAudio = []
    audio = MonoLoader(filename=filename)()
    sampleSegments = audio_segments_generator(audio)
    allSampleList.append(sampleSegments)
    allAudio.append(audio)
    files = concat_audio(out_dir, 0, 0, allSampleList, allAudio, 0, [])
    return files
