"""App configuration for the news app."""
from django.apps import AppConfig
from django.core import management
from news.scripts.model_loader import ModelLoader


class NewsConfig(AppConfig):
    """App configuration for the news app."""
    name = "news"

    def ready(self):
        # Run the download_nltk_data management command when the app is ready
        management.call_command("download_nltk_data")

        print("Initial model loading....")
        model_loader = ModelLoader()  # wake up modules
        # this hard codeed url may cause problems in the future, but it's enough for now
        url = "https://www.thesun.co.uk/news/19747379/queen-elizabeth-dead-news/"

        print("Initial model loading finished.")
        print("Performing mock prediction...")

        try:
            print("Scraping...")
            scraped_data = model_loader.scraper.scrape(url)
            title = scraped_data["title"]
            print("Using NLP model...")
            model_loader.nlp.predict_on_text(title)
            print("Using LLM model...")
            model_loader.llm.predict(title)
            print("Using summarizer model...")
            summary = model_loader.summarizer(
                scraped_data["content"], max_length=200, min_length=40, do_sample=False
            )
            print("Using VertexAI model...")
            model_loader.vertex.run(scraped_data["title"], summary)
        except Exception as e:  # pylint: disable=broad-exception-caught
            print("Error in initialisation: ", e)
            print("The app starts normally, but there may be some problems.")
        print("Initialization finished.")
