"""Views for the news app."""
import datetime
import concurrent.futures
from functools import partial
from typing import Optional, List

from django.http import JsonResponse, HttpRequest
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views import generic
from django.utils import timezone
from django.db.models import Q

from news.scripts.nlp import NLP
from news.scripts.llm import LocalLLM
from news.scripts.model_loader import ModelLoader
from news.scripts.scraping import Scraper
from news.vertex.cloud.vertex_connection import VertexAI
from transformers.pipelines.text2text_generation import SummarizationPipeline

from .models import Article
from .forms import URLForm, SiteSelectionForm, SearchArticlesForm


# for type hinting


class NoMoreUrlsException(Exception):
    """
    This exception is raised when there are not more urls to scrape.
    If this exception is raised, the user should be notified to change the scraped category.
    """
    def __init__(self, message="There are no more urls to scrape from this category."):
        super().__init__(message)


#############################################
#                 HELPERS                   #
#############################################


def get_model_loader_attributes() -> (
    tuple([Scraper, NLP, LocalLLM, SummarizationPipeline, VertexAI])
):
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


def classify_nlp(title: str, nlp: NLP) -> tuple([int, float]):
    """
    Returns the decision and the probability made by the NLP model.
    """
    clickbait_decision_nlp_proba = nlp.predict_on_text(title)
    clickbait_decision_nlp_proba = clickbait_decision_nlp_proba[0][1]
    decision = int(clickbait_decision_nlp_proba > nlp.proba_cutoff)
    probability = round(clickbait_decision_nlp_proba, 3)
    return decision, probability


def classify_llm(title: str, llm: LocalLLM) -> tuple([int, float]):
    """
    Returns the decision and the probability made by the LLM model.
    """
    probability = llm.predict(title)
    decision = int(probability > llm.proba_cutoff)
    probability = round(probability, 3)
    return decision, probability


def classify_vertex(title: str, vertex: VertexAI, summary: str = None):
    """
    Returns the decision made by the VertexAI model.
    If the models fails to load or there is an error, returns -1.
    -1 means that the model failed to make a decision.
    """
    try:
        if summary:
            clickbait_decision_vertex = vertex.run(title=title, summary=summary)
        else:
            clickbait_decision_vertex = vertex.run(title=title)
        return int(clickbait_decision_vertex)
    except Exception as e:  # pylint: disable=broad-except
        print(e)
        return -1


# pylint: disable=too-many-arguments
# pylint: disable=too-many-locals
def process_article(
    url: str,
    scraper: Scraper,
    nlp: NLP,
    llm: LocalLLM,
    summarizer: SummarizationPipeline,
    selected_category: str,
) -> Optional[Article]:
    """This function scrapes the article from the url, classifies it
    and saves it to the database if it doesn't exist.
    If the article already exists in the database, it returns it.
    The function returns None if there have been any errors
    during the process.
    """

    article = Article.objects.filter(url_from=url).first()
    if article:
        return article
    try:
        scraped_data = scraper.scrape(url)
        scraped_data["url"] = url
        title = scraped_data["title"]
        clickbait_decision_nlp, clickbait_probability_nlp = classify_nlp(title, nlp)
        clickbait_decision_llm, clickbait_probability_llm = classify_llm(title, llm)
        content_summary = summarizer(
            scraped_data["content"], max_length=200, min_length=40, do_sample=False
        )[0]["summary_text"].replace(" .", ".")
        vertex = VertexAI()
        clickbait_decision_vertex = classify_vertex(title, vertex, content_summary)

        article = Article(
            title=title,
            url_from=url,
            content_summary=content_summary,
            source_site=scraped_data["source_site"],
            category=selected_category,
            clickbait_decision_nlp=clickbait_decision_nlp,
            clickbait_probability_nlp=clickbait_probability_nlp,
            clickbait_decision_llm=clickbait_decision_llm,
            clickbait_probability_llm=clickbait_probability_llm,
            clickbait_decision_vertex=clickbait_decision_vertex,
        )
        article.make_final_decision()
        article.save()
        return article
    except Exception as e:  # pylint: disable=broad-except
        print(e)
        return None


# pylint: enable=too-many-arguments
# pylint: enable=too-many-locals


def get_articles(
    request: HttpRequest,
    selected_sites: List[str] = None,
    selected_category: str = None,
    load_more=False,
) -> List[Article]:
    """
    This function is used to get the articles from the selected sites and categories.
    """

    scraper, nlp, llm, summarizer, _ = get_model_loader_attributes()

    if not selected_sites or not selected_category:
        # Get the session variables, from the scrape_articles view
        selected_sites = request.session["selected_sites"]
        selected_category = request.session["selected_category"]

    for site in selected_sites:
        if load_more:
            update_session_variables(request, site, selected_category, scraper)
        else:
            scrape_urls(request, site, selected_category, scraper)
    urls = get_next_urls(request, selected_sites)
    process_article_partial = partial(
        process_article,
        scraper=scraper,
        nlp=nlp,
        llm=llm,
        summarizer=summarizer,
        selected_category=selected_category,
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=9) as executor:
        articles = list(executor.map(process_article_partial, urls))
        articles = [
            el
            for el in articles
            if el is not None
        ]
    return articles


def update_session_variables(
    request: HttpRequest, site: str, selected_category: str, scraper: Scraper
) -> None:
    """
    This function is used to update the session when the users scrapes many articles.
    It is used to keep track of the urls that have been scraped per site and category.
    If the user changes the category or the sites, the session variables are kept track of.
    This is the function that stops the user from scraping the same urls again and limits
    the number of urls that can be scraped per click to 3 per site.
    """
    site_category = f"{site}_{selected_category}"

    start = request.session[site_category]["start"]
    end = request.session[site_category]["end"]

    print(
        f"{site_category}, articles: {start} - {end},",
        f"page: {request.session[site_category]['page']}",
    )

    while start <= end:
        try:
            request.session[site_category]["urls_to_scrape"].append(
                request.session[site_category]["urls_all"][start]
            )
        except IndexError:
            if (
                selected_category == "Front Page"
                or site == "abcnews"
                or site_category == "cbsnews_Sports"
            ):
                # main sites and abcnews don't have pagination
                break

            # This situation means that there are no more urls on the current page,
            # so we need to go to the next page
            request.session[site_category]["page"] += 1
            page_suffix = scraper.site_variables_dict[site]["page_suffix"]
            page = request.session[site_category]["page"]
            page_part = f"{page_suffix}{page}"
            urls = scraper.scrape_article_urls(
                f"{scraper.site_variables_dict[site]['topics'][selected_category]}{page_part}"
            )
            request.session[site_category]["urls_all"] = urls
            start, end = 0, 2
            request.session[site_category]["urls_to_scrape"].append(
                request.session[site_category]["urls_all"][start]
            )

        start += 1
    request.session[site_category]["start"] = start
    request.session[site_category]["end"] = start + 2


def get_next_urls(request: HttpRequest, sites: List[str] = None) -> List[str]:
    """
    This function is used to get the next urls from the selected sites and categories.
    """

    selected_category = request.session["selected_category"]
    site_url_lists = []
    for site in sites:
        site_category = f"{site}_{selected_category}"
        url_list = request.session[site_category]["urls_to_scrape"]
        if url_list:
            site_url_lists.append(url_list)
            request.session[site_category]["urls_to_scrape"] = []

    urls = [item for sublist in zip(*site_url_lists) for item in sublist]
    if not urls:
        raise NoMoreUrlsException()
    return urls


def scrape_urls(
    request: HttpRequest, site: str, selected_category: str, scraper: Scraper
) -> None:
    """
    This function is used to scrape the urls from the selected sites and categories.
    It scrapes all the available urls from the selected sites and categories and
    stores them in session variables.
    """
    selected_category = request.session["selected_category"]
    if selected_category == "Front Page":
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
        # cbsnews_Sports have a different site structure than the other sites
        # we don't support this for now
        request.session.save()

    else:
        update_session_variables(request, site, selected_category, scraper)




def create_sites_list(form:SearchArticlesForm):
    """
    Used in browse_articles view.
    Returns a list of the selected sites from the form.
    """
    thesun = form.cleaned_data["thesun"]
    cbsnews = form.cleaned_data["cbsnews"]
    abcnews = form.cleaned_data["abcnews"]
    source_sites = []
    if thesun:
        source_sites.append("The Sun UK")
    if cbsnews:
        source_sites.append("CBS News")
    if abcnews:
        source_sites.append("ABC News")

    return source_sites


def create_categories_list(form:SearchArticlesForm) -> Optional[List[str]]:
    """
    Used in browse_articles view.
    Returns a list of the selected categories from the form.
    """
    front_page = form.cleaned_data["front_page"]
    world = form.cleaned_data["World"]
    politics = form.cleaned_data["Politics"]
    sports = form.cleaned_data["Sports"]
    health = form.cleaned_data["Health"]
    technology = form.cleaned_data["Technology"]
    if any([front_page, world, politics, sports, health, technology]):
        categories = []
        if front_page:
            categories.append("Front Page")
        if world:
            categories.append("World")
        if politics:
            categories.append("Politics")
        if sports:
            categories.append("Sports")
        if health:
            categories.append("Health")
        if technology:
            categories.append("Technology")
        return categories
    return None


def filter_articles_post(form:SearchArticlesForm, request: HttpRequest):
    """
    Used in browse_articles view.
    This function is used to filter the articles in the database.
    """
    search_query = form.cleaned_data["search_query"]
    date_scraped_from = form.cleaned_data["date_scraped_from"]
    date_scraped_to = form.cleaned_data["date_scraped_to"] + datetime.timedelta(days=1)
    clickbait_tolerance = int(form.cleaned_data["clickbait_tolerance"])

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

    source_sites = create_sites_list(form)

    if source_sites:
        query &= Q(source_site__in=source_sites)

    categories = create_categories_list(form)
    if categories:
        query &= Q(category__in=categories)

    articles = Article.objects.filter(query).order_by("-scraped_date")
    context = {"form": form, "latest_article_list": articles}

    return render(request, "news/browse.html", context=context)

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


def check_url(request: HttpRequest):
    """
    This view is used to check the url of a single article provided by the user.
    """
    if request.method == "POST":
        form = URLForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data["url"]

            # Access the loaded models
            scraper, nlp, llm, summarizer, _ = get_model_loader_attributes()

            article = process_article(url, scraper, nlp, llm, summarizer, "UNKNOWN")

            html_content = render_to_string(
                "news/article_info.html", {"article": article}
            )
            return JsonResponse({"html": html_content})
    else:
        form = URLForm()

    return render(request, "news/check_url.html", {"form": form})


def scrape_articles(request: HttpRequest):
    """
    This view is used to scrape articles from the selected sites and categories.
    It accepts a POST request with the form data and returns a JsonResponse with
    the html of the scraped articles. There are at most 9 threads running at the
    same time corresponding to the maximum number of articles returned by this view.
    """
    if request.method == "POST":
        form = SiteSelectionForm(request.POST)
        if form.is_valid():
            request.session["articles_html"] = ""
            # Process the form data, and remember them in the session
            selected_sites = [
                key
                for key, value in form.cleaned_data.items()
                if value and key != 'category'
            ]
            selected_category = form.cleaned_data["category"]

            request.session["selected_sites"] = selected_sites
            request.session["selected_category"] = selected_category

            articles = get_articles(
                request, selected_sites, selected_category
            )

            articles_html = render_to_string(
                "news/list_articles.html", {"latest_article_list": articles}
            )
            request.session["articles_html"] += articles_html
            return JsonResponse({"articles_html": articles_html})
    else:

        form = SiteSelectionForm()
    if request.session.get("articles_html", None):
        articles_html = request.session["articles_html"]
    else:
        articles_html = ""
    return render(
        request, "news/index.html", {"form": form, "articles_html": articles_html}
    )


def load_more_articles(request: HttpRequest) -> JsonResponse:
    """
    This is a view used to load more articles from the selected sites and categories.
    It is only possible to be called after the scrape_articles view.
    """

    articles = get_articles(request, load_more=True)
    articles_html = render_to_string(
        "news/list_articles.html", {"latest_article_list": articles}
    )
    request.session["articles_html"] += articles_html
    request.session.save()
    return JsonResponse({"articles_html": articles_html})


def browse_articles(request: HttpRequest):
    """
    This view used to browse the articles in the database.
    """
    if request.method == "POST":
        form = SearchArticlesForm(request.POST)
        if form.is_valid():
            return filter_articles_post(form, request)
    else:
        form = SearchArticlesForm()
    articles = Article.objects.order_by("-scraped_date")[:10]
    context = {"form": form, "latest_article_list": articles}
    return render(request, "news/browse.html", context=context)
