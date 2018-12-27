from twisted.internet import reactor
from twisted.internet import defer
from twisted.web.client import getPage
from queue import Queue

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


class Request(object):
    def __init__(self, url, callback):
        self.url = url
        self.callback = callback


class Response(object):
    # 这里把原来的返回二进制也封装进去了,因为如果是图片的话,便可以使用,想得周到
    def __init__(self, content, request):
        self.content = content
        self.request = request
        self.text = str(content,encoding='utf-8')


class Spider(object):
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


q = Queue()


class Engine(object):
    def __init__(self):
        self._close = defer.Deferred()  # 初始化为None,可我觉得直接初始化比较好
        self.max = 5
        self.crawing = []

    # 这个加上装饰器，为yield _close
    @defer.inlineCallbacks
    def crawl(self, spider):
        start_requests = iter(spider.start_requests())
        for req in start_requests:
            q.put(req)
        # 存入任务调度器之后下一步就是取出来
        reactor.callLater(0, self._next_request)

        yield self._close

    def _next_request(self):
        if q.qsize() == 0 and len(self.crawing) == 0:
            self._close.callback(None)
            return
        while len(self.crawing) < self.max:
            try:
                req = q.get(block=False)
                self.crawing.append(req)
                d = getPage(req.url.encode('utf8'))
                d.addCallback(self.hanlde_callback, req)
                d.addCallback(lambda _: reactor.callLater(0, self._next_request))
            except Exception as e:
                print(e)
                break


    def hanlde_callback(self, content, request):
        self.crawing.remove(request)
        response = Response(request=request, content=content)
        res = request.callback(response)
        import types
        if isinstance(res, types.GeneratorType):
            for req in res:
                q.put(req)




if __name__ == '__main__':
    spider = Spider()
    engine = Engine()
    d = engine.crawl(spider)

    dd = defer.DeferredList([d, ])
    dd.addBoth(lambda *args: reactor.stop())
    reactor.run()
