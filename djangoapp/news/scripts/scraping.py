import requests
import re
import json
from bs4 import BeautifulSoup


class NotSupportedWebsiteException(Exception):
    pass

class Scraper:
    def __init__(self, path_to_site_variables: str):
        self.site_variables_dict = self.get_site_variables_dict(path_to_site_variables)

    @staticmethod
    def get_site_variables_dict(path: str) -> dict:
        # read json file
        with open(path, "r") as f:
            site_variables_dict = json.load(f)
        return site_variables_dict

    def scrape_article_urls(self, main_url: str) -> list[str]:
        response = requests.get(main_url)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise Exception(
                f"HTTP request failed with status code {response.status_code}"
            ) from e

        soup = BeautifulSoup(response.text, "html.parser")

        site_variables = self.discern_website_from_url(main_url)

        url_matchings = site_variables.get("url_matchings")
        compiled_excluded_patterns = []
        compiled_included_patterns = []
        # compile regex patterns
        if url_matchings.get("excluded_patterns"):
            compiled_excluded_patterns = [
                re.compile(pattern.replace("\\\\", "\\"))
                for pattern in url_matchings["excluded_patterns"]
            ]
        if url_matchings.get("included_patterns"):
            compiled_included_patterns = [
                re.compile(pattern.replace("\\\\", "\\"))
                for pattern in url_matchings["included_patterns"]
            ]

        all_hrefs = [a["href"] for a in soup.find_all("a", href=True)]
        url_matchings = site_variables["url_matchings"]
        matching_hrefs = [
            f'https://thesun.co.uk{href}' if href.startswith('/') else href
            for href in all_hrefs
            if self.check_href_match_condition(
                href,
                url_matchings,
                compiled_excluded_patterns,
                compiled_included_patterns,
            )
        ]
        matching_hrefs = list(dict.fromkeys(matching_hrefs))
        return matching_hrefs

    def discern_website_from_url(self, url: str) -> dict:
        if url.startswith("https://www.cbssports.com"):
            return self.site_variables_dict["cbsnews"]

        site_variables = next(
            (
                site_dict
                for key, site_dict in self.site_variables_dict.items()
                if url.startswith(f"https://www.{key}")
                or url.startswith(f"https://{key}")
            ),
            None,
        )
        if not site_variables:
            raise NotSupportedWebsiteException(
                f"Scraping for this website is not supported. Supported websites are: {', '.join(self.site_variables_dict.keys())}"
            )
        return site_variables

    @staticmethod
    def check_href_match_condition(
        url, url_matchings, compiled_excluded_patterns, compiled_included_patterns
    ):
        excluded_patterns_match_condition = True
        if compiled_excluded_patterns:
            excluded_patterns_match_condition = not any(
                pattern.match(url) for pattern in compiled_excluded_patterns
            )

        included_patterns_match_condition = False
        if compiled_included_patterns:
            included_patterns_match_condition = any(
                pattern.match(url) for pattern in compiled_included_patterns
            )

        starts_with_match_condition = True
        if url_matchings.get("starts_with"):
            starts_with_match_condition = any(
                url.startswith(starts_with)
                for starts_with in url_matchings["starts_with"]
            )
        return (
            starts_with_match_condition and excluded_patterns_match_condition
        ) or included_patterns_match_condition

    @staticmethod
    def scrape_content(
        url: str,
        paragraph_tag: str,
        title_tag: str,
        subtitle_tag: str = None,
        exclude: list[str] = [],
    ) -> dict[str, str]:
        response = requests.get(url)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise Exception(
                f"HTTP request failed with status code {response.status_code}"
            ) from e

        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find(title_tag).text
        subtitle = soup.find(subtitle_tag).text if subtitle_tag else None

        content = ""
        content_list = []
        paragraphs = soup.find_all(paragraph_tag)
        for paragraph in paragraphs:
            wrapper_elements_class = paragraph.find_parent(class_=exclude)
            wrapper_elements_id = paragraph.find_parent(id=exclude)

            element_class = paragraph.get("class", None)
            common_class = {}
            if element_class and exclude:
                common_class = set(element_class).intersection(exclude)

            element_id = paragraph.get("id", None)
            common_id = {}
            if element_id and exclude:
                common_id = set(element_id).intersection(exclude)

            if (
                wrapper_elements_class
                or wrapper_elements_id
                or common_class
                or common_id
            ):
                continue

            content_list.append(paragraph.text.strip())
            content = " ".join(content_list)

        special_chars_trans = str.maketrans(
            {"\n": " ", "\xa0": " ", "\t": " ", "'": "'"}
        )

        result = {
            "title": title.translate(special_chars_trans).strip() if title else None,
            "subtitle": subtitle.translate(special_chars_trans).strip()
            if subtitle
            else None,
            "content": content.translate(special_chars_trans).strip()
            if content
            else None,
        }

        return result

    def scrape(self, url: str):
        if not url.startswith("http://") and not url.startswith("https://"):
            raise NotSupportedWebsiteException(
                f"Scraping for this website is not supported. Supported websites are: {', '.join(self.site_variables_dict.keys())}"
            )
        site_dict = self.discern_website_from_url(url)
        result_dict = self.scrape_content(
            url,
            site_dict["paragraph_tag"],
            site_dict["title_tag"],
            exclude=site_dict["exclude"],
        )
        result_dict["source_site"] = site_dict["source_site"]
        return result_dict
