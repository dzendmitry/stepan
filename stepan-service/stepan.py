import pickle
import threading
import queue

from keras.models import load_model
import numpy as np
import librosa
from scipy import signal

min_message_length = 60000 # the name of STEPAN
min_message_in_samples = int(min_message_length / 2)
silent_stepans = 5

# pre-def
q = queue.Queue(1024)
one_class_model_file = 'models/one_class_model.pkl'
stepan_model_file = 'models/stepan_4_classes_acc_89.hdf5'

# librosa params
sampling_rate = 44100
hop_length = 512
n_mfcc = 13

# models
one_class_svm_model = None
stepan_model = None

def get_spectrogram_of_data(samples, sample_rate=44100):
    frequencies, times, spectrogram = signal.spectrogram(samples, sample_rate)
    return spectrogram.T

class StepanBatchGenerator:

    def __init__(self, data, num_steps=60, batch_size=8, skip_steps=30, freq=129):
        self.data = data
        self.num_steps = num_steps
        self.batch_size = batch_size
        self.skip_steps = skip_steps
        self.freq = freq
        self.current_pos_in_spectrogram = 0
        self.current_spectrogram = get_spectrogram_of_data(self.data)
        print('current_spectrogram', len(self.current_spectrogram))

    def __iter__(self):
        return self

    def __next__(self):
        while self.current_pos_in_spectrogram + self.num_steps < len(self.current_spectrogram):
            x = np.zeros((self.batch_size, self.num_steps, self.freq))
            for i in range(self.batch_size):
                if self.current_pos_in_spectrogram + self.num_steps >= len(self.current_spectrogram):
                    break
                x[i, :, :] = self.current_spectrogram[self.current_pos_in_spectrogram:self.current_pos_in_spectrogram + self.num_steps, :]
                self.current_pos_in_spectrogram += self.skip_steps
            return x
        raise StopIteration

def init_models():
    global one_class_svm_model
    global stepan_model
    one_class_svm_model = pickle.load(open(one_class_model_file, 'rb'))
    stepan_model = load_model(stepan_model_file)
    stepan_model._make_predict_function()
    if one_class_svm_model is None or stepan_model is None:
        raise Exception("one class svm model OR stepan model are None")

def extract_audio_features(sound_data, sampling_rate, hop_length):
    mfcc = librosa.feature.mfcc(y=sound_data, sr=sampling_rate, hop_length=hop_length, n_mfcc=n_mfcc)
    spectral_center = librosa.feature.spectral_centroid(y=sound_data, sr=sampling_rate, hop_length=hop_length)
    chroma = librosa.feature.chroma_stft(y=sound_data, sr=sampling_rate, hop_length=hop_length)
    spectral_contrast = librosa.feature.spectral_contrast(y=sound_data, sr=sampling_rate, hop_length=hop_length)

    timeseries_length = mfcc.T.shape[0]
    features = np.zeros((timeseries_length, 33), dtype=np.float64)

    features[:, 0:13] = mfcc.T
    features[:, 13:14] = spectral_center.T
    features[:, 14:26] = chroma.T
    features[:, 26:33] = spectral_contrast.T

    features = features / np.linalg.norm(features)

    return features

def get_spectrogram(samples, sample_rate=44100):
    frequencies, times, spectrogram = signal.spectrogram(samples, sample_rate)
    return spectrogram.T

def is_familiar_command(data_predicted, threshold=0.7):
    familiar_count = float(len(data_predicted[data_predicted == 1]))
    print('familiar_count', familiar_count)
    all_data_count = float(len(data_predicted))
    print('all_data_count', all_data_count)
    familiar_percent = familiar_count / all_data_count
    print('familiar_percent', familiar_percent, ' threshold ', threshold)
    if familiar_percent >= threshold:
        return True
    return False

def run():
    global one_class_svm_model
    global stepan_model

    while True:
        sound_chunk = q.get()
        if len(sound_chunk) % 2 != 0:
            sound_chunk = sound_chunk[:-1]
        sound_data = np.frombuffer(sound_chunk, dtype=np.int16)
        print('sound_data numpy: ', sound_data.shape)
        print('sound_chunk len: ', len(sound_chunk))
        audio_features = extract_audio_features(sound_data.astype(np.float32), sampling_rate, hop_length)
        is_familiar = is_familiar_command(one_class_svm_model.predict(audio_features))
        print('is familiar command: ', is_familiar)
        if is_familiar:
            for chunk in StepanBatchGenerator(sound_data):
                prediction = stepan_model.predict_proba(chunk)
                print(prediction)
                predicted = np.argmax(prediction, axis=1)
                print('predicted: ', predicted)


def start():
    stepan_thread = threading.Thread(target=run)
    stepan_thread.start()