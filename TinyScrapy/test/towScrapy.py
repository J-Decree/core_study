from twisted.internet import reactor
from twisted.internet import defer
from twisted.web.client import getPage
from queue import Queue
import types

"""
需求分析
1.用户通过自定义Spider类的相关方法,并指定回调函数便可以完成基本爬虫
2.用户在处理respone的回调函数中，可以产生数个新的请求
3.用户将产生的数个请求也会被指定回调函数,借此可以形成一个'循环'，可以源源不断的爬取指定页面
"""

"""
角色与动作
1.引擎    -   封装了所有处理方法,高级的类
2.请求容器 -    队列
4.response类 -   结构体
5.Request类  -   结构体
"""
n = 0


class Request(object):
    def __init__(self, url, callback):
        self.url = url
        self.callback = callback


class Response(object):
    def __init__(self, request, text):
        self.request = request
        self.text = str(text, 'utf8')


class Spider(object):
    def start_request(self):
        start_urls = [
            'https://www.baidu.com/',
            'https://cn.bing.com/',
        ]

        for url in start_urls:
            yield Request(url=url, callback=self.parse)

    def parse(self, response):
        print(response.request.url,'parse!!!!!!')
        global n
        n += 1
        print(n)
        yield Request(url='http://kaito-blog.qiniudn.com/scrapy-arch.jpg', callback=self.myparse)
        yield Request(url='https://www.bilibili.com/', callback=self.myparse)

    def myparse(self, response):
        print(response.url, 'test@@@@@@@@@@@')


class Engine(object):
    def __init__(self):
        self._close = defer.Deferred()
        self.queue = Queue()
        self.max = 5
        self.crawing = []
        self._active = set()

    def craw(self, spider):
        for req in iter(spider.start_request()):
            self.queue.put(req)

        reactor.callLater(0, self._next_request)

    def handle_callback(self, content, req):
        self.crawing.remove(req)
        reactor.callLater(0, self._next_request)
        response = Response(text=content, request=req)
        res = req.callback(response)
        if isinstance(res, types.GeneratorType):
            for obj in req.callback(response):
                if isinstance(obj, Request):
                    print(obj.url, 'handlerfsdfdsdfsdfasd')
                    self.queue.put(obj)


    def _next_request(self, *args, **kwargs):
        for i in self.crawing:
            print(id(i))
        if len(self.crawing) == 0 and self.queue.qsize()==0:
            self._close.callback(None)
            return

        while len(self.crawing) < self.max:
            print('len(crawing)', len(self.crawing), 'qsize', self.queue.qsize())
            try:
                req = self.queue.get(block=False)
                print(req.url, *args)
                d = getPage(url=req.url.encode('utf8'))
                d.addCallback(self.handle_callback, req)
                d.addCallback(lambda _: reactor.callLater(0, self._next_request))
                self.crawing.append(req)
            except Exception as e:
                print(e)
                break

    def run(self):
        dd = defer.DeferredList([self._close, ])
        dd.addBoth(self.stop)
        reactor.run()

    def stop(self):
        print('stop!!!!!!!!!')
        reactor.stop()


if __name__ == '__main__':
    print(1)
    e = Engine()
    s = Spider()
    e.craw(s)
    e.run()
