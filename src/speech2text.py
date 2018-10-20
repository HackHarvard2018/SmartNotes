# Imports the Google Cloud client library
from google.cloud import speech_v1p1beta1 as speech
from google.cloud.speech_v1p1beta1 import enums
from google.cloud.speech_v1p1beta1 import types
from google.cloud import storage
import datetime

class Speech2Text:

    def speech2text(self, source_file_name):
        # Instantiates a client
        client = speech.SpeechClient()

        metadata = types.module.RecognitionMetadata()
        metadata.interaction_type = (speech.enums.RecognitionMetadata.InteractionType.DISCUSSION)
        metadata.recording_device_type = (speech.enums.RecognitionMetadata.RecordingDeviceType.SMARTPHONE)
        metadata.audio_topic = 'meeting'

        config = types.module.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.FLAC,
            sample_rate_hertz=44100,
            language_code='en-US',
            enable_automatic_punctuation=True,
            enable_speaker_diarization=True,
            diarization_speaker_count=2,
            use_enhanced=True,
            model='default',
            metadata=metadata
        )

        audio = types.module.RecognitionAudio(
            uri='gs://smartnotes/audio_clips/'+source_file_name
        )

        # Detects speech in the audio file
        response = client.long_running_recognize(config, audio)
        res = response.result(timeout=90)
        # results = res.results[-1]

        for result in res.results:
            print('Transcript: {}'.format(result.alternatives[0].transcript))
            print('Confidence: {}'.format(result.alternatives[0].confidence))

        return [result.alternatives[0].transcript for result in res.results]

    def upload_transcript(self, transcript, dest_file_name):
        storage_client = storage.Client()
        bucket = storage_client.get_bucket('smartnotes')
        blob = bucket.blob('transcripts/' + dest_file_name)
        data = ''.join(transcript)
        blob.upload_from_string(data)
        return blob.exists()

speech_client = Speech2Text()
results = speech_client.speech2text('test6.flac')
speech_client.upload_transcript(results, str(datetime.datetime.now()).replace(' ', '_') + '.txt')