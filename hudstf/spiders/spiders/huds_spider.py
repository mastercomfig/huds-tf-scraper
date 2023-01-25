import hashlib
import re

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import TextResponse

from bs4 import BeautifulSoup

class HudsSpider(CrawlSpider):
    name = 'huds'
    allowed_domains = ['huds.tf']
    start_urls = [
      'https://huds.tf/site/d-HUD',
    ]
    rules = (
      Rule(LinkExtractor(canonicalize=True), follow=True, callback='parse_item'),
    )

    def parse_item(self, response):
      if isinstance(response, TextResponse):
        soup = BeautifulSoup(response.text)
        text = soup.get_text(separator=" ", strip=True)

        yield {
          "pageid": hashlib.blake2b(response.url.encode("utf-8")).hexdigest(),
          "url": response.url,
          "title": soup.find("title").string.split(" - ")[1],
          "body": text
        }