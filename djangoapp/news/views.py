import datetime
import concurrent.futures
from functools import partial

from django.http import JsonResponse, HttpRequest
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views import generic
from django.utils import timezone
from django.db.models import Q


from .models import Article
from .forms import URLForm, SiteSelectionForm, SearchArticlesForm

from news.scripts.nlp import NLP
from news.scripts.llm import LocalLLM
from news.scripts.model_loader import ModelLoader
from news.scripts.scraping import NotSupportedWebsiteException, Scraper
from news.vertex.cloud.vertex_connection import VertexAI

# for type hinting
from typing import Optional, List
from transformers.pipelines.text2text_generation import SummarizationPipeline




class NoMoreUrlsException(Exception):
    pass


#############################################
#                 HELPERS                   #
#############################################

def get_model_loader_attributes() -> tuple([Scraper, NLP, LocalLLM, SummarizationPipeline, VertexAI]):
    """
    Returns the attributes of the model loader.
    Model loader is a singleton class, so it's attributes are the same for every instance.
    """
    model_loader = ModelLoader()
    scraper = model_loader.scraper
    nlp = model_loader.nlp
    vertex = model_loader.vertex
    llm = model_loader.llm
    summarizer = model_loader.summarizer
    return scraper, nlp, llm, summarizer, vertex

def classify_NLP(title:str, nlp:NLP) -> tuple([int, float]):
    """
    Returns the decision and the probability made by the NLP model.
    """
    clickbait_decision_NLP_proba = nlp.predict_on_text(title)
    clickbait_decision_NLP_proba = clickbait_decision_NLP_proba[0][1]
    decision = int(clickbait_decision_NLP_proba > nlp.proba_cutoff)
    probability = round(clickbait_decision_NLP_proba, 3)
    return decision, probability


def classify_LLM(title:str, llm:LocalLLM) -> tuple([int, float]):
    """
    Returns the decision and the probability made by the LLM model.
    """
    probability = llm.predict(title)
    decision = int(probability > llm.proba_cutoff)
    probability = round(probability, 3)
    return decision, probability


def classify_VERTEX(title:str, vertex:VertexAI, summary:str=None):
    """
    Returns the decision made by the VertexAI model.
    If the models fails to load or there is an error, returns -1.
    -1 means that the model failed to make a decision.
    """
    try:
        if summary:
            clickbait_decision_VERTEX = vertex.run(title=title, summary=summary)
        else:
            clickbait_decision_VERTEX = vertex.run(title=title)
        return int(clickbait_decision_VERTEX)
    except:
        return -1


def make_final_decision(
    clickbait_decision_NLP:int, clickbait_decision_LLM:int, clickbait_decision_VERTEX:int
) -> int:
    if clickbait_decision_VERTEX != -1:
        return int(
            clickbait_decision_NLP + clickbait_decision_LLM + clickbait_decision_VERTEX
        )

    decisions = [clickbait_decision_NLP, clickbait_decision_LLM]
    sum_ = sum(decisions)
    if sum_ == 0:
        return 0
    elif sum_ == 1:
        return 2
    elif sum_ == 2:
        return 3
    return -1


def process_article(url:str, scraper:Scraper, nlp:NLP, llm:LocalLLM, summarizer:SummarizationPipeline, vertex:VertexAI, selected_category:str) -> Optional[Article]:
    """
    This function scrapes the article from the url, classifies it and saves it to the database if it doesn't exist.
    If the article already exists in the database, it returns it.
    The function returns None if there have been any errors during the process.
    """
    try:
        article = Article.objects.get(url_from=url)
        return article
    except:
        try:
            scraped_data = scraper.scrape(url)
            scraped_data["url"] = url
            title = scraped_data["title"]
            clickbait_decision_NLP, clickbait_probability_NLP = classify_NLP(title, nlp)
            clickbait_decision_LLM, clickbait_probability_LLM = classify_LLM(title, llm)
            content_summary = summarizer(
                scraped_data["content"], max_length=200, min_length=40, do_sample=False
            )[0]["summary_text"].replace(" .", ".")
            vertex = VertexAI()
            clickbait_decision_VERTEX = classify_VERTEX(title, vertex, content_summary)

            clickbait_decision_final = make_final_decision(
                clickbait_decision_NLP,
                clickbait_decision_LLM,
                clickbait_decision_VERTEX,
            )
            article = Article(
                title=title,
                url_from=url,
                content_summary=content_summary,
                source_site=scraped_data["source_site"],
                category=selected_category,
                clickbait_decision_NLP=clickbait_decision_NLP,
                clickbait_probability_NLP=clickbait_probability_NLP,
                clickbait_decision_LLM=clickbait_decision_LLM,
                clickbait_probability_LLM=clickbait_probability_LLM,
                clickbait_decision_VERTEX=clickbait_decision_VERTEX,
                clickbait_decision_final=clickbait_decision_final,
            )
            article.save()
            return article
        except Exception as e:
            print(e)
            return None
        

def get_articles(request:HttpRequest, selected_sites:List[str]=None, selected_category:str=None) -> List[Article]:  
    """
    This function is used to get the articles from the selected sites and categories.
    """

    scraper, nlp, llm, summarizer, vertex = get_model_loader_attributes()

    if not selected_sites or not selected_category:
    # Get the session variables, from the scrape_articles view
        selected_sites = request.session["selected_sites"]
        selected_category = request.session["selected_category"]


    for site in selected_sites:
        use_generator(request, site, selected_category, scraper)
    urls = get_next_urls(request, selected_sites)
    process_article_partial = partial(
        process_article,
        scraper=scraper,
        nlp=nlp,
        llm=llm,
        summarizer=summarizer,
        vertex=vertex,
        selected_category=selected_category,
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        articles = list(executor.map(process_article_partial, urls))
        articles = [el for el in articles if el is not None]
    return articles



#############################################
#                 VIEWS                     #
#############################################


class DetailView(generic.DetailView):
    """
    This view is used to display the details of a single article.
    """
    model = Article
    template_name = "news/detail.html"

    def get_queryset(self):
        return Article.objects.filter(scraped_date__lte=timezone.now())


def check_url(request:HttpRequest):
    """
    This view is used to check the url of a single article provided by the user.
    """
    if request.method == "POST":
        form = URLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data["url"]

            # Access the loaded models
            scraper, nlp, llm, summarizer, vertex = get_model_loader_attributes()

            article = process_article(
                url, scraper, nlp, llm, summarizer, vertex, selected_category="UNKNOWN"
            )

            html_content = render_to_string(
                "news/article_info.html", {"article": article}
            )
            return JsonResponse({"html": html_content})
    else:
        form = URLForm()

    return render(request, "news/check_url.html", {"form": form})



def scrape_articles(request:HttpRequest):
    """
    This view is used to scrape articles from the selected sites and categories.
    It accepts a POST request with the form data and returns a JsonResponse with the html of the scraped articles.
    There are at most 9 threads running at the same time correstponding to the maxium number of articles returned by this view.
    """
    if request.method == "POST":
        form = SiteSelectionForm(request.POST)
        if form.is_valid():
            # Process the form data, and remember them in the session
            selected_sites = [
                key
                for key, value in form.cleaned_data.items()
                if value and key not in ["clickbait_tolerance", "category"]
            ]
            selected_category = form.cleaned_data["category"]

            request.session["selected_sites"] = selected_sites
            request.session["selected_category"] = selected_category

            articles = get_articles(request, selected_sites, selected_category)

            articles_html = render_to_string(
                "news/list_articles.html", {"latest_article_list": articles}
            )
            return JsonResponse({"articles_html": articles_html})
    else:
        form = SiteSelectionForm()

    return render(request, "news/index.html", {"form": form})



def load_more_articles(request:HttpRequest) -> JsonResponse:
    """
    This is a view used to load more articles from the selected sites and categories.
    It is only possible to be called after the scrape_articles view.
    """
   
    articles = get_articles(request)
    request.session.save()
    articles_html = render_to_string(
        "news/list_articles.html", {"latest_article_list": articles}
    )
    return JsonResponse({"articles_html": articles_html})


def browse_articles(request):
    """
    This view used to browse the articles in the database.
    """
    if request.method == "POST":
        form = SearchArticlesForm(request.POST)
        if form.is_valid():
            search_query = form.cleaned_data["search_query"]
            date_scraped_from = form.cleaned_data["date_scraped_from"]
            date_scraped_to = form.cleaned_data[
                "date_scraped_from"
            ] + datetime.timedelta(days=1)
            clickbait_tolerance = int(form.cleaned_data["clickbait_tolerance"])

            thesun = form.cleaned_data["thesun"]
            cbsnews = form.cleaned_data["cbsnews"]
            abcnews = form.cleaned_data["abcnews"]

            # Use the form data as needed to filter the articles from the database

            query = Q()

            # Add conditions based on form fields
            if search_query:
                query &= Q(title__icontains=search_query) | Q(
                    content_summary__icontains=search_query
                )

            query &= Q(clickbait_decision_final__lte=clickbait_tolerance)

            query &= Q(scraped_date__gte=date_scraped_from) & Q(
                scraped_date__lte=date_scraped_to
            )

            source_sites = []
            if thesun:
                source_sites.append("The Sun UK")
            if cbsnews:
                source_sites.append("CBS News")
            if abcnews:
                source_sites.append("ABC News")

            if source_sites:
                query &= Q(source_site__in=source_sites)

            articles = Article.objects.filter(query).order_by("-scraped_date")
            context = {"form": form}
            context["latest_article_list"] = articles
            return render(request, "news/browse.html", context=context)

    else:
        form = SearchArticlesForm()

    articles = Article.objects.order_by("-scraped_date")[:10]
    context = {"form": form, "latest_article_list": articles}
    return render(request, "news/browse.html", context=context)


def use_generator(request, site, selected_category, scraper):
    # doesn't return anything, updates the session variables
    if selected_category == "front_page":
        selected_category = "main"
    site_category = f"{site}_{selected_category}"

    start = request.session[site_category]["start"]
    end = request.session[site_category]["end"]

    print(
        f"{site_category}: {start} - {end}, page: {request.session[site_category]['page']}"
    )

    while start <= end:
        try:
            request.session[site_category]["urls_to_scrape"].append(
                request.session[site_category]["urls_all"][start]
            )
        except IndexError as e:
            print(e)
            if selected_category == "main" or site == "abcnews":
                # main sites and abcnews don't have pagination
                break
            # This situation means that there are no more urls on the current page, so we need to go to the next page
            request.session[site_category]["page"] += 1
            number = request.session[site_category]["page"]

            page_part = eval(f"f'{scraper.site_variables_dict[site]['page_suffix']}'")
            urls = scraper.scrape_article_urls(
                f"{scraper.site_variables_dict[site]['topics'][selected_category]}{page_part}"
            )
            if not urls:
                print("no urls")
            request.session[site_category]["urls_all"] = urls
            start, end = 0, 3
            request.session[site_category]["urls_to_scrape"].append(
                request.session[site_category]["urls_all"][start]
            )

        start += 1
    request.session[site_category]["start"] = start
    request.session[site_category]["end"] = start + 3


def get_next_urls(request, sites):
    selected_category = request.session["selected_category"]
    if selected_category == "front_page":
        selected_category = "main"

    site_url_lists = []
    for site in sites:
        site_category = f"{site}_{selected_category}"
        url_list = request.session[site_category]["urls_to_scrape"]
        if url_list:
            site_url_lists.append(url_list)
            request.session[site_category]["urls_to_scrape"] = []

    urls = [item for sublist in zip(*site_url_lists) for item in sublist]
    if not urls:
        raise NoMoreUrlsException(
            "There are no more urls to scrape from this category."
        )
    return urls


def scrape_urls(request, site, scraper):
    # doesn't return anything, updates the session variables
    selected_category = request.session["selected_category"]
    if selected_category == "front_page":
        selected_category = "main"
        hrefs_to_find_urls = scraper.site_variables_dict[site][selected_category]
    else:
        hrefs_to_find_urls = scraper.site_variables_dict[site]["topics"][
            selected_category
        ]

    site_category = f"{site}_{selected_category}"
    if not request.session.get(site_category, None):
        urls = scraper.scrape_article_urls(hrefs_to_find_urls)
        if not urls:
            print(f"No urls found for {site_category}")
        request.session[site_category] = {
            "urls_all": urls,
            "urls_to_scrape": [],
            "page": 1,
            "start": 0,
            "end": 2,
        }
    if site_category == "cbsnews_Sports":
        request.session.save()
    else:
        use_generator(request, site, selected_category, scraper)
