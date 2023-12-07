import datetime
from dataclasses import asdict
from typing import Optional

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from google.auth import default

from .models import Article

from unittest.mock import patch
from news.vertex.cloud.connections_based_on_docs import VertexAI, ModelName
from news.vertex.configs.config import Config

# python manage.py test news
# https://docs.djangoproject.com/en/4.2/intro/tutorial05/

print('Testing news app...')
print('Time now: ', timezone.now())


class ArticleModelTests(TestCase):

    #   def test_was_scraped_in_the_last_24h(self):
    #      """
    #     was_scraped_today() should return True for articles whose scraped_date
    #    is within the last day.
    #   """
    #  time = timezone.now() - datetime.timedelta(hours=23, minutes=59)
    #  recent_article = Article(pub_date=time)
    #  self.assertIs(recent_article.was_scraped_today(), True)

    def test_was_scraped_later_than_the_last_24h(self):
        """
        was_scraped_today() should return False for articles whose scraped_date
        is outside the last day.
        """
        time = timezone.now() - datetime.timedelta(days=1, minutes=1)
        old_article = Article(scraped_date=time)
        self.assertIs(old_article.was_scraped_today(), False)

    def test_decision_integer_constraint(self):
        # Attempt to save a record with an invalid value
        with self.assertRaises(IntegrityError):
            Article.objects.create(clickbait_decision_NLP=42)  # An invalid value

    # def test_published_date_constraint(self):
    #     # Attempt to save a record with a scraped_date more than 1 day after published_date
    #     with self.assertRaises(ValidationError):
    #         article = Article.objects.create(
    #             pub_date=timezone.now() + datetime.timedelta(days=1, minutes=1),
    #         )
    #         article.full_clean()


# def create_article(content, days):
#     """
#     Create a article with the given `content` and published the
#     given number of `days` offset to now (negative for articles published
#     in the past, positive for articles that have yet to be published).
#     """
#     time = timezone.now() + datetime.timedelta(days=days)
#     return Article.objects.create(content=content, pub_date=time)


# class ArticleIndexViewTests(TestCase):
#     def test_no_articles(self):
#         """
#         If no articles exist, an appropriate message is displayed.
#         """
#         response = self.client.get(reverse("news:index"))
#         self.assertEqual(response.status_code, 200)
#         self.assertContains(response, "No articles are available.")
#         self.assertQuerySetEqual(response.context["latest_article_list"], [])

#     def test_past_article(self):
#         """
#         Articles with a pub_date in the past are displayed on the
#         index page.
#         """
#         article = create_article(content="Past article.", days=-30)
#         response = self.client.get(reverse("news:index"))
#         self.assertQuerySetEqual(
#             response.context["latest_article_list"],
#             [article],
#         )

#     def test_future_article(self):
#         """
#         Articles with a pub_date in the future aren't displayed on
#         the index page.
#         """
#         create_article(content="Future article.", days=30)
#         response = self.client.get(reverse("news:index"))
#         self.assertContains(response, "No articles are available.")
#         self.assertQuerySetEqual(response.context["latest_article_list"], [])

#     def test_future_article_and_past_article(self):
#         """
#         Even if both past and future articles exist, only past articles
#         are displayed.
#         """
#         article = create_article(content="Past article.", days=-30)
#         create_article(content="Future article.", days=30)
#         response = self.client.get(reverse("news:index"))
#         self.assertQuerySetEqual(
#             response.context["latest_article_list"],
#             [article],
#         )

#     def test_two_past_articles(self):
#         """
#         The articles index page may display multiple articles.
#         """
#         article1 = create_article(content="Past article 1.", days=-30)
#         article2 = create_article(content="Past article 2.", days=-5)
#         response = self.client.get(reverse("news:index"))
#         self.assertQuerySetEqual(
#             response.context["latest_article_list"],
#             [article2, article1],
#         )


# class ArticleDetailViewTests(TestCase):
#     def test_future_article(self):
#         """
#         The detail view of a article with a pub_date in the future
#         returns a 404 not found.
#         """
#         future_article = create_article(content="Future article.", days=5)
#         url = reverse("news:detail", args=(future_article.id,))
#         response = self.client.get(url)
#         self.assertEqual(response.status_code, 404)

#     def test_past_article(self):
#         """
#         The detail view of a article with a pub_date in the past
#         displays the article's text.
#         """
#         past_article = create_article(content="Past Article.", days=-5)
#         url = reverse("news:detail", args=(past_article.id,))
#         response = self.client.get(url)
#         self.assertContains(response, past_article.content)

class VertexAIMock(VertexAI):
    def init_connection(self):
        pass

    def load_model(self):
        pass

    def predict(self, title: Optional[str] = None):
        if title:
            return '1' if title.strip() == 'My Clickbait Title' else '0'
        elif self.title:
            return '1' if self.title.strip() == 'My Clickbait Title' else '0'
        return '0'


    @patch('google.auth.load_credentials_from_dict')
    def load_config(self, mock_load_credentials_from_dict):

        try:
            return_value = Config(
                refresh_token="test_refresh_token",
                client_id="test_client_id",
                client_secret="test_client_secret",
                quota_project_id="test_quota_project_id",
                type="test_type"
            )
            mock_load_credentials_from_dict.return_value = (return_value, return_value.quota_project_id)
            self.credentials, self.project_id = mock_load_credentials_from_dict(asdict(return_value))
        except FileNotFoundError or KeyError:
            self.credentials, self.project_id = default()


class TestVertexAI(TestCase):

    def test_init(self):
        self.vertex_ai = VertexAIMock()
        """Test initializing VertexAI object."""
        self.assertEqual(self.vertex_ai.project_id, None)
        self.assertEqual(self.vertex_ai.location, None)
        self.assertEqual(self.vertex_ai.experiment, None)
        self.assertEqual(self.vertex_ai.staging_bucket, None)
        self.assertIsNone(self.vertex_ai.credentials)
        self.assertIsNone(self.vertex_ai.encryption_spec_key_name)
        self.assertIsNone(self.vertex_ai.service_account)
        self.assertEqual(self.vertex_ai.model_name, ModelName.BISON_001)
        self.assertEqual(self.vertex_ai.title, "This is the Most Clickbait Title Ever!")
        self.assertEqual(
            self.vertex_ai.prompt, "Is this title a clickbait: 'PLACE_FOR_TITLE'? Return 1 if yes, 0 if no.")
        self.assertIsNone(self.vertex_ai.my_chat_model)

    @patch('google.auth.load_credentials_from_dict')
    def test_load_config(self, mock_load_credentials_from_dict):
        mock_load_credentials_from_dict.return_value = (None, None)
        self.vertex_ai = VertexAIMock()
        self.vertex_ai.load_config()
        self.assertEqual(self.vertex_ai.credentials.refresh_token, "test_refresh_token")
        self.assertEqual(self.vertex_ai.credentials.client_id, "test_client_id")
        self.assertEqual(self.vertex_ai.credentials.client_secret, "test_client_secret")
        self.assertEqual(self.vertex_ai.credentials.quota_project_id, "test_quota_project_id")
        self.assertEqual(self.vertex_ai.credentials.type, "test_type")

    def test_predict(self):
        self.vertex_ai = VertexAIMock()
        result = self.vertex_ai.predict("My Clickbait Title")
        assert bool(result) is True

    @patch('google.auth.load_credentials_from_dict')
    def test_run_clickbait(self, mock_load_credentials_from_dict):
        mock_load_credentials_from_dict.return_value = (None, None)
        with patch('news.vertex.cloud.connections_based_on_docs.VertexAI.predict') as mock_predict:
            mock_predict.return_value = '1'
            self.vertex_ai = VertexAIMock()
            result = self.vertex_ai.run(title='My Clickbait Title')
            assert bool(result) is True

    @patch('google.auth.load_credentials_from_dict')
    def test_run_not_clickbait(self, mock_load_credentials_from_dict):
        mock_load_credentials_from_dict.return_value = (None, None)
        with patch('news.vertex.cloud.connections_based_on_docs.VertexAI.predict') as mock_predict:
            self.vertex_ai = VertexAIMock()
            mock_predict.return_value = '0'
            titles = [
                "A Comprehensive Review of the Latest Machine Learning Techniques",
                "The Impact of Artificial Intelligence on Society",
                "The Future of Work in the Age of Automation"
            ]
            for title in titles:
                result = self.vertex_ai.run(title=title)
                assert result is False
