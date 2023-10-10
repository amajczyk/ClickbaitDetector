# import datetime

from django.test import TestCase
# from django.utils import timezone
# from django.urls import reverse

# from .models import Article



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



# class ArticleModelTests(TestCase):
#     def test_was_published_recently_with_old_article(self):
#         """
#         was_published_recently() returns False for articles whose pub_date
#         is older than 1 day.
#         """
#         time = timezone.now() - datetime.timedelta(days=1, seconds=1)
#         old_article = Article(pub_date=time)
#         self.assertIs(old_article.was_published_recently(), False)


#     def test_was_published_recently_with_recent_article(self):
#         """
#         was_published_recently() returns True for articles whose pub_date
#         is within the last day.
#         """
#         time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
#         recent_article = Article(pub_date=time)
#         self.assertIs(recent_article.was_published_recently(), True)