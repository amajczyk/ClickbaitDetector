"""Tests for the news app."""
import datetime
import os
from dataclasses import asdict
from typing import Optional
from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from django.conf import settings

from google.auth import default


from news.vertex.cloud.vertex_connection import VertexAI, ModelName
from news.vertex.configs.config import Config
from news.scripts.scraping import Scraper
from news.scripts.nlp import NLP
from news.scripts.llm import LocalLLM

from .models import Article


# pylint: disable=line-too-long
ABCNEWS_NOT_CLICKBAIT = "https://abcnews.go.com/Politics/joe-biden-apparent-winner-presidency/story?id=73981165"
CBSNEWS_NOT_CLICKBAIT = "https://www.cbsnews.com/news/joe-biden-wins-2020-election-46th-president-united-states/"
THESUN_NOT_CLICKBAIT = (
    "https://www.thesun.co.uk/news/19747379/queen-elizabeth-dead-news/"
)
CBSSPORTS_NOT_CLICKBAIT = "https://www.cbssports.com/nba/news/p-j-tucker-says-theres-not-enough-basketballs-on-the-planet-for-clippers/"
CLICKBAIT_TITLE = "10 Signs Your Partner Is Cheating - Don't Ignore #7!"
NOT_CLICKBAIT_TITLE = "Hertz is selling Teslas for as little as $21,000, as it offloads the pricey EVs from its rental fleet"
# pylint: enable=line-too-long

class TestScraper(TestCase):
    """Test the Scraper class."""
    def setUp(self):
        # Set up any necessary resources or configurations for tests
        # python manage.py test news
        # https://docs.djangoproject.com/en/4.2/intro/tutorial05/
        config_path = os.path.join(
            settings.BASE_DIR, "news", "config", "site_variables_dict"
        )
        print("Testing news app...")
        print("Time now: ", timezone.now())
        self.scraper = Scraper(config_path)

    def test_get_site_variables_dict(self):
        """Test that the site_variables_dict is a dictionary and contains the
        expected keys.
        """
        site_variables_dict = self.scraper.site_variables_dict
        self.assertIsInstance(site_variables_dict, dict)
        self.assertIn("cbsnews", site_variables_dict)
        self.assertIn("thesun", site_variables_dict)
        self.assertIn("abcnews", site_variables_dict)

    def test_scrape_article_urls(self):
        """Test that the scrape_article_urls() method returns a list of
        strings.
        """
        # Test scraping urls from the main website
        result = self.scraper.scrape_article_urls(
            self.scraper.site_variables_dict["thesun"]["main"]
        )
        self.assertGreater(len(result), 0)

        result = self.scraper.scrape_article_urls(
            self.scraper.site_variables_dict["cbsnews"]["main"]
        )
        self.assertGreater(len(result), 0)

        result = self.scraper.scrape_article_urls(
            self.scraper.site_variables_dict["abcnews"]["main"]
        )
        self.assertGreater(len(result), 0)

    def test_discern_website_from_url(self):
        """Test that the discern_website_from_url() method returns a dictionary
        with the expected keys.
        """
        result = self.scraper.discern_website_from_url(ABCNEWS_NOT_CLICKBAIT)
        self.assertEqual(result["source_site"], "ABC News")

        result = self.scraper.discern_website_from_url(CBSNEWS_NOT_CLICKBAIT)
        self.assertEqual(result["source_site"], "CBS News")

        result = self.scraper.discern_website_from_url(THESUN_NOT_CLICKBAIT)
        self.assertEqual(result["source_site"], "The Sun UK")

        result = self.scraper.discern_website_from_url(CBSSPORTS_NOT_CLICKBAIT)
        self.assertEqual(result["source_site"], "CBS News")

    def test_scrape(self):
        """Test that the scrape() method returns a dictionary with the expected
        keys.
        """
        result = self.scraper.scrape(THESUN_NOT_CLICKBAIT)

        self.assertIsInstance(result, dict)
        self.assertIn("title", result)
        self.assertIsNotNone(result["title"])
        self.assertIn("content", result)
        self.assertIsNotNone(result["content"])
        self.assertIn("source_site", result)
        self.assertIsNotNone(result["source_site"])


class NLPPredictorTests(TestCase):
    """Test the NLP class."""
    def test_predict_on_text(self):
        """Test that the predict_on_text() method returns a list of tuples
        containing the predicted class and the probability of the predicted
        class.
        """
        # Test the model on a non-clickbait title
        nlp = NLP()
        result = nlp.predict_on_text(CLICKBAIT_TITLE)
        self.assertGreater(result[0][1], nlp.proba_cutoff)

        # Test the model on a non-clickbait title
        result = nlp.predict_on_text(NOT_CLICKBAIT_TITLE)
        self.assertLess(result[0][1], nlp.proba_cutoff)


class LLMPredictorTests(TestCase):
    """Test the LocalLLM class."""
    def test_predict(self):
        """Test that the predict() method returns a float."""
        llm = LocalLLM()
        result = llm.predict(CLICKBAIT_TITLE)
        result = 1 if result > llm.proba_cutoff else 0
        self.assertEqual(result, 1)

        result = llm.predict(NOT_CLICKBAIT_TITLE)
        result = 1 if result > llm.proba_cutoff else 0
        self.assertEqual(result, 0)


class ArticleModelTests(TestCase):
    """Test the Article model."""
    def test_default_values(self):
        """Test that default values are set for clickbait_decision fields.
        """
        new_article = Article(
            title="Test Article", content_summary="Summary"
        )
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
            article = Article(
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
            article = Article(
                title="Test Article",
                content_summary="Summary",
                clickbait_decision_NLP=decision,
                clickbait_decision_LLM=decision,
                clickbait_decision_VERTEX=decision,
                clickbait_decision_final=decision,
            )
            article.save()

    def test_decision_integer_constraint(self):
        """Test that the model raises IntegrityError for invalid decision values.
        """
        # Attempt to save a record with an invalid value
        with self.assertRaises(IntegrityError):
            article = Article(clickbait_decision_NLP=42)  # An invalid value
            article.save()


class VertexAIMock(VertexAI):
    """Mock the VertexAI class."""
    def init_connection(self):
        pass

    def load_model(self):
        pass

    def predict(self, title: Optional[str] = None):
        if title:
            return "1" if title.strip() == "My Clickbait Title" else "0"
        if self.title:
            return "1" if self.title.strip() == "My Clickbait Title" else "0"
        return "0"

    @patch("google.auth.load_credentials_from_dict")
    def load_config(self, mock_load_credentials_from_dict):  # pylint: disable=arguments-differ
        try:
            return_value = Config(
                refresh_token="test_refresh_token",
                client_id="test_client_id",
                client_secret="test_client_secret",
                quota_project_id="test_quota_project_id",
                type="test_type",
            )
            mock_load_credentials_from_dict.return_value = (
                return_value,
                return_value.quota_project_id,
            )
            self.cloud_setup.credentials, self.cloud_setup.project_id = mock_load_credentials_from_dict(
                asdict(return_value)
            )
        except (FileNotFoundError, KeyError):
            self.cloud_setup.credentials, self.cloud_setup.project_id = default()


class TestVertexAI(TestCase):
    """Test the VertexAI class."""
    def setUp(self):
        """Set up the test case."""
        self.vertex_ai = VertexAIMock()

    def test_init(self):
        """Test initializing VertexAI object."""
        self.assertEqual(self.vertex_ai.cloud_setup.project_id, None)
        self.assertEqual(self.vertex_ai.cloud_setup.location, None)
        self.assertEqual(self.vertex_ai.cloud_setup.experiment, None)
        self.assertEqual(self.vertex_ai.cloud_setup.staging_bucket, None)
        self.assertIsNone(self.vertex_ai.cloud_setup.credentials)
        self.assertIsNone(self.vertex_ai.cloud_setup.encryption_spec_key_name)
        self.assertIsNone(self.vertex_ai.cloud_setup.service_account)
        self.assertEqual(self.vertex_ai.model_name, ModelName.GEMINI)
        self.assertEqual(self.vertex_ai.title, "This is the Most Clickbait Title Ever!")
        self.assertEqual(
            self.vertex_ai.prompt,
            "Is this title a clickbait: 'PLACE_FOR_TITLE'? Summary of the article: 'PLACE_FOR_SUMMARY'. Return 1 if yes, 0 if no.",  # pylint: disable=line-too-long
        )
        self.assertIsNone(self.vertex_ai.my_chat_model)

    @patch("google.auth.load_credentials_from_dict")
    def test_load_config(self, mock_load_credentials_from_dict):
        """Test loading the config file."""
        mock_load_credentials_from_dict.return_value = (None, None)
        self.vertex_ai.load_config()  # pylint: disable=no-value-for-parameter
        self.assertEqual(self.vertex_ai.cloud_setup.credentials.refresh_token, "test_refresh_token")
        self.assertEqual(self.vertex_ai.cloud_setup.credentials.client_id, "test_client_id")
        self.assertEqual(self.vertex_ai.cloud_setup.credentials.client_secret, "test_client_secret")
        self.assertEqual(
            self.vertex_ai.cloud_setup.credentials.quota_project_id, "test_quota_project_id"
        )
        self.assertEqual(self.vertex_ai.cloud_setup.credentials.type, "test_type")

    def test_predict(self):
        """Test the predict() method."""
        result = self.vertex_ai.predict("My Clickbait Title")
        assert bool(result) is True

    @patch("google.auth.load_credentials_from_dict")
    def test_run_clickbait(self, mock_load_credentials_from_dict):
        """Test the run() method."""
        mock_load_credentials_from_dict.return_value = (None, None)
        with patch(
                "news.vertex.cloud.vertex_connection.VertexAI.predict"
        ) as mock_predict:
            with patch(
                    "news.vertex.cloud.vertex_connection.VertexAI.predict_gemini"
            ) as mock_predict_gemini:
                mock_predict_gemini.return_value = "1"
                mock_predict.return_value = "1"
                result = self.vertex_ai.run(title="My Clickbait Title")
                assert bool(result) is True

    @patch("google.auth.load_credentials_from_dict")
    def test_run_not_clickbait(self, mock_load_credentials_from_dict):
        """Test the run() method."""
        mock_load_credentials_from_dict.return_value = (None, None)
        with patch(
                "news.vertex.cloud.vertex_connection.VertexAI.predict"
        ) as mock_predict:
            with patch(
                    "news.vertex.cloud.vertex_connection.VertexAI.predict_gemini"
            ) as mock_predict_gemini:
                mock_predict_gemini.return_value = "0"
                mock_predict.return_value = "0"
                titles = [
                    "A Comprehensive Review of the Latest Machine Learning Techniques",
                    "The Impact of Artificial Intelligence on Society",
                    "The Future of Work in the Age of Automation",
                ]
                for title in titles:
                    result = self.vertex_ai.run(title=title)
                    assert result is False
