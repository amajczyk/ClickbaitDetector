import datetime
import os

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from django.db import IntegrityError
from django.core.exceptions import ValidationError

from django.conf import settings


from .models import Article


# python manage.py test news
# https://docs.djangoproject.com/en/4.2/intro/tutorial05/

print('Testing news app...')
print('Time now: ', timezone.now())




import unittest
from unittest.mock import patch
from news.scripts.scraping import Scraper  # Replace with your actual module name
from news.scripts.nlp import load_predictive_model, Word2VecModel, predict_on_text, return_best_model
from news.scripts.llm import LocalLLM



ABCNEWS_NOT_CLICKBAIT = 'https://abcnews.go.com/Politics/joe-biden-apparent-winner-presidency/story?id=73981165'
CBSNEWS_NOT_CLICKBAIT = 'https://www.cbsnews.com/news/joe-biden-wins-2020-election-46th-president-united-states/'
THESUN_NOT_CLICKBAIT = 'https://www.thesun.co.uk/news/19747379/queen-elizabeth-dead-news/'
CBSSPORTS_NOT_CLICKBAIT = 'https://www.cbssports.com/nba/news/p-j-tucker-says-theres-not-enough-basketballs-on-the-planet-for-clippers/'
CLICKBAIT_TITLE = "10 Signs Your Partner Is Cheating - Don't Ignore #7!"
NOT_CLICKBAIT_TITLE = "Joe Biden projected to win presidency in deeply divided nation"




class TestScraper(TestCase):
    def setUp(self):
        # Set up any necessary resources or configurations for tests
        config_path = os.path.join(settings.BASE_DIR, 'news', 'config', 'site_variables_dict')
        self.scraper = Scraper(config_path)


    def test_get_site_variables_dict(self):
        site_variables_dict = self.scraper.site_variables_dict
        self.assertIsInstance(site_variables_dict, dict)
        self.assertIn("cbsnews", site_variables_dict)
        self.assertIn("thesun", site_variables_dict)
        self.assertIn("abcnews", site_variables_dict)
        

    def test_scrape_article_urls(self):
        # Test scraping urls from the main website
        result= self.scraper.scrape_article_urls(self.scraper.site_variables_dict['thesun']['main'])
        self.assertGreater(len(result), 0)
        
        result= self.scraper.scrape_article_urls(self.scraper.site_variables_dict['cbsnews']['main'])
        self.assertGreater(len(result), 0)
        
        result= self.scraper.scrape_article_urls(self.scraper.site_variables_dict['abcnews']['main'])
        self.assertGreater(len(result), 0)


    def test_discern_website_from_url(self):
        result = self.scraper.discern_website_from_url(ABCNEWS_NOT_CLICKBAIT)
        self.assertEqual(result["source_site"], "ABC News")
        
        result = self.scraper.discern_website_from_url(CBSNEWS_NOT_CLICKBAIT)
        self.assertEqual(result["source_site"], "CBS News")

        result = self.scraper.discern_website_from_url(THESUN_NOT_CLICKBAIT)
        self.assertEqual(result["source_site"], "The Sun UK")
        
        result = self.scraper.discern_website_from_url(CBSSPORTS_NOT_CLICKBAIT)
        self.assertEqual(result["source_site"], "CBS News")

    def test_scrape(self):
        result = self.scraper.scrape(THESUN_NOT_CLICKBAIT)

        self.assertIsInstance(result, dict)
        self.assertIn("title", result)
        self.assertIsNotNone(result["title"])
        self.assertIn("content", result)
        self.assertIsNotNone(result["content"])
        self.assertIn("source_site", result)
        self.assertIsNotNone(result["source_site"])


class NLPPredictorTests(TestCase):
    def test_predict_on_text(self):
        # Test the model on a non-clickbait title
        predictive_model_path = os.path.join(settings.BASE_DIR, 'news', 'predictive_models', 'catboost_model.pkl')
        predictive_model = load_predictive_model(predictive_model_path)
        model_settings_path = os.path.join(settings.BASE_DIR, 'news', 'config', 'model_settings.json')
        model_w2v_settings = return_best_model(path=model_settings_path)
        model_path = os.path.join(settings.BASE_DIR, 'news', 'word2vec_models', model_w2v_settings['model_path'])
        model_w2v = Word2VecModel(model_w2v_settings,model_path)
        proba_cutoff = 0.5
        result = predict_on_text(predictive_model, model_w2v, CLICKBAIT_TITLE)
        self.assertGreater(result[0][1], proba_cutoff)
        
        # Test the model on a non-clickbait title
        result = predict_on_text(predictive_model, model_w2v, NOT_CLICKBAIT_TITLE)
        self.assertLess(result[0][1], proba_cutoff)
        
        
# class LLMPredictorTests(TestCase):
    
#     def test_predict(self):
#         llm = LocalLLM()
#         result = llm.predict(CLICKBAIT_TITLE)
#         self.assertEqual(result, 1)
        
#         result = llm.predict(NOT_CLICKBAIT_TITLE)
#         self.assertEqual(result, 0)
    


class ArticleModelTests(TestCase):  
    
    def test_default_values(self):
        """
        Test that default values are set for clickbait_decision fields.
        """
        new_article = Article.objects.create(title="Test Article", content_summary="Summary")
        self.assertEqual(new_article.clickbait_decision_NLP, -1)
        self.assertEqual(new_article.clickbait_decision_LLM, -1)
        self.assertEqual(new_article.clickbait_decision_VERTEX, -1)
        self.assertEqual(new_article.clickbait_decision_final, -1)
    
    def test_was_scraped_within_the_last_24h(self):
        """
        was_scraped_today() should return True for articles whose scraped_date
        is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59)
        recent_article = Article(scraped_date=time)
        self.assertIs(recent_article.was_scraped_today(), True)
    
    def test_was_scraped_later_than_the_last_24h(self):
        """
        was_scraped_today() should return False for articles whose scraped_date
        is outside the last day.
        """
        time = timezone.now() - datetime.timedelta(days=1, minutes=1)
        old_article = Article(scraped_date=time)
        self.assertIs(old_article.was_scraped_today(), False)

    
    
    def test_valid_decision_values(self):
        """
        Test that the model allows valid decision values for NLP and LLM fields.
        """
        valid_decisions = [-1, 0, 1]
        for decision in valid_decisions:
            article = Article.objects.create(
                title="Test Article",
                content_summary="Summary",
                clickbait_decision_NLP=decision,
                clickbait_decision_LLM=decision,
            )
            self.assertEqual(article.clickbait_decision_NLP, decision)
            self.assertEqual(article.clickbait_decision_LLM, decision)

    def test_invalid_decision_values(self):
        """
        Test that the model raises IntegrityError for invalid decision values.
        """

        decision = -2
        with self.assertRaises(IntegrityError):
            Article.objects.create(
                title="Test Article",
                content_summary="Summary",
                clickbait_decision_NLP=decision,
                clickbait_decision_LLM = decision,
                clickbait_decision_VERTEX = decision,
                clickbait_decision_final = decision
            )


