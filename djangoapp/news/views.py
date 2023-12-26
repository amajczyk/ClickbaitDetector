import os
from multiprocessing import Pool
from random import shuffle

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string  
from django.views import generic
from django.utils import timezone

from .models import Article

from .forms import URLForm, SiteSelectionForm, SearchArticlesForm

from news.scripts.nlp import predict_on_text
from news.scripts.model_loader import ModelLoader
from django.db.models import Q

import concurrent.futures

from functools import partial


from dataclasses import dataclass

@dataclass
class ArticleData:
    title: str = ''
    content: str = ''
    content_summary: str = ''
    url_from: str = ''
    source_site: str = ''
    clickbait_decision_NLP: int = -1
    clickbait_decision_LLM: int = -1
    clickbait_decision_VERTEX: int = -1
    clickbait_decision_final: int = -1
    
    def to_model(self):
        return Article(
            title=self.title,
            content_summary=self.content_summary,
            url_from=self.url_from,
            source_site=self.source_site,
            clickbait_decision_NLP=self.clickbait_decision_NLP,
            clickbait_decision_LLM=self.clickbait_decision_LLM,
            clickbait_decision_VERTEX=self.clickbait_decision_VERTEX,
            clickbait_decision_final=self.clickbait_decision_final,
        )
    
    




class DetailView(generic.DetailView):
    model = Article
    template_name = "news/detail.html"
    def get_queryset(self):
        return Article.objects.filter(scraped_date__lte=timezone.now())
    


def check_url(request):
    if request.method == 'POST':
        form = URLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']

            model_loader = ModelLoader()

            # Access the loaded models
            scraper = model_loader.scraper
            model_w2v = model_loader.model_w2v
            scaler = model_loader.scaler
            predictive_model = model_loader.predictive_model
            vertex = model_loader.vertex
            llm = model_loader.llm
            summarizer = model_loader.summarizer
            

            
            scraped_data = scraper.scrape(url)
            title = scraped_data['title']
     
            try:
                article = get_object_or_404(Article, title=scraped_data['title'], source_site=scraped_data['source_site'])
            except:
                content_summary = summarizer(scraped_data['content'], max_length=200, min_length=40, do_sample=False)[0]["summary_text"]
                clickbait_decision_NLP = classify_NLP(title, predictive_model, model_w2v, scaler)
                clickbait_decision_LLM = classify_LLM(title, llm)
                clickbait_decision_VERTEX = classify_VERTEX(title, vertex)
                clickbait_decision_final = make_final_decision(clickbait_decision_NLP, clickbait_decision_LLM, clickbait_decision_VERTEX)
                
                

                article = Article(
                    title=scraped_data['title'],
                    content_summary=content_summary,
                    url_from=url,
                    source_site=scraped_data['source_site'],
                    clickbait_decision_NLP = clickbait_decision_NLP,
                    clickbait_decision_LLM = int(clickbait_decision_LLM),
                    clickbait_decision_VERTEX = clickbait_decision_VERTEX,
                    clickbait_decision_final = clickbait_decision_final,
                )
                
            
            article.save()
            html_content = render_to_string('news/article_info.html', {'article': article})
            return JsonResponse({'html': html_content})    
    else:
        form = URLForm()

    return render(request, 'news/check_url.html', {'form': form})



def classify_NLP(data, predictive_model, model_w2v,scaler):
    proba_cutoff = 0.3490965225838074
    clickbait_decision_NLP_proba = predict_on_text(predictive_model, model_w2v, scaler, data)
    clickbait_decision_NLP_proba = clickbait_decision_NLP_proba[0][1]
    return int(clickbait_decision_NLP_proba > proba_cutoff)

def classify_LLM(data, llm):
    proba_cutoff = 0.5
    probability = llm.predict(data)
    print(probability)
    return int(probability > proba_cutoff)
    

def classify_VERTEX(data, vertex):
    try:
        clickbait_decision_VERTEX = vertex.run(title=data)
        return clickbait_decision_VERTEX
    except:
        return -1


def process_article(url, scraper, predictive_model, model_w2v, scaler, llm, summarizer,vertex):
    scraped_data = scraper.scrape(url)
    scraped_data['url'] = url
    title = scraped_data['title']
    clickbait_decision_NLP = int(classify_NLP(title, predictive_model, model_w2v, scaler))
    clickbait_decision_LLM = int(classify_LLM(title, llm))
    content_summary = summarizer(scraped_data['content'], max_length=200, min_length=40, do_sample=False)[0]['summary_text'].replace(' .','.')
    clickbait_decision_VERTEX = classify_VERTEX(title, vertex)
    clickbait_decision_final = make_final_decision(clickbait_decision_NLP, clickbait_decision_LLM, clickbait_decision_VERTEX)
    article = Article(
        title=title,
        url_from=url,
        content_summary=content_summary,
        source_site=scraped_data['source_site'],
        clickbait_decision_NLP = clickbait_decision_NLP,
        clickbait_decision_LLM = clickbait_decision_LLM,
        clickbait_decision_VERTEX=clickbait_decision_VERTEX,
        clickbait_decision_final=clickbait_decision_final,
    )
    article.save()
    return article



def scrape_articles(request):
    if request.method == 'POST':
        form = SiteSelectionForm(request.POST)
        if form.is_valid():
            # Process the form data
            selected_sites = [
                key for key, value in form.cleaned_data.items() if value
            ]
        

            model_loader = ModelLoader()
            scraper = model_loader.scraper
            model_w2v = model_loader.model_w2v
            scaler = model_loader.scaler
            predictive_model = model_loader.predictive_model
            vertex = model_loader.vertex
            llm = model_loader.llm
            summarizer = model_loader.summarizer

            urls = []
            for site in selected_sites:
                urls += scraper.scrape_article_urls(scraper.site_variables_dict[site]['main'])
            shuffle(urls) # shuffle in place
            urls_to_scrape = urls[:5]
            process_article_partial = partial(process_article, scraper=scraper, predictive_model=predictive_model, model_w2v=model_w2v, scaler=scaler, llm=llm, summarizer=summarizer,vertex=vertex)
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                articles = list(executor.map(process_article_partial, urls_to_scrape))

            
            context = {'form': form}
            context['latest_article_list'] = articles
            return render(request, 'news/index.html', context)
    else:
        form = SiteSelectionForm()

    return render(request, 'news/index.html', {'form': form})



def make_final_decision(clickbait_decision_NLP, clickbait_decision_LLM, clickbait_decision_VERTEX):
    if clickbait_decision_VERTEX != -1:
        return int(clickbait_decision_NLP + clickbait_decision_LLM + clickbait_decision_VERTEX)
    
    decisions = [clickbait_decision_NLP, clickbait_decision_LLM]
    sum_ = sum(decisions)
    if sum_ == 0:
        return 0
    elif sum_ == 1:
        return 2
    elif sum_ == 2:
        return 3
    return -1


def browse_articles(request):
    if request.method == 'POST':
        form = SearchArticlesForm(request.POST)
        if form.is_valid():

            search_query = form.cleaned_data['search_query']
            date_from = form.cleaned_data['date_from']
            date_to = form.cleaned_data['date_to']
            show_clickbaits = form.cleaned_data['show_clickbaits']
            thesun = form.cleaned_data['thesun']
            cbsnews = form.cleaned_data['cbsnews']
            abcnews = form.cleaned_data['abcnews']
            # Use the form data as needed to filter the articles from the database
            
            query = Q()

            # Add conditions based on form fields
            if search_query:
                query &= Q(title__icontains=search_query) | Q(content_summary__icontains=search_query)

            if not show_clickbaits:
                query &= ~Q(clickbait_decision_final=1)

            source_sites = []
            if thesun:
                source_sites.append('The Sun UK')
            if cbsnews:
                source_sites.append('CBS News')
            if abcnews:
                source_sites.append('ABC News')

            if source_sites:
                query &= Q(source_site__in=source_sites)

            articles = Article.objects.filter(query)
            context = {'form': form}
            context['latest_article_list'] = articles
            return render(request, 'news/browse.html', context=context)


    else:
        form = SearchArticlesForm()

    return render(request, 'news/browse.html', {'form': form})

