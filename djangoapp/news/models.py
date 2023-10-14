import datetime

from django.db import models
from django.utils import timezone


# Create your models here.


class Article(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    pub_date = models.DateTimeField('date published')
    author = models.CharField(max_length=200)
    url_from = models.CharField(max_length=200, default="")
    clickbait = models.BooleanField(default=False)
    def __str__(self):
        return self.title
    
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now