import os

from django.apps import AppConfig
from news.scripts.model_loader import ModelLoader


class NewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'news'

    
    def __init__(self, app_name, app_module):
        super().__init__(app_name, app_module)
    
    def ready(self):
        # Run the download_nltk_data management command when the app is ready
        from django.core import management
        management.call_command('download_nltk_data')

        print('Initial model loading....')
        model_loader = ModelLoader()
 

 
