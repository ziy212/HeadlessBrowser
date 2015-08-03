from scrapy.selector import HtmlXPathSelector
from scrapy.spiders import Spider
from scrapy.http import Request

DOMAIN = 'taobao.com'
URL = 'http://www.%s' % DOMAIN
url='http://world.taobao.com/item/44235973193.htm'


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

