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
角色与职责
- 引擎类 
1.根据传入的爬虫类路径,创建出爬虫
2.处理将所有爬虫的种子放入调度器
3.从调度器中取出爬虫种子,并去指定页面下载,下载完成后会触发回调函数
4.将回调函数中产生的新种子放入调度器,并触发下一次请求处理


- 调度器类  
为了可扩展（便于更换底层处理的容易），再次封装

- main类(充当main函数职责,是一个底层类,处理事件循环,统领其他'上层'类）
1.维护事件循环
2.创建调度器，传递给引擎对象
3.创建引擎,获得并压入门卫defer，指定事件循环停止函数
4.解析爬虫路径,将解析好的参数传递给引擎类创建


- response类 -   不变
- Request类  -   不变

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
        self.text = str(content, encoding='utf-8')


class Scheduler(object):
    def __init__(self):
        self.container = Queue()

    def put_task(self, task):
        self.container.put(task)

    def get_task(self):
        task = self.container.get(block=False)
        return task

    def is_empty(self):
        return self.container.empty()

    @property
    def length(self):
        return self.container.qsize()


class Engine(object):
    def __init__(self, scheduler):
        self._close = defer.Deferred()
        self.spider_list = []
        self.scheduler = scheduler
        self.max = 5
        self.crawlling = []

    @defer.inlineCallbacks
    def crawler(self):
        for spider in self.spider_list:
            for req in spider.start_requests():
                self.scheduler.put_task(req)

        reactor.callLater(0, self._next_request)
        yield self._close

    def create_spider(self, cls):
        self.spider_list.append(cls())

    def _next_request(self):
        if len(self.crawlling) == 0 and self.scheduler.is_empty():
            self._close.callback(None)
            return
        while len(self.crawlling) < self.max:
            try:
                req = self.scheduler.get_task()
                self.crawlling.append(req)
                d = getPage(url=req.url.encode('utf8'))
                d.addCallback(self._handle_callback, req)
            except Exception as e:
                print(e)
                return

    def _handle_callback(self, content, req):
        self.crawlling.remove(req)
        response = Response(content, req)
        res = req.callback(response)
        if isinstance(res, types.GeneratorType):
            for obj in res:
                self.scheduler.put_task(obj)

        reactor.callLater(0,  self._next_request)


class Main(object):
    spider_paths = [
        "TinyScrapy.spider.baiduSpider.BaiduSpider",
        "TinyScrapy.spider.choutiSpider.ChoutiSpider"
    ]

    def _parse_path(self):
        ret = []
        import importlib
        for line in self.spider_paths:
            import_module, cls = line.rsplit('.', 1)
            m = importlib.import_module(import_module)
            if hasattr(m, cls):
                ret.append(getattr(m, cls))
        return ret

    def run(self):
        scheduler = Scheduler()
        e = Engine(scheduler)
        for cls in self._parse_path():
            e.create_spider(cls)

        d = e.crawler()
        dd = defer.DeferredList([d, ])
        dd.addBoth(lambda *args: reactor.stop())
        reactor.run()


if __name__ == '__main__':
    m = Main()
    m.run()
