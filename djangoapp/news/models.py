import datetime

from django.db import models
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ValidationError


def validate_date_is_not_future(value):
    if value is not None and value >  timezone.now() + datetime.timedelta(days=1):
        raise ValidationError("The date cannot be more than 1 day in the future.")

class Article(models.Model):
    title = models.CharField(max_length=256)
    content_summary = models.TextField()
    scraped_date = models.DateTimeField(default=timezone.now, validators=[validate_date_is_not_future])
    source_site = models.CharField(max_length=64, default='UNKNOWN') 
    url_from = models.CharField(max_length=256, null=True,blank=True)
    category = models.CharField(max_length=64, null=True,blank=True)
    subcategory = models.CharField(max_length=64, null=True,blank=True)
    
    clickbait_decision_NLP = models.SmallIntegerField(default=-1)  # classic mlp model decision
    clickbait_probability_NLP = models.FloatField(default=-1)  # classic mlp model decision
    clickbait_decision_LLM = models.SmallIntegerField(default=-1)  # LLM model decision
    clickbait_probability_LLM = models.FloatField(default=-1)  # LLM model decision
    clickbait_decision_VERTEX = models.SmallIntegerField(default=-1)  # VERTEX AI model decision 
    
    clickbait_decision_final = models.SmallIntegerField(default=-1) # joined decision
    # 0 - clickbait 0/3 or 0/2
    # 1 - clickbait 1/3
    # 2 - not clickbait 2/3 or 1/2
    # 3 - not clickbait 3/3 or 2/2 
    
    
    def __str__(self):
        return self.title
    
    
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=Q(clickbait_decision_NLP__in=[-1, 0, 1]),
                name="valid_decision_NLP"
            ),
            models.CheckConstraint(
                check=Q(clickbait_decision_LLM__in=[-1, 0, 1]),
                name="valid_decision_LLM"
            )
        ]
    
    
    
    def __str__(self):
        return self.title
    
    
    def was_scraped_today(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.scraped_date <= now
    
    
    # def published_date(self):
    #     if self.pub_date:
    #         return self.pub_date.strftime('%Y-%m-%d')
    #     return '-'
    
    
