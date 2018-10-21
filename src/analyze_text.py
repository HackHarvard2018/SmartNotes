
from google.cloud import language_v1beta2 as language
from google.cloud.language_v1beta2 import enums
from google.cloud.language_v1beta2 import types
from google.cloud import storage
import six

class AnalyzeText:
    def __init__(self):
        self.text_client = language.LanguageServiceClient()
        self.storage_client = storage.Client()

    def text_classifier(self, input_str=None):
        if input_str:
            if isinstance(input_str, six.binary_type):
                input_str = input_str.decode('utf-8')
            doc = types.module.Document(
                content=input_str.encode('utf-8'),
                type=enums.Document.Type.PLAIN_TEXT
            )
        else:
            doc = types.module.Document(
                gcs_content_uri=self.get_transcript_uri(),
                type=enums.Document.Type.PLAIN_TEXT
            )
        return self.text_client.classify_text(doc)

    def text_sentiment(self):
        doc = types.module.Document(
            gcs_content_uri=self.get_transcript_uri(),
            type=enums.Document.Type.PLAIN_TEXT
        )
        return self.text_client.analyze_entity_sentiment(doc)

    def get_transcript_uri(self):
        bucket = self.storage_client.get_bucket('smartnotes')
        source_file = sorted([blob.name for blob in bucket.list_blobs(prefix='transcripts/')])[-1]
        return 'gs://smartnotes/' + source_file

text_analyzer = AnalyzeText()
categories = text_analyzer.text_classifier().categories
entities = text_analyzer.text_sentiment().entities
# text_classes = text_analyzer.text_classifier('Google, headquartered in Mountain View, unveiled the new Android phone at the Consumer Electronic Show.  Sundar Pichai said in his keynote that users love their new Android phones.')

for category in categories:
    print('=' * 20)
    print('Name: {}'.format(category.name.replace('/', '')))
    print('Confidence: {}'.format(category.confidence))

for entity in entities:
    print('=' * 20)
    print('Name: {}'.format(entity.name))
    print('Salience: {}'.format(entity.salience))