"""
Data models for the news app.
"""
import datetime

from django.db import models
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ValidationError


def validate_date_is_not_future(value):
    """
    Used in the Article model to validate the scraped_date field.
    """
    if value is not None and value > timezone.now() + datetime.timedelta(days=1):
        raise ValidationError("The date cannot be more than 1 day in the future.")


class Article(models.Model):
    """
    Data model for the Article object.
    The final clickbait decision can be one of the following:
    -1 - unknown - no decision made or something went wrong
    0 - definitely not clickbait, all models agree
    1 - likely not a clickbait one out of three models agree
    2 - likely  a clickbait, 
        either two of three models agree or one of two models agree 
        (this is the case when vertex model is not used)
    3 - definitely a clickbait, all models agree

    """
    title = models.CharField(max_length=256)
    content_summary = models.TextField()
    scraped_date = models.DateTimeField(
        default=timezone.now,
        validators=[validate_date_is_not_future]
    )
    source_site = models.CharField(max_length=64, default="UNKNOWN")
    url_from = models.CharField(max_length=256, null=True, blank=True)
    category = models.CharField(max_length=64, null=True, blank=True)
    clickbait_decision_nlp = models.SmallIntegerField(default=-1)
    clickbait_probability_nlp = models.FloatField(default=0)
    clickbait_decision_llm = models.SmallIntegerField(default=-1)
    clickbait_probability_llm = models.FloatField(default=0)
    clickbait_decision_vertex = models.SmallIntegerField(default=-1)
    clickbait_decision_final = models.SmallIntegerField(default=-1)


    def __str__(self):
        return str(self.title)

    # pylint: disable=too-few-public-methods
    class Meta:
        """
        Meta class for the Article model.
        For now this is only used to define the constraints.
        """
        constraints = [
            models.CheckConstraint(
                check=Q(clickbait_decision_nlp__in=[-1, 0, 1]),
                name="valid_decision_nlp",
            ),
            models.CheckConstraint(
                check=Q(clickbait_decision_llm__in=[-1, 0, 1]),
                name="valid_decision_llm",
            ),
            models.CheckConstraint(
                check=Q(clickbait_decision_vertex__in=[-1, 0, 1]),
                name="valid_decision_vertex",
            ),
            models.CheckConstraint(
                check=Q(clickbait_decision_final__in=[-1, 0, 1, 2, 3]),
                name="valid_decision_final",
            ),
            models.CheckConstraint(
                check=Q(clickbait_probability_nlp__gte=0, clickbait_probability_nlp__lte=1),
                name="valid_probability_nlp",
            ),
            models.CheckConstraint(
                check=Q(clickbait_probability_llm__gte=0, clickbait_probability_llm__lte=1),
                name="valid_probability_llm",
            ),
        ]

    def was_scraped_today(self) -> bool:
        """Return True if the article was scraped today."""
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.scraped_date <= now


    def make_final_decision(self) -> None:
        """
        Returns the final decision made by the models.
        If vertex model is not used, the decision is made by the other two models.
        """
        if self.clickbait_decision_vertex != -1: # vertex model is used
            self.clickbait_decision_final = int(
                self.clickbait_decision_nlp +
                self.clickbait_decision_llm +
                self.clickbait_decision_vertex
            )
        else:
            sum_ = self.clickbait_decision_llm + self.clickbait_decision_nlp
            if sum_ == 0: # both models agree that it is not a clickbait
                self.clickbait_decision_final = 0
            elif sum_ == 1: # one of the models thinks it is a clickbait
                self.clickbait_decision_final = 1
            elif sum_ == 2: # both models think it is a clickbait
                self.clickbait_decision_final = 3
            # something went wrong
            else:
                self.clickbait_decision_final =  -1
