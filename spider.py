from scrapy.selector import HtmlXPathSelector
from scrapy.spiders import Spider
from scrapy.http import Request

DOMAIN = 'pawprintpets.com'
DOMAIN = 'boardshorts.com'
URL = 'http://www.%s' % DOMAIN
URL = 'http://165.124.182.209:10001/'


class MySpider(Spider):
    name = DOMAIN
    allowed_domains = [DOMAIN]
    start_urls = [
        URL
    ]

    def parse(self, response):
        hxs = HtmlXPathSelector(response)
        for url in hxs.select('//a/@href').extract():
            if not ( url.startswith('http://') or url.startswith('https://') ):
                url= URL + url 
            print url
            yield Request(url, callback=self.parse)

