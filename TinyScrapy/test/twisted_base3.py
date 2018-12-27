from twisted.internet import reactor  # 事件循环（终止条件，所有的socket都已经移除）
from twisted.web.client import getPage  # socket对象（如果下载完成，自动从时间循环中移除...）
from twisted.internet import defer  # defer.Deferred 特殊的socket对象 （不会发请求，手动移除）

_close = defer.Deferred()
count = 0


def response(content):
    print(content)

    # 链接数全部收到，干掉'门卫'
    global count
    count += 1
    print(count)
    if count == 2:
        _close.callback(None)


# 停止事件循环函数
def stop(*args, **kwargs):
    # twisted 就是个扑街,这个函数一定要有可变参数，不然不会执行，也不会报错
    print(args, kwargs)
    print('to stop')
    reactor.stop()
    print('stop ok')


@defer.inlineCallbacks
def task1():
    # yield是获取执行动作的结果状态，用作于监视列表监视
    # getpage是不阻塞,如果多次yield一定要注意,如果d1的动作没有发生异常,则会继续yield剩下的动作
    # 若前面的yield出异常,则后面的yield不执行
    d1 = getPage(url='https://blog.csdn.net/weixin_37947156/article/details/74533108'.encode('utf8'))
    d1.addCallback(response)

    d2 = getPage(url='http://kaito-blog.qiniudn.com/scrapy-arch.jpg'.encode('utf8'))
    d2.addCallback(response)

    yield _close


if __name__ == '__main__':
    d1 = task1()
    active_list = [d1, ]
    dd = defer.DeferredList(active_list)
    dd.addBoth(stop)
    reactor.run()
