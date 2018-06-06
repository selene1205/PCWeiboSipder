# coding:utf-8

import requests
import json
import logging
from multiprocessing.dummy import Pool
import redis
import time
import random
from accounts import MyAccounts

headers = {
    'Referer': 'https://passport.weibo.cn/signin/login?entry=mweibo&r=http%3A%2F%2Fweibo.cn%2F&backTitle=%CE%A2%B2%A9&vt=',
    'Origin': 'https://passport.weibo.cn',
    'Host': 'passport.weibo.cn'
}

logger = logging.getLogger(__name__)

login_url = 'https://passport.weibo.cn/sso/login'


def get_cookie(account, password, times=0):
    formdata = {
        'username': account,
        'password': password,
        'savestate': '1',
        'r': 'http://weibo.cn/',
        'ec': '0',
        'pagerefer': '',
        'entry': 'mweibo',
        'wentry': '',
        'loginfrom': '',
        'client_id': '',
        'code': '',
        'qq': '',
        'mainpageflag': '1',
        'hff': '',
        'hfp': '',
    }

    session = requests.Session()
    r = session.post(login_url, data=formdata, headers=headers)
    if r.status_code == 200:
        if not r.cookies.get_dict():
            print("account %s,msg:%s" % (account, r.content))
            return None
        # logger.warning('Succeed to get cookie of account(%s).' % account)
        logger.warning(r.cookies.get_dict())
        return json.dumps(r.cookies.get_dict())
    elif r.status_code == 429 and times < 4:
        time.sleep(random.randint(1, 3))
        times += 1
        get_cookie(account, password, times=times)
    else:
        logger.warning('Failed to get cookie of account(%s).Status_code:%d.' % (account, r.status_code))
        return None


def get_Cookies(Accounts):
    cookies = []
    for account in Accounts:
        cookie = get_cookie(account['no'], account['psw'])
        if cookie:
            cookies.append(cookie)
    return cookies


cookies = get_Cookies(MyAccounts)
redis_pool = redis.ConnectionPool(host="127.0.0.1", port="6379")
r = redis.Redis(connection_pool=redis_pool)
r.delete("phone_cookie")
r.sadd("phone_cookie", *cookies)

logger.warning('Finished to get cookies. Num:%d.' % len(cookies))
