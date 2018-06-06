# -*- coding: utf-8 -*-
#!/usr/bin/python3
import redis
import requests
import regex as re
from lxml import html
import lxml
import chardet
import time
import datetime
agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0'
headers = {
'Accept':'*/*',
    'User-Agent': agent,
"Content-Type":"text/html"
}
redis_pool = redis.ConnectionPool(host="127.0.0.1", port="6379")
r = redis.Redis(connection_pool=redis_pool)
cookie = r.srandmember("d_cookie").decode()
cookies = eval(cookie)

text = requests.get("http://s.weibo.com/weibo/e%25E7%25A7%259F%25E5%25AE%259D&typeall=1&suball=1&timescope=custom:2016-01-12-5:2016-01-12-5&Refer=g#1514539229240",headers=headers,cookies=cookies).content.decode('utf8')
print(requests.get("http://s.weibo.com/weibo/e%25E7%25A7%259F%25E5%25AE%259D&typeall=1&suball=1&timescope=custom:2016-01-12-5:2016-01-12-5&Refer=g#1514539229240",headers=headers,cookies=cookies).text)



# print(text)
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
        time = re.findall("\d{2}月\d{2}日 \d{2}:\d{2}", w_time)
        if len(time):
            pubtime = datetime.datetime.strptime("2017 " + time[0], "%Y %m月%d日 %H:%M").strftime("%Y-%m-%d %H:%M")

    elif len(re.findall("\d{4}-\d{2}-\d{2} \d{2}:\d{2}", w_time)):
        pubtime = re.findall("\d{4}-\d{2}-\d{2} \d{2}:\d{2}", w_time)[0]

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

if "解除帐号异常" in text:
    print("帐号异常")
    print(cookie)
    r.srem("cookie", cookie)
else:
    print('没有异常')

    html_content = html.fromstring(re.search(r'"pid":"pl_weibo_direct".*?"html":"(.*?)"}\)</script>', text).group(1).replace(r"\n","").replace(r"\t","").replace(r'\"','"').replace(r"\/","/"))

    weibos = html_content.xpath("//div[@class='WB_cardwrap S_bg2 clearfix']/div")

    for weibo in weibos:
        feed_from = weibo.xpath(".//div[@class='feed_from W_textb']/a[@class='W_textb']")[0]
        w_time = feed_from.attrib['title']
        weibo_url = 'https:' + feed_from.attrib['href']
        mid = weibo.attrib.get('mid')
        lis = weibo.xpath(".//ul[@class='feed_action_info feed_action_row4']/li")
        zhuanfa_num = lis[1].xpath("string(.)").encode('utf8').decode('unicode_escape')
        pinglun_num = lis[2].xpath("string(.)").encode('utf8').decode('unicode_escape')
        if zhuanfa_num !='转发':
            zhuanfa_num = zhuanfa_num[2:]
            zhuanfa_json = requests.get("https://weibo.com/aj/v6/mblog/info/big?ajwvr=6&id={}&filter=0&__rnd={}".format(mid,int(time.time()*1000)),headers=headers,cookies=cookies).json()
            if zhuanfa_json['code'] == '100000':
                print('请求转发成功')
                # print(zhuanfa_json['data']['html'])
                zhuanfa_content = html.fromstring(zhuanfa_json['data']['html'])
                zhuanfas = zhuanfa_content.xpath("//div[@class='list_li S_line1 clearfix']")

                for zhuanfa in zhuanfas:
                    zhuan_mid = zhuanfa.attrib.get('mid')
                    print(zhuan_mid)
                    zhuanfa_time = zhuanfa.xpath(
                        ".//div[@class='WB_func clearfix']/div[@class='WB_from S_txt2']/a[@class='S_txt1']/@title")[0]
                    zhuanfa_str = zhuanfa.xpath(".//div[@class='WB_text']/span[@node-type='text']")[0].xpath("./*|./text()")
                    zhuanfa_str = get_str(zhuanfa_str)
                    print(zhuanfa_str)
                has_next = zhuanfa_content.find_class("page next S_txt1 S_line1")

                if has_next:
                    sub_next_url = has_next[0].find('span').attrib.get('action-data')
                    next_url = "https://weibo.com/aj/v6/mblog/info/big?ajwvr=6&{}&__rnd={}".format(sub_next_url,int(time.time()*1000))
                    # print(next_url)
                    # print(requests.get(next_url,headers=headers,cookies=cookies).json())
        else:
            zhuanfa_num = 0
        if pinglun_num !='评论':
            pinglun_num = pinglun_num[2:]
            pinglun_json = requests.get("https://weibo.com/aj/v6/comment/big?ajwvr=6&id={}&filter=all&from=singleWeiBo&__rnd={}".format(mid,int(time.time()*1000)),headers=headers,cookies=cookies).json()
            # print(pinglun_json)
            if pinglun_json['code'] == '100000':
                print('请求评论成功')

                print(pinglun_json['data']['html'])
                pinglun_content = html.fromstring(pinglun_json['data']['html'])
                pingluns = pinglun_content.xpath("//div[@class='list_li S_line1 clearfix']")
                for pinglun in pingluns:
                    comment_id = pinglun.attrib.get('comment_id')
                    zhuanfa_time = pinglun.xpath(
                        ".//div[@class='WB_func clearfix']/div[@class='WB_from S_txt2']")[0].text_content()
                    zhuanfa_time = get_time(zhuanfa_time)
                    # print(comment_id,zhuanfa_time)
                    pinglun_str = pinglun.xpath(".//div[@class='WB_text']")[0].xpath("./*|./text()")
                    pinglun_str = get_str(pinglun_str).replace('            ：',"")
                    print(pinglun_str)
                # has_comment_next = pinglun_content.xpath("//a[@class='WB_cardmore S_txt1 S_line1 clearfix']")
                has_comment_next = re.findall('action-data="(id={}.*?)"'.format(mid),pinglun_json['data']['html'])
                print(has_comment_next)
                if has_comment_next:
                    next_comment_url = "https://weibo.com/aj/v6/comment/big?ajwvr=6&{}&from=singleWeiBo&__rnd={}".format(has_comment_next[-1],int(time.time()*1000))
                    print(next_comment_url)

        else:

            pinglun_num =0
        weibo_content = weibo.xpath(".//div[@class='content clearfix']/div[@class='feed_content wbcon']/p[@class='comment_txt']")[0].xpath("./*|./text()")
        weibo_str = ''
        for field in weibo_content:
            if isinstance(field, lxml.etree._ElementUnicodeResult):
                weibo_str +=field
            elif field.tag == 'em':
                weibo_str +=field.xpath('string(.)')
            elif field.tag == 'img':
                if field.attrib.get('class') =='W_img_face':
                    weibo_str += field.attrib['alt']
            elif field.tag == 'a':
                if  field.attrib.get('class') =='a_topic W_linkb':
                    weibo_str += field.xpath('string(.)')
                if field.attrib.get('class') == 'W_linkb':
                    if weibo_str[-2:] == '//':
                        weibo_str= weibo_str[:-2]
                        break
                    weibo_str += field.xpath('string(.)')
                if field.attrib.get('class') in ['W_btn_c6','video_link']:
                    break
        # 'http://s.weibo.com/ajax/comment/small?act=list&mid={}&smartFlag=false&smartCardComment=&isMain=true&_t=0&{}'.format(mid,)


        weibo_str = remov_emoji(weibo_str.strip())

        a = weibo_str.encode('utf-8').decode('unicode_escape')
        print(a)

        break














