import os

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string  
from django.urls import reverse
from django.views import generic
from django.utils import timezone

from .models import Article

from .forms import URLForm

from django.conf import settings

from news.scripts.scraping import Scraper


class IndexView(generic.ListView):
    template_name = "news/index.html"
    context_object_name = "latest_article_list"

    def get_queryset(self):
        """Return the last five published articles."""
        article_list = (
            Article.objects.filter(source_site='Site 1').filter(scraped_date__lte=timezone.now()).order_by("-scraped_date")[:5]   
        )
        return article_list


class DetailView(generic.DetailView):
    model = Article
    template_name = "news/detail.html"
    def get_queryset(self):
        """
        Excludes any articles that aren't published yet.
        """
        return Article.objects.filter(scraped_date__lte=timezone.now())
    
    
class BrowseView(generic.TemplateView):
    template_name = "news/browse.html"

    def get_context_data(self, **kwargs):
        context = super(BrowseView, self).get_context_data(**kwargs)
        context['latest_article_list'] = Article.objects.filter(scraped_date__lte=timezone.now()).order_by("-scraped_date")[:5]
        context['date_today'] = timezone.now().date().strftime("%Y-%m-%d")
        context['date_week_ago'] = (timezone.now() - timezone.timedelta(days=7)).date().strftime("%Y-%m-%d")
        return context

def vote(request, article_id):
    return HttpResponse("You're voting on article %s." % article_id)








def check_url(request):
    if request.method == 'POST':
        form = URLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']

            config_path = os.path.join(settings.BASE_DIR, 'news', 'config', 'site_variables_dict')
            scraper = Scraper(config_path)
            scraped_data = scraper.scrape(url)

            try:
                article = get_object_or_404(Article, title=scraped_data['title'], source_site=scraped_data['source_site'])
            except:

                    # Create a new article if no matching article exists
                    article = Article(
                        title=scraped_data['title'],
                        content_summary=scraped_data['content'],
                        url_from=url,
                        source_site=scraped_data['source_site']
                    )
                    article.save()

            # Render the details template with the scraped data and return as a JSON response
            html_content = render_to_string('news/article_info.html', {'article': article})
            return JsonResponse({'html': html_content})    
    else:
        form = URLForm()

    return render(request, 'news/check_url.html', {'form': form})
