from twisted.internet import reactor
from twisted.internet import defer
from twisted.web.client import getPage
from queue import Queue
import types

"""
角色与职责
一.!!Main类职责过于混乱,拆分为以下两类,方法是职责的分门别类

- CrawlerProcess(对应我的Main类)
@ 一言以蔽之：爬虫事件管理，即操纵内容为事件

- Crawler
@ 一言以蔽之：创建引擎，创建爬虫对象(.这里实现的方法是,一个爬虫对象对应一个引擎,一个门卫)
因为这些和事件处理类（CrawlerProcess）干的是完全不同的类别（行业）


- Command类
传入路径的类，真正的main类
定义路径,调用事件处理类启动。
____________________________________________________________________________

注意:由于引擎的_close(门卫)是用于停止事件的，属于事件层面的东西,所以要想办法直接或间接交给CrawlerProcess


"""


class Command(object):
    spider_paths = [
        "TinyScrapy.spider.baiduSpider.BaiduSpider",
        "TinyScrapy.spider.choutiSpider.ChoutiSpider"
    ]

    def run(self):
        event_processer = CrawlerProcess()
        for path in self.spider_paths:
            event_processer.craw(path)
        event_processer.start()


class CrawlerProcess(object):
    # 获得爬虫门卫（间接的操纵）
    def __init__(self):
        self._active = set()

    def craw(self, spider_path):
        # 压入被监视的defer对象
        crawler = Crawler()
        d = crawler.crawl(spider_path)
        self._active.add(d)

    def start(self):
        dd = defer.DeferredList(self._active)
        dd.addBoth(lambda *args: reactor.stop())
        reactor.run()


class Crawler(object):
    def _create_engine(self):
        # 统一接口,为了可替换
        return Engine.from_setting()

    def _create_spider(self, spider_path):
        # 解析路径,返回爬虫对象
        import importlib
        import_module, cls = spider_path.rsplit('.', 1)
        m = importlib.import_module(import_module)
        if hasattr(m, cls):
            cls = getattr(m, cls)
            return cls()
        else:
            raise Exception('the path of spider is error!')

    @defer.inlineCallbacks
    def crawl(self, spider_path):
        # 创建引擎，创建爬虫对象
        engine = self._create_engine()
        spider = self._create_spider(spider_path)

        yield engine.open_spider(spider)
        # 传递那几个爬虫的门卫出去
        yield engine.start()


class Engine(object):
    def __init__(self):
        self.max = 5
        self.crawlling = []
        self.scheduler = Scheduler()
        self._close = None  # 想了一下，还是在函数初始化较好，为了可变性

    @classmethod
    def from_setting(cls):
        # 类方法实例化
        obj = cls()
        # 增加属性...
        return obj

    def err_callback(self, req):
        self.crawlling.remove(req)
        print('Fail:', req.url)

    def ok_callback(self, content, req):
        self.crawlling.remove(req)
        response = Response(content, req)
        res = req.callback(response)
        if isinstance(res, types.GeneratorType):
            for obj in res:
                self.scheduler.put_task(obj)

        reactor.callLater(0, self._next_request)

    def _next_request(self):
        if self.scheduler.length == 0 and len(self.crawlling) == 0:
            self._close.callback(None)
            return

        while len(self.crawlling) < self.max:
            try:
                req = self.scheduler.get_task()
                self.crawlling.append(req)
                d = getPage(req.url.encode('utf-8'))
                d.addCallback(self.ok_callback, req)
                d.addCallback(self.err_callback, req)
                d.addCallback(lambda _: reactor.callLater(0, self._next_request))
            except Exception as e:
                print(e)
                return

    @defer.inlineCallbacks
    def start(self):
        self._close = defer.Deferred()
        yield self._close

    @defer.inlineCallbacks
    def open_spider(self, spider):
        for req in spider.start_requests():
            self.scheduler.put_task(req)
        reactor.callLater(0, self._next_request)
        yield None


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
        # 小细节,隐藏内部的实现细节所暴露出来的异常，替换成统一的异常
        try:
            task = self.container.get(block=False)
        except:
            raise Exception('container is empty')
        return task

    def is_empty(self):
        return self.container.empty()

    @property
    def length(self):
        return self.container.qsize()


if __name__ == '__main__':
    c = Command()
    c.run()
