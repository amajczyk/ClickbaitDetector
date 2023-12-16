from django.core.management.base import BaseCommand
import nltk

class Command(BaseCommand):
    help = 'Download NLTK data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Downloading NLTK data...'))
        nltk.download('punkt')
        nltk.download('wordnet')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('words')
        nltk.download('stopwords')
        self.stdout.write(self.style.SUCCESS('NLTK data downloaded successfully.'))