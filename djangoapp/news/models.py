import datetime

from django.db import models
from django.utils import timezone
from django.db.models import Q
from django.db.models.functions import Now


# Create your models here.


class Article(models.Model):
    title = models.CharField(max_length=256)
    content_summary = models.TextField()
    pub_date = models.DateTimeField(null=True,blank=True)
    scraped_date = models.DateTimeField(default=timezone.now)
    author = models.CharField(max_length=64)
    source_site = models.CharField(max_length=64, default='UNKNOWN') 
    url_from = models.CharField(max_length=256, null=True,blank=True)
    # clickbait = models.BooleanField(default=False)
    clickbait_decision_NLP = models.SmallIntegerField(default=-1)  # classic mlp model decision
    clickbait_decision_LLM = models.SmallIntegerField(default=-1)  # LLM model decision
    clickbait_decision_final = models.SmallIntegerField(default=-1) # joined decision, maybe this could be on a confidence scale?
    def __str__(self):
        return self.title
    
    
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                # possibility for the article to be published one day in the future, but no more, because of timezone
                check=(
                    Q(pub_date__isnull=True) |
                    Q(pub_date__lte=timezone.now+datetime.timedelta(days=1))
                ),
                name="published_date_not_later_than_tomorrow"  
            ),
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
    
    
    def published_date(self):
        if self.pub_date:
            return self.pub_date.strftime('%Y-%m-%d')
        return '-'