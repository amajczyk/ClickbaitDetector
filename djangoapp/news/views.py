from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views import generic
from django.utils import timezone

from .models import Article

class IndexView(generic.ListView):
    template_name = "news/index.html"
    context_object_name = "latest_article_list"

    def get_queryset(self):
        """Return the last five published articles."""
        return Article.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]   


class DetailView(generic.DetailView):
    model = Article
    template_name = "news/detail.html"
    def get_queryset(self):
        """
        Excludes any articles that aren't published yet.
        """
        return Article.objects.filter(pub_date__lte=timezone.now())
    
    
class BrowseView(generic.ListView):
    template_name = "news/browse.html"
    context_object_name = "latest_article_list"

    def get_queryset(self):
        """Return the last five published articles."""
        return Article.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]



def vote(request, article_id):
    return HttpResponse("You're voting on article %s." % article_id)