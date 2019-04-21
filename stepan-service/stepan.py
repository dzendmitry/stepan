import pickle
import threading
import queue
import datetime
import logging

from keras.models import load_model
import numpy as np
import librosa
from scipy import signal
from enum import Enum

import refresher
import replier
from replier import Commands as Classes

logger = logging.getLogger('stepan')


class States(Enum):
    WAIT_STEPAN = 1
    WAIT_COMMAND = 2


# params
min_message_length = 60000  # the name of STEPAN
min_message_in_samples = int(min_message_length / 2)
silent_stepans = 2
state = States.WAIT_STEPAN

# pre-def
q = queue.Queue(1024)
one_class_model_file = 'models/one_class_model_for_5_classes.pkl'
stepan_model_file = 'models/stepan_model_5_classes_(noise,stepan,catalog,kuber,item)_acc_84.hdf5'

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
        logger.info('current_spectrogram {}'.format(len(self.current_spectrogram)))

    def __iter__(self):
        return self

    def __next__(self):
        while self.current_pos_in_spectrogram + self.num_steps < len(self.current_spectrogram):
            x = np.zeros((self.batch_size, self.num_steps, self.freq))
            for i in range(self.batch_size):
                if self.current_pos_in_spectrogram + self.num_steps >= len(self.current_spectrogram):
                    break
                x[i, :, :] = self.current_spectrogram[
                             self.current_pos_in_spectrogram:self.current_pos_in_spectrogram + self.num_steps, :]
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


def extract_audio_features(sound_data):
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


def is_familiar_command(data_predicted, threshold=0.8):
    familiar_count = float(len(data_predicted[data_predicted == 1]))
    logger.info('familiar_count {}'.format(familiar_count))
    all_data_count = float(len(data_predicted))
    logger.info('all_data_count {}'.format(all_data_count))
    familiar_percent = familiar_count / all_data_count
    logger.info('familiar_percent {}, threshold {}'.format(familiar_percent, threshold))
    if familiar_percent >= threshold:
        return True
    return False


def is_it_stepan(classes_counters):
    if Classes.STEPAN.value in classes_counters:
        if classes_counters[Classes.STEPAN.value] >= 2:
            return True
    return False


def parse_command(classes_counters):
    if len(classes_counters) == 0:
        return Classes.NOISE, False
    if Classes.NOISE.value in classes_counters:
        del classes_counters[Classes.NOISE.value]
    logger.info("classes_counters: {}".format(classes_counters))
    command = Classes.NOISE
    try:
        command = max(classes_counters, key=classes_counters.get)
    except:
        return Classes.NOISE, False
    if command != Classes.STEPAN.value:
        return command, True
    return command, False


def analyze_predictions(predictions):
    """
    TODO: a lot of heuristics. try to rewrite it using some smart algo
    """
    global state

    classes_counters = dict()
    for prediction in predictions:
        last_chunk_class = None
        for chunk_class in prediction:
            if last_chunk_class is None:
                last_chunk_class = chunk_class
                continue
            if chunk_class == last_chunk_class:
                if chunk_class not in classes_counters:
                    classes_counters[chunk_class] = 2
                else:
                    classes_counters[chunk_class] += 1
            last_chunk_class = chunk_class

    if state == States.WAIT_STEPAN and is_it_stepan(classes_counters):
        logger.info("Got STEPAN command")
        replier.q.put(Classes.STEPAN, block=False)
        state = States.WAIT_COMMAND
        refresher.q.put(datetime.datetime.now())
        return

    if state == States.WAIT_COMMAND:
        command, ok = parse_command(classes_counters)
        if ok:
            logger.info("Got command {}".format(command))
            replier.q.put(Classes(command), block=False)
            state = States.WAIT_STEPAN
            replier.q.put(Classes.STATE_SKIPPED, block=False)


def run():
    global one_class_svm_model
    global stepan_model

    while True:
        sound_chunk = q.get()
        if len(sound_chunk) % 2 != 0:
            sound_chunk = sound_chunk[:-1]
        sound_data = np.frombuffer(sound_chunk, dtype=np.int16)
        logger.info('sound_data numpy: {}'.format(sound_data.shape))
        logger.info('sound_chunk len: {}'.format(len(sound_chunk)))
        audio_features = extract_audio_features(sound_data.astype(np.float32))
        is_familiar = is_familiar_command(one_class_svm_model.predict(audio_features))
        logger.info('is familiar command: {}'.format(is_familiar))
        if is_familiar:
            predictions = []
            for chunk in StepanBatchGenerator(sound_data):
                prediction = stepan_model.predict_proba(chunk)
                logger.info(prediction)
                predicted = np.argmax(prediction, axis=1)
                logger.info('predicted: {}'.format( predicted))
                predictions.append(predicted)
            analyze_predictions(predictions)


def start():
    stepan_thread = threading.Thread(target=run)
    stepan_thread.start()
