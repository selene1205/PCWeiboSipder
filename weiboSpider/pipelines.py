# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html




import pymongo
from weiboSpider.items import weiboItem, zhuanfaItem,pinglunItem

import logging
logger = logging.getLogger(__name__)



class MongoDBPipeline(object):
    def __init__(self):
        clinet = pymongo.MongoClient("localhost", 27017)
        db = clinet["PCweibo"]
        self.weibo_infrom = db["weibo"]
        self.pinglun_inform = db["pinglun"]
        self.zhuanfa_inform = db["zhuanfa"]

    def process_item(self, item, spider):
        """ 判断item的类型，并作相应的处理，再入数据库 """

        if isinstance(item, weiboItem):
            result = dict(item)
            try:
                self.weibo_infrom.update({"mid": result['mid']}, {'$set': result}, upsert=True)

            except Exception:
                pass
        elif isinstance(item, zhuanfaItem):
            result = dict(item)
            try:
                self.zhuanfa_inform.update({"zhuanfa_mid": result['zhuanfa_mid']}, {'$set': result}, upsert=True)
            except Exception:
                pass
        elif isinstance(item, pinglunItem):
            result = dict(item)
            try:
                self.pinglun_inform.update({"comment_id": result['comment_id']}, {'$set': result}, upsert=True)
            except Exception:
                pass
        return item





