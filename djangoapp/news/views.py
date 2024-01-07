import datetime

from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string  
from django.views import generic
from django.utils import timezone

from .models import Article

from .forms import URLForm, SiteSelectionForm, SearchArticlesForm

from news.scripts.nlp import NLP
from news.scripts.model_loader import ModelLoader
from news.scripts.scraping import NotSupportedWebsiteException
from news.vertex.cloud.connections_based_on_docs import VertexAI

from django.db.models import Q

import concurrent.futures

from functools import partial


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
            nlp = model_loader.nlp
            vertex = model_loader.vertex
            llm = model_loader.llm
            summarizer = model_loader.summarizer
            

            try:
                scraped_data = scraper.scrape(url)
            except NotSupportedWebsiteException as e:
                return JsonResponse({'error': str(e)})


            title = scraped_data['title']
     
            try:
                article = Article.objects.get(url_from=url)
            except:
                content_summary = summarizer(scraped_data['content'], max_length=200, min_length=40, do_sample=False)[0]["summary_text"]
                clickbait_decision_NLP = classify_NLP(title, nlp)
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



def classify_NLP(title, nlp):
    clickbait_decision_NLP_proba = nlp.predict_on_text(title)
    clickbait_decision_NLP_proba = clickbait_decision_NLP_proba[0][1]
    return int(clickbait_decision_NLP_proba > nlp.proba_cutoff)

def classify_LLM(title, llm):
    proba_cutoff = 0.5
    probability = llm.predict(title)
    result = int(probability > proba_cutoff)
    return result
    

def classify_VERTEX(title, vertex, summary=None):
    try:
        if summary:
            clickbait_decision_VERTEX = vertex.run(title=title, summary=summary)
        else:
            clickbait_decision_VERTEX = vertex.run(title=title)
        return int(clickbait_decision_VERTEX)
    except:
        return -1


def process_article(url, scraper, nlp, llm, summarizer,vertex, selected_category):
    # qery the database for the article using url
    # if it exists, return it
    try:
        article = Article.objects.get(url_from=url)
        return article
    except:
        scraped_data = scraper.scrape(url)
        scraped_data['url'] = url
        title = scraped_data['title']
        clickbait_decision_NLP = int(classify_NLP(title, nlp))
        clickbait_decision_LLM = int(classify_LLM(title, llm))
        content_summary = summarizer(scraped_data['content'], max_length=200, min_length=40, do_sample=False)[0]['summary_text'].replace(' .','.')

        vertex = VertexAI() 
        clickbait_decision_VERTEX = classify_VERTEX(title, vertex, content_summary)
        
        
        clickbait_decision_final = make_final_decision(clickbait_decision_NLP, clickbait_decision_LLM, clickbait_decision_VERTEX)
        article = Article(
            title=title,
            url_from=url,
            content_summary=content_summary,
            source_site=scraped_data['source_site'],
            category = selected_category,
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
                key for key, value in form.cleaned_data.items() if value and key not in ['clickbait_tolerance','category']
            ]
            selected_category = form.cleaned_data['category']
            
            request.session['selected_sites'] = selected_sites
            request.session['selected_category'] = selected_category
            


            model_loader = ModelLoader()
            scraper = model_loader.scraper
            nlp = model_loader.nlp
            vertex = model_loader.vertex
            llm = model_loader.llm
            summarizer = model_loader.summarizer


            for site in selected_sites:
                scrape_urls(request, site, scraper)
            urls = get_next_urls(request, selected_sites)
            process_article_partial = partial(process_article, scraper=scraper, nlp=nlp, llm=llm, summarizer=summarizer,vertex=vertex,selected_category=selected_category)
            with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
                articles = list(executor.map(process_article_partial, urls))
                
            context = {'form': form}
            articles_html =  render_to_string('news/list_articles.html', {'latest_article_list': articles})
            return JsonResponse({'articles_html': articles_html})
    else:
        form = SiteSelectionForm()

    return render(request, 'news/index.html', {'form': form})


def load_more_articles(request):
    
    model_loader = ModelLoader()
    scraper = model_loader.scraper
    nlp = model_loader.nlp
    vertex = model_loader.vertex
    llm = model_loader.llm
    summarizer = model_loader.summarizer

    selected_sites = request.session['selected_sites']
    selected_category = request.session['selected_category']
    for site in selected_sites:
        use_generator(request,site,selected_category,scraper)
    urls = get_next_urls(request, selected_sites)
    process_article_partial = partial(process_article, scraper=scraper, nlp=nlp, llm=llm, summarizer=summarizer,vertex=vertex, selected_category=selected_category)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        articles = list(executor.map(process_article_partial, urls))    
    request.session.save()
    
    articles_html = render_to_string('news/list_articles.html', {'latest_article_list': articles})
    return JsonResponse({'articles_html': articles_html})




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
            date_to = form.cleaned_data['date_to'] + datetime.timedelta(days=1)
            clickbait_tolerance = int(form.cleaned_data['clickbait_tolerance'])
            
            thesun = form.cleaned_data['thesun']
            cbsnews = form.cleaned_data['cbsnews']
            abcnews = form.cleaned_data['abcnews']
            
            # Use the form data as needed to filter the articles from the database
            
            query = Q()

            # Add conditions based on form fields
            if search_query:
                query &= Q(title__icontains=search_query) | Q(content_summary__icontains=search_query)

            query &= Q(clickbait_decision_final__lte=clickbait_tolerance)

            query &= Q(scraped_date__gte=date_from) & Q(scraped_date__lte=date_to)

            source_sites = []
            if thesun:
                source_sites.append('The Sun UK')
            if cbsnews:
                source_sites.append('CBS News')
            if abcnews:
                source_sites.append('ABC News')

            if source_sites:
                query &= Q(source_site__in=source_sites)

            articles = Article.objects.filter(query).order_by('-scraped_date')
            context = {'form': form}
            context['latest_article_list'] = articles
            return render(request, 'news/browse.html', context=context)


    else:
        form = SearchArticlesForm()

    articles = Article.objects.order_by('-scraped_date')[:10]
    context = {'form': form, 'latest_article_list': articles}    
    return render(request, 'news/browse.html', context=context)


        
def use_generator(request,site,selected_category,scraper):
    
    # doesn't return anything, updates the session variables
    if selected_category == 'front_page':
        selected_category = 'main'
    site_category = f'{site}_{selected_category}'
    
    start = request.session[site_category]['start']
    end = request.session[site_category]['end']
    
    while start<=end:
        try:
            request.session[site_category]['urls_to_scrape'].append(
                request.session[site_category]['urls_all'][start]
            )
        except IndexError as e:
            print(e)
            request.session[site_category]['page'] +=  1
            page_part = scraper.site_variables_dict[site]['page_suffix'].format(request.session[site_category]['page']) 
            urls = scraper.scrape_article_urls(
                f"{scraper.site_variables_dict[site][selected_category]}{page_part}"
            )
            request.session[site_category]['urls_all'] = urls
            start,end = 0, end-start
            request.session[site_category]['urls_to_scrape'].append(
                request.session[site_category]['urls_all'][start]
            )
        
        start += 1
    request.session[site_category]['start'] = start
    request.session[site_category]['end'] = end + 3    
            
            
def get_next_urls(request, sites):
    selected_category = request.session['selected_category']
    if selected_category == 'front_page':
        selected_category = 'main'

    

    ttt = []
    for site in sites:
        site_category = f'{site}_{selected_category}'

        ttt.append(request.session[site_category]['urls_to_scrape'])
        request.session[site_category]['urls_to_scrape'] = []
    
    urls = [item for sublist in zip(*ttt) for item in sublist]
    return urls

    
def scrape_urls(request, site, scraper):
    # doesn't return anything, updates the session variables
    selected_category = request.session['selected_category']
    if selected_category == 'front_page':
        selected_category = 'main'
        hrefs_to_find_urls = scraper.site_variables_dict[site][selected_category]
    else:
        hrefs_to_find_urls = scraper.site_variables_dict[site]['topics'][selected_category]

    site_category = f'{site}_{selected_category}'
    if not request.session.get(site_category,None):
        urls = scraper.scrape_article_urls(hrefs_to_find_urls)
        request.session[site_category] = {
            'urls_all': urls,
            'urls_to_scrape': [],
            'page' : 1,
            'start': 0,
            'end': 2,
            
    }
    use_generator(request,site,selected_category,scraper)




