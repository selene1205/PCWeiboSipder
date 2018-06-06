# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Item,Field



class weiboItem(Item):
    """ 个人信息 """
    mid = Field()
    w_time = Field()
    weibo_url = Field()
    zhuanfa_num = Field()
    pinglun_num = Field()
    weibo_str = Field()
    keyword = Field()




class zhuanfaItem(Item):
    """ 微博信息 """
    zhuanfa_mid = Field()
    mid = Field()
    zhuanfa_str = Field()
    zhuanfa_time = Field()
    keyword = Field()




class pinglunItem(Item):
    """ 微博信息 """
    comment_id = Field()
    mid = Field()
    pinglun_str = Field()
    pinglun_time = Field()
    keyword = Field()
