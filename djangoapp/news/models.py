"""Models for the clickbait detector app."""
import datetime

from django.db import models
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ValidationError


def validate_date_is_not_future(value):
    """Validate that the date is not in the future."""
    if value is not None and value > timezone.now() + datetime.timedelta(days=1):
        raise ValidationError("The date cannot be more than 1 day in the future.")


class Article(models.Model):
    """Model for the articles."""
    title = models.CharField(max_length=256)
    content_summary = models.TextField()
    scraped_date = models.DateTimeField(
        default=timezone.now, validators=[validate_date_is_not_future]
    )
    source_site = models.CharField(max_length=64, default="UNKNOWN")
    url_from = models.CharField(max_length=256, null=True, blank=True)
    category = models.CharField(max_length=64, null=True, blank=True)
    subcategory = models.CharField(max_length=64, null=True, blank=True)

    clickbait_decision_nlp = models.SmallIntegerField(
        default=-1
    )  # classic mlp model decision
    clickbait_probability_nlp = models.FloatField(
        default=-1
    )  # classic mlp model decision
    clickbait_decision_llm = models.SmallIntegerField(default=-1)  # LLM model decision
    clickbait_probability_llm = models.FloatField(default=-1)  # LLM model decision
    clickbait_decision_vertex = models.SmallIntegerField(
        default=-1
    )  # VERTEX AI model decision

    clickbait_decision_final = models.SmallIntegerField(default=-1)  # joined decision
    # 0 - clickbait 0/3 or 0/2
    # 1 - clickbait 1/3
    # 2 - not clickbait 2/3 or 1/2
    # 3 - not clickbait 3/3 or 2/2

    def __str__(self):
        return str(self.title)

    # pylint: disable=too-few-public-methods
    class Meta:
        """Metaclass for the Article model."""
        constraints = [
            models.CheckConstraint(
                check=Q(clickbait_decision_nlp__in=[-1, 0, 1]),
                name="valid_decision_nlp",
            ),
            models.CheckConstraint(
                check=Q(clickbait_decision_llm__in=[-1, 0, 1]),
                name="valid_decision_llm",
            ),
        ]
    # pylint: enable=too-few-public-methods

    def was_scraped_today(self):
        """Return True if the article was scraped today."""
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.scraped_date <= now

    # def published_date(self):
    #     if self.pub_date:
    #         return self.pub_date.strftime('%Y-%m-%d')
    #     return '-'
