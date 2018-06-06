# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from weiboSpider.user_agents import agents
# from weiboSpider.cookies import cookies
import redis
from scrapy import Request
import scrapy.downloadermiddlewares.retry
from scrapy.exceptions import IgnoreRequest
import base64
import random
import hashlib
import requests
import time
import logging

pool = redis.ConnectionPool(host="127.0.0.1", port="6379")
r = redis.Redis(connection_pool=pool)
logger = logging.getLogger("request")

# r.delete("cookie")

# r.sadd("cookie",*cookies)
# 获得cookie，每次第一次运行时启动一遍就好。

class ProxyMiddleware():
    # overwrite process request

    def generate_sign(self):
        appkey = "61512082"
        secret = "3bad36fe0d575e2c83298dbeb072b4c2"
        mayi_url = "s5.proxy.mayidaili.com"
        mayi_port = "8123"
        mayi_proxy = 'http://{}:{}'.format(mayi_url, mayi_port)

        paramMap = {
            "app_key": appkey,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        keys = sorted(paramMap)
        codes = "%s%s%s" % (secret, str().join('%s%s' % (key, paramMap[key]) for key in keys), secret)

        sign = hashlib.md5(codes.encode('utf-8')).hexdigest().upper()

        paramMap["sign"] = sign

        keys = paramMap.keys()
        authHeader = "MYH-AUTH-MD5 " + str('&').join('%s=%s' % (key, paramMap[key]) for key in keys)
        return authHeader, mayi_proxy



    def process_request(self, request, spider):

        authHeader, mayi_proxy = self.generate_sign()

        request.meta["proxy"] = mayi_proxy
        request.headers['Proxy-Authorization'] = authHeader



    def process_response(self, response, request, spider):


        return response


class UserAgentMiddleware():
    """ 换User-Agent """

    def process_request(self, request, spider):
        agent = random.choice(agents)
        request.headers["User-Agent"] = agent


class CookiesMiddleware():
    """ 换Cookie """

    def process_request(self, request, spider):
        if "remind.do" in request.url:
            meta =request.meta
            meta['retry_times']  =meta.get('retry_times',0) +1
            if request.meta.get('redirect_urls'):
                return Request(url=request.meta.get('redirect_urls')[0],meta=meta,callback=request.callback,dont_filter=True)

        if r'https://login.sina.com.cn/' in request.url:
            logging.debug('cookie:{}'.format(request.cookies))
            logging.debug("帐号异常")
            logging.debug("成功删除{}条cookie".format(r.srem("cookie", str(request.cookies).replace("'",'"'))))
            meta =request.meta
            meta['retry_times']  =meta.get('retry_times',0) +1
            if request.meta.get('redirect_urls'):
                logging.debug("retry:{}".format(request.meta.get('redirect_urls')[0]))
                return Request(url=request.meta.get('redirect_urls')[0],meta=meta,callback=request.callback,dont_filter=True,priority=20)
        cookie = r.srandmember("cookie").decode()
        request.cookies = eval(cookie)


    def process_response(self, response, request, spider):
        if '帐号异常' in response.text or '犯愁苍白猜测思' in response.text:
            logging.debug("帐号异常")
            logging.debug("删除{}条cookie".format(r.srem("cookie", str(request.cookies).replace("'",'"'))))
        if r'\u60a8\u53ef\u4ee5\u5c1d\u8bd5\u66f4\u6362\u5173\u952e\u8bcd\uff0c\u518d\u6b21\u641c\u7d22\u3002' in response.text:
            logging.debug("没有内容")
            raise IgnoreRequest
        return response
