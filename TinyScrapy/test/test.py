from twisted.internet import reactor  # 事件循环（终止条件，所有的socket都已经移除）
from twisted.web.client import getPage  # socket对象（如果下载完成，自动从时间循环中移除...）
from twisted.internet import defer  # defer.Deferred 特殊的socket对象 （不会发请求，手动移除）


def response(content, *args, **kwargs):
    print('okokok')
    # print(args, kwargs)
    # print(content)


def response2(content, *args, **kwargs):
    print('errrrrr')
    print(args, kwargs)
    # print(content)


# 停止事件循环函数
def stop(*args, **kwargs):
    # twisted 就是个扑街,这个函数一定要有可变参数，不然不会执行，也不会报错
    print(args, kwargs)
    print('to stop')
    reactor.stop()
    print('stop ok')


@defer.inlineCallbacks
def task1():
    d = getPage(url='https://www.baidu.1com'.encode('utf8'))
    d.addCallback(response)
    d.addErrback(response2)
    yield d


if __name__ == '__main__':
    d1 = task1()
    dd = defer.DeferredList([d1, ])
    dd.addBoth(lambda _: reactor.stop())
    reactor.run()
