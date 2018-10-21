import io
import time
import math
import wave
import audioop
import pyaudio
from collections import deque
from google.cloud import storage

class SpeechRecord:
    """PyAudio example: Record a few seconds of audio and save to a WAVE file."""

    LANG_CODE = 'en-US'     # Language to use
    FLAC_CONV = 'flac -f'   # WAV to FLAC converter (flac is available on Linux)
    GOOGLE_SPEECH_URL = 'https://www.google.com/speech-api/v1/recognize?xjerr=1&client=chromium&pfilter=2&lang=%s&maxresults=6' % (LANG_CODE)
    GOOGLE_BUCKET_NAME = 'smartnotes'

    # Microphone stream configs
    FORMAT = pyaudio.paInt16

    CHANNELS = 1

    CHUNK = 1024        # Bytes of data to read each time

    RATE = 44100        # Sampling rate in Hz

    THRESHOLD = 1750    # The threshold intensity that defines silence
                        # and noise signal (a value lower than THRESHOLD is silence).

    SILENCE_LIMIT = 3   # Silence limit in seconds. The max amount of seconds where
                        # only silence is recorded. When this time passes the
                        # recording finishes and the file is delivered.

    PREV_AUDIO = 0.5    # Previous audio (in seconds) to prepend. When noise
                        # is detected, how much of previously recorded audio is
                        # prepended. This helps to prevent chopping the beggining
                        # of the phrase.

    def audio_int(self, num_samples=50):
        """
        Gets average audio intensity of your mic sound. You can use it to get
        average intensities while you're talking and/or silent. The average
        is the avg of the 20% largest intensities recorded.
        """

        print ('Getting intensity values from mic.')
        p = pyaudio.PyAudio()

        stream = p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK)

        values = [math.sqrt(abs(audioop.avg(stream.read(self.CHUNK), 4))) for x in range(num_samples)]
        values = sorted(values, reverse=True)
        r = sum(values[:int(num_samples * 0.2)]) / int(num_samples * 0.2)
        print ('Finished: Average audio intensity is', r)

        stream.stop_stream()
        stream.close()
        p.terminate()
        return r


    def listen_for_speech(self, threshold=THRESHOLD, num_phrases=3):
        """
        Listens to Microphone, extracts phrases from it and sends it to
        Google's TTS service and returns response. a "phrase" is sound
        surrounded by silence (according to threshold). num_phrases controls
        how many phrases to process before finishing the listening process
        (-1 for infinite).
        """

        # Open stream
        p = pyaudio.PyAudio()

        stream = p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK)

        print ('Listening for a voice.')
        audio2send = []
        cur_data = ''

        rel = self.RATE // self.CHUNK
        slid_win = deque(maxlen=self.SILENCE_LIMIT * rel)
        prev_audio = deque(maxlen=int(self.PREV_AUDIO * rel))

        started = False
        response = []

        while num_phrases == -1 or num_phrases > 0:
            cur_data = stream.read(self.CHUNK)
            slid_win.append(math.sqrt(abs(audioop.avg(cur_data, 4))))

            if sum([x > self.THRESHOLD for x in slid_win]) > 0:
                if not started:
                    print ('Starting to record phrase.')
                    started = True
                audio2send.append(cur_data)
            elif started:
                print ('Finished recording phrase.')
                # The limit was reached, finish capture and deliver.
                filename = self.upload_speech_gs(list(prev_audio) + audio2send, p)
                # Send file to Google and get response
                # r = stt_google_wav(filename)
                # Reset all
                started = False
                slid_win = deque(maxlen=self.SILENCE_LIMIT * rel)
                prev_audio = deque(maxlen=int(0.5 * rel))
                audio2send = []
                num_phrases -= 1
                print ('Listening for a voice.')
            else:
                prev_audio.append(cur_data)

        print ('Done listening.')
        stream.close()
        p.terminate()

        return response


    def upload_speech_gs(self, data, p):
        """Saves mic data to WAV file on Google Cloud Storage. Returns path of saved file."""

        wf_name = 'speech_' + str(time.time()) + '.wav'
        bucket = storage.Client().get_bucket(self.GOOGLE_BUCKET_NAME)
        blob = bucket.blob('audio_clips/' + wf_name)

        wf_buffer = io.BytesIO()
        with wave.open(wf_buffer, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(data))

            wf_buffer.seek(0)
            blob.upload_from_string(data=wf_buffer.read(), content_type='audio/wav')

            wf.close()
            wf_buffer.close()

        return wf_name


    def stt_google_wav(self, audio_fname):
        """
        Sends audio file (audio_fname) to Google's text to speech
        service and returns service's response. We need a FLAC
        converter if audio is not FLAC (check FLAC_CONV).
        """

        print ('Sending ', audio_fname)
        # Convert to flac first
        filename = audio_fname
        del_flac = False
        if 'flac' not in filename:
            del_flac = True
            print ('Converting to flac.')
            print (self.FLAC_CONV + filename)
            os.system(self.FLAC_CONV + ' ' + filename)
            filename = filename.split('.')[0] + '.flac'

        f = open(filename, 'rb')
        flac_cont = f.read()
        f.close()

        # Headers
        hdrs = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7',
            'Content-type': 'audio/x-flac; rate=16000'
        }

        req = urllib2.Request(self.GOOGLE_SPEECH_URL, data=flac_cont, headers=hdrs)
        print ('Sending request to Google TTS.')
        try:
            p = urllib2.urlopen(req)
            response = p.read()
            res = eval(response)['hypotheses']
        except:
            print ('Couldn\'t parse service response.')
            res = None

        if del_flac:
            os.remove(filename)  # Remove temp file

        return res

SpeechRecord().listen_for_speech()  # listen to mic.
