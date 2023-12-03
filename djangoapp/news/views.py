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
from news.scripts.nlp import Word2VecModel, return_best_model, predict_on_text, load_predictive_model
from news.scripts.llm import LocalLLM


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
        return Article.objects.filter(scraped_date__lte=timezone.now())
    
    
class BrowseView(generic.TemplateView):
    template_name = "news/browse.html"

    def get_context_data(self, **kwargs):
        context = super(BrowseView, self).get_context_data(**kwargs)
        context['latest_article_list'] = Article.objects.filter(scraped_date__lte=timezone.now()).order_by("-scraped_date")[:10]
        context['date_today'] = timezone.now().date().strftime("%Y-%m-%d")
        context['date_week_ago'] = (timezone.now() - timezone.timedelta(days=7)).date().strftime("%Y-%m-%d")
        return context









def check_url(request):
    if request.method == 'POST':
        form = URLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']

            # scraping vars
            config_path = os.path.join(settings.BASE_DIR, 'news', 'config', 'site_variables_dict')
            scraper = Scraper(config_path)
            scraped_data = scraper.scrape(url)
            
            
            # w2v model vars
            model_settings_path = os.path.join(settings.BASE_DIR, 'news', 'config', 'model_settings.json')
            model_w2v_settings = return_best_model(path=model_settings_path)
            model_path = os.path.join(settings.BASE_DIR, 'news', 'word2vec_models', model_w2v_settings['model_path'])
            model_w2v = Word2VecModel(model_w2v_settings,model_path)
            
            # predictive model vars
            predictive_model_path = os.path.join(settings.BASE_DIR, 'news', 'predictive_models', 'catboost_model.pkl')
            predictive_model = load_predictive_model(predictive_model_path)
            

            # try:
            #     # If an article with the same title and source site exists don't, create a new article
            #     article = get_object_or_404(Article, title=scraped_data['title'], source_site=scraped_data['source_site'])
            # except:
            proba_cutoff = 0.5
            clickbait_decision_NLP_proba = predict_on_text(predictive_model,model_w2v, scraped_data['title'])
            clickbait_decision_NLP_proba = clickbait_decision_NLP_proba[0][1]
            clickbait_decision_NLP = int(clickbait_decision_NLP_proba > proba_cutoff)
            
            llm = LocalLLM()
            clickbait_decision_LLM = llm.predict(scraped_data['title'])
            # Create a new article if no matching article exists
            article = Article(
                title=scraped_data['title'],
                content_summary=scraped_data['content'],
                url_from=url,
                source_site=scraped_data['source_site'],
                clickbait_decision_NLP = clickbait_decision_NLP,
                clickbait_decision_LLM = int(clickbait_decision_LLM),
                clickbait_decision_final = clickbait_decision_NLP,
            )
            
            
            article.save()

            # Render the details template with the scraped data and return as a JSON response
            html_content = render_to_string('news/article_info.html', {'article': article})
            return JsonResponse({'html': html_content})    
    else:
        form = URLForm()

    return render(request, 'news/check_url.html', {'form': form})
