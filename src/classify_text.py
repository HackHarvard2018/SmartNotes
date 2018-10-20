
from google.cloud import language_v1beta2 as language
from google.cloud.language_v1beta2 import enums
from google.cloud.language_v1beta2 import types
from google.cloud import storage

class ClassifyText:

    def text_classifier(self):
        text_client = language.LanguageServiceClient()
        text = ''

    def download_transcript(self):
        storage_client = storage.Client()
        bucket = storage_client.get_bucket('smartnotes')
        blob = bucket.list_blobs(prefix='transcripts/')