from TinyScrapy.tinyScrapy import Request


class BaiduSpider(object):
    def start_requests(self):
        start_urls = [
            'https://blog.csdn.net/weixin_37947156/article/details/74435304',
            'https://www.baidu.com/',
            'https://blog.csdn.net/weixin_37947156/article/list/3',
        ]

        for url in start_urls:
            yield Request(url=url, callback=self.parse)

    def parse(self, response):
        print(response.request.url, '！！！！')
        yield Request(url='https://pagespeed.v2ex.com/go/cv?p=1', callback=self.parse2)
        yield Request(url='https://www.bilibili.com/', callback=self.parse2)

    def parse2(self, response):
        print(response.request.url, '@@@@@@@@@@')
