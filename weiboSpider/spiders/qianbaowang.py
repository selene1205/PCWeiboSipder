# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.selector import Selector
from scrapy import Request
import datetime
import pymongo
import time
import lxml
from weiboSpider.items import weiboItem, zhuanfaItem,pinglunItem
import json
from scrapy.spiders import Spider
import redis
import logging
from lxml import html
import regex as re
from lxml import html
import requests
import os
import scrapy.spidermiddlewares.httperror


def get_time(w_time):
    now_time = datetime.datetime.now()
    pubtime = ""
    if "分钟" in w_time:
        minute = re.findall("\d*?(?=分钟)", w_time)
        if len(minute):
            pubtime = now_time - datetime.timedelta(minutes=int(minute[0]))
        pubtime = pubtime.strftime("%Y-%m-%d %H:%M")
    elif "今天" in w_time:

        hour, minute = re.findall("(?<=今天 )\d{2}:\d{2}", w_time)[0].split(":")
        if hour and minute:
            pubtime = now_time.strftime("%Y-%m-%d") + " " + hour + ":" + minute
    elif "月" in w_time and "日" in w_time:
        time = re.findall("\d{1,2}月\d{2}日 \d{2}:\d{2}", w_time)
        if len(time):
            pubtime = datetime.datetime.strptime("2017 " + time[0], "%Y %m月%d日 %H:%M").strftime("%Y-%m-%d %H:%M")

    elif len(re.findall("\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2}", w_time)):
        pubtime = re.findall("\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2}", w_time)[0]

    return pubtime


def get_str(weibo_content):
    weibo_str = ''
    for field in weibo_content:
        if isinstance(field, lxml.etree._ElementUnicodeResult):
            weibo_str += field
        elif field.tag == 'img':
            if field.attrib.get('class') == 'W_img_face':
                weibo_str += field.attrib['alt']
        elif field.tag == 'a':
            if field.attrib.get('render') == 'ext':
                if weibo_str[-2:] == '//':
                    weibo_str = weibo_str[:-2]
                    break
                weibo_str += field.xpath('string(.)')
            if field.attrib.get('class') in ['W_btn_c6', 'video_link']:
                break
    return weibo_str


def remov_emoji(text):
    emoji_pattern = re.compile(
        r"(\\ud83d......)|"  
        r"(\\ud83c......)|" 
        r"(\\ud83d......)|"  
        r"(\\ud83d......)|"  
        r"(\\ud83c......)"  
        "+", flags=re.UNICODE)
    return emoji_pattern.sub("",text)

keyword='钱宝网'
class WeiboSpider(Spider):

    clinet = pymongo.MongoClient("localhost", 27017)
    db = clinet["PCweibo"]
    weibo_infrom = db["weibo"]
    pinglun_inform = db["pinglun"]
    zhuanfa_inform = db["zhuanfa"]
    # proxies = {
    #     "http": "http://duoipesssplhp:1g3Z6uwIcoI4X@ip4.hahado.cn:32926",
    #     "https": "http://duoipesssplhp:1g3Z6uwIcoI4X@ip4.hahado.cn:32926",
    # }
    name = 'qianbaowang'
    allowed_domains = ['http://s.weibo.com', "https://weibo.com",'s.weibo.com','weibo.com']

    nowTime = datetime.datetime.now()
    clinet = pymongo.MongoClient("localhost", 27017)
    db = clinet["PCweibo"]
    infor_col = db["Information"]

    def start_requests(self):
        url = 'http://s.weibo.com/weibo/{}&scope=ori&suball=1&timescope=custom::{}'.format(keyword,'2014-01-01')
        yield Request(url=url, callback=self.parse, meta={"flag": 1},
                      )
        start_time = datetime.datetime.strptime("2014-01-01", "%Y-%m-%d")
        while start_time < datetime.datetime.strptime("2017-12-31", "%Y-%m-%d"):
                start_time_str = start_time.strftime("%Y-%m-%d")

                url = 'http://s.weibo.com/weibo/{}&scope=ori&suball=1&timescope=custom:{}:{}'.format(keyword,
                    start_time_str, start_time_str)
                yield Request(url=url, callback=self.parse, meta={"flag": 1,'start_time':start_time_str})
                start_time = start_time + datetime.timedelta(days=1)

        # text_url = 'http://s.weibo.com/weibo/%25E5%2580%259F%25E8%25B4%25B7%25E5%25AE%259D&scope=ori&suball=1&timescope=custom:2015-11-26:2015-11-26'
        # yield Request(url=text_url, callback=self.parse, meta={"flag": 1,'start_time':'2015-11-26'})


    def parse(self, response):
        flag = response.meta.get('flag')
        try:
            html_content = html.fromstring(
                re.search(r'"pid":"pl_weibo_direct".*?"html":"(.*?)"}\)</script>', response.text).group(1).replace(r"\n",
                                                                                                                   "").replace(
                    r"\t", "").replace(r'\"', '"').replace(r"\/", "/"))
        except:
            print(response.text)

        weibos = html_content.xpath("//div[@class='WB_cardwrap S_bg2 clearfix']/div")
        # print(response.text)
        if flag:
            ul = html_content.xpath("//div[@class='layer_menu_list W_scroll']/ul/li")
            print(response.meta.get('start_time'))
            if len(ul) >=49 and response.meta.get('start_time'):
                start_time = response.meta.get('start_time')
                print("这一天大于49页 {}：{}".format(keyword,start_time))
                for i in range(24):
                    xiaoshi_url ='http://s.weibo.com/weibo/{}&scope=ori&suball=1&timescope=custom:{}:{}'.format(keyword,
                                                                                                                        start_time+'-{}'.format(i), start_time+'-{}'.format(i))
                    yield Request(url=xiaoshi_url, callback=self.parse, meta={"flag": 1, })



                return
            else:
                for li in ul:
                    if not li.attrib.get('class'):
                        next_url = 'http://s.weibo.com/'+li.find('a').attrib.get('href')
                        yield Request(url=next_url, callback=self.parse)
        for weibo in weibos:
            feed_from = weibo.xpath(".//div[@class='feed_from W_textb']/a[@class='W_textb']")[-1]
            w_time = feed_from.attrib['title']

            weibo_url = 'https:' + feed_from.attrib['href']
            mid = weibo.attrib.get('mid')
            lis = weibo.xpath(".//ul[@class='feed_action_info feed_action_row4']/li")
            zhuanfa_num = lis[1].xpath("string(.)").encode('utf8').decode('unicode_escape')
            pinglun_num = lis[2].xpath("string(.)").encode('utf8').decode('unicode_escape')
            if zhuanfa_num != '转发':
                zhuanfa_num = zhuanfa_num[2:]
                zhuanfa_url = "https://weibo.com/aj/v6/mblog/info/big?ajwvr=6&id={}&filter=0".format(mid)
                yield Request(url=zhuanfa_url, callback=self.zhuanfa_parse,meta={'mid':mid},
                              )
            else:
                zhuanfa_num = 0
            if pinglun_num != '评论':
                pinglun_num = pinglun_num[2:]
                pinglun_url = "https://weibo.com/aj/v6/comment/big?ajwvr=6&id={}&filter=all&from=singleWeiBo".format(mid)
                yield Request(url=pinglun_url, callback=self.pinglun_parse,meta={'mid':mid},
                              )
            else:
                pinglun_num = 0
            weibo_content = weibo.xpath(".//div[@class='content clearfix']/div[@class='feed_content wbcon']/p[@class='comment_txt']")[0].xpath("./*|./text()")
            weibo_str = ''
            for field in weibo_content:
                if isinstance(field, lxml.etree._ElementUnicodeResult):
                    weibo_str += field
                elif field.tag == 'em':
                    weibo_str += field.xpath('string(.)')
                elif field.tag == 'img':
                    if field.attrib.get('class') == 'W_img_face':
                        weibo_str += field.attrib['alt']
                elif field.tag == 'a':
                    if field.attrib.get('class') == 'a_topic W_linkb':
                        weibo_str += field.xpath('string(.)')
                    if field.attrib.get('class') == 'W_linkb':
                        if weibo_str[-2:] == '//':
                            weibo_str = weibo_str[:-2]
                            break
                        weibo_str += field.xpath('string(.)')
                    if field.attrib.get('class') in ['W_btn_c6', 'video_link']:
                        break
            # 'http://s.weibo.com/ajax/comment/small?act=list&mid={}&smartFlag=false&smartCardComment=&isMain=true&_t=0&{}'.format(mid,)
            weibo_str = remov_emoji(weibo_str.strip()).encode('utf8').decode('unicode_escape')
            weiboitem = weiboItem()
            weiboitem['w_time'] =w_time
            weiboitem['weibo_url'] =weibo_url
            weiboitem['mid'] =mid
            weiboitem['zhuanfa_num'] =zhuanfa_num
            weiboitem['pinglun_num'] =pinglun_num
            weiboitem['keyword'] =keyword
            weiboitem['weibo_str'] =weibo_str.replace('\n',"").replace('\u200b',"")
            yield weiboitem

    def zhuanfa_parse(self, response):
        mid = response.meta['mid']
        zhuanfa_json = json.loads(response.text)
        if zhuanfa_json['code'] == '100000':
            print('请求转发成功')
            # print(zhuanfa_json['data']['html'])
            zhuanfa_content = html.fromstring(zhuanfa_json['data']['html'])
            zhuanfas = zhuanfa_content.xpath("//div[@class='list_li S_line1 clearfix']")

            for zhuanfa in zhuanfas:
                zhuanfa_mid = zhuanfa.attrib.get('mid')
                # print(zhuan_mid)
                zhuanfa_time = zhuanfa.xpath(
                    ".//div[@class='WB_func clearfix']/div[@class='WB_from S_txt2']/a[@class='S_txt1']/@title")[
                    0]
                zhuanfa_str = zhuanfa.xpath(".//div[@class='WB_text']/span[@node-type='text']")[0].xpath(
                    "./*|./text()")
                zhuanfa_str = get_str(zhuanfa_str)
                zhuanfaitem = zhuanfaItem()
                zhuanfaitem['zhuanfa_time'] = zhuanfa_time
                zhuanfaitem['mid'] = mid
                zhuanfaitem['keyword'] = keyword
                zhuanfaitem['zhuanfa_mid'] = zhuanfa_mid
                zhuanfaitem['zhuanfa_str'] = zhuanfa_str.replace(r'\n',"")
                yield zhuanfaitem


            has_next = zhuanfa_content.find_class("page next S_txt1 S_line1")
            if has_next:
                sub_next_url = has_next[0].find('span').attrib.get('action-data')
                next_url = "https://weibo.com/aj/v6/mblog/info/big?ajwvr=6&{}".format(sub_next_url)
                # print(next_url)
                yield Request(url=next_url, callback=self.zhuanfa_parse, meta={'mid': mid},
                              )

    def pinglun_parse(self, response):
        mid = response.meta['mid']
        # print(pinglun_json)
        pinglun_json = json.loads(response.text)
        if pinglun_json['code'] == '100000':
            print('请求评论成功')
            # print(pinglun_json['data']['html'])
            pinglun_content = html.fromstring(pinglun_json['data']['html'])
            pingluns = pinglun_content.xpath("//div[@class='list_li S_line1 clearfix']")
            for pinglun in pingluns:
                comment_id = pinglun.attrib.get('comment_id')
                pinglun_time = pinglun.xpath(
                    ".//div[@class='WB_func clearfix']/div[@class='WB_from S_txt2']")[0].text_content()
                pinglun_time = get_time(pinglun_time)
                # print(comment_id,pinglun_time)
                pinglun_str = pinglun.xpath(".//div[@class='WB_text']")[0].xpath("./*|./text()")
                pinglun_str = get_str(pinglun_str).replace('            ：', "")
                # print(pinglun_str)
                pinglunitem = pinglunItem()
                pinglunitem['pinglun_time'] = pinglun_time
                pinglunitem['mid'] = mid
                pinglunitem['keyword'] = keyword
                pinglunitem['comment_id'] = comment_id
                pinglunitem['pinglun_str'] = pinglun_str.replace('\n',"")
                yield pinglunitem

            # has_comment_next = pinglun_content.xpath("//a[@class='WB_cardmore S_txt1 S_line1 clearfix']")
            has_comment_next = re.findall('action-data="(id={}.*?)"'.format(mid), pinglun_json['data']['html'])
            if has_comment_next:
                next_comment_url = "https://weibo.com/aj/v6/comment/big?ajwvr=6&{}&from=singleWeiBo".format(has_comment_next[-1])
                yield Request(url=next_comment_url, callback=self.pinglun_parse, meta={'mid': mid},
                              )
