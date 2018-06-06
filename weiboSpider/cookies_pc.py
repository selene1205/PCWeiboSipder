# coding:utf-8

import base64
from urllib.parse import quote, unquote
import rsa
import binascii
import requests
import json
import re
import logging
import redis
import random
from rk import *
from PIL import Image
from accounts import MyAccounts


logger = logging.getLogger(__name__)

agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0'
headers = {
'Accept':'*/*',
'Referer':'https://weibo.com/',
    'User-Agent': agent
}
def getif():
    requests.get("http://7xrnwq.com1.z0.glb.clouddn.com/proxy_list.txt?v=1000")

login_url = 'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.19)'

def get_cookie(account, password):
    ips = None
    ip = None
    en_user = base64.b64encode(bytes(quote(account), encoding="utf-8"))
    # first_url = '''https://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=
    #     sinaSSOController.preloginCallBack&su=&rsakt=mod&client=ssologin.js(v1.4.19)&_=%s''' % (int(time.time() * 1000))
    prelogin_url = '''https://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=
    sinaSSOController.preloginCallBack&su=%s&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.19)&_=%s''' % (en_user,int(time.time()*1000))
    session = requests.session()
    # t = session.get(first_url,headers=headers)

    r = session.get(prelogin_url,headers=headers)


    pre_data = re.search(r'\{.+\}', r.content.decode()).group()
    pre_data = json.loads(pre_data)
    servertime = pre_data['servertime']
    nonce = pre_data['nonce']
    rsakv = pre_data['rsakv']
    pubkey = pre_data['pubkey']
    # print(pre_data)
    pubkey = int(pubkey, 16)
    e = int('10001', 16)
    pub = rsa.PublicKey(pubkey, e)

    en_pwd = rsa.encrypt(bytes(str(servertime) + '\t' + str(nonce) + '\n' + password,encoding="utf-8"), pub)
    en_pwd = binascii.b2a_hex(en_pwd)


    formdata = {
        'entry': 'weibo',
        'gateway': '1',
        'from': '',
        'savestate': '7',
        #'qrcode_flag': 'false',
        'useticket': '1',
        'ssosimplelogin': '1',
        'pagerefer': '',
        'vsnf': '1',
        #'vsnval': '',
        'su': en_user,
        'service': 'miniblog',
        'servertime': servertime,
        'nonce': nonce,
        'pwencode': 'rsa2',
        'rsakv': rsakv,
        'sp': en_pwd,
        'sr': '1920*1080',
        'encoding': 'UTF-8',
        'cdult': '2',
        'domain': 'weibo.com',
        'prelt': '34',
        'returntype': 'TEXT'
    }

    # r1 = session.post(login_url, data=formdata,headers=headers)
    # print(r1.text)
    # url2 = re.search('location.replace\(\"(.*?)\"\)', r1.content.decode("gbk")).group(1)
    #
    # retcode = str(re.search('retcode=(\d+)', unquote(url2)).group(1))

    flag = 1
    login_url_time = login_url +'&_={}'.format(int(time.time()*1000))

    retcode =1
    while retcode !='0' and flag<4:
        print(retcode)
        get_cha(pre_data['pcid'], session)
        print("自动打码第",flag,"次")
        door = dama()
        formdata['door'] = door

        r1 = session.post(login_url_time, data=formdata, headers=headers)



        dict_result = eval(r1.text)

        retcode = dict_result['retcode']
        flag+=1

    print("the retcode is",retcode)


    if retcode =='0':
        logger.warning('Succeed to get cookie of account(%s).' % account)
        urls = dict_result['crossDomainUrlList']


        return json.dumps(r1.cookies.get_dict())
    else:
        reason = dict_result['reason']
        #print(reason)
        logger.warning('Failed to get cookie of account(%s).Reason:%s.' % (account, reason))
        return None
def get_cha(pcid,session):
    cha_url = "http://login.sina.com.cn/cgi/pin.php?r="
    cha_url = cha_url + str(int(random.random() * 100000000)) + "&s=0&p="
    cha_url = cha_url + pcid
    cha_page = session.get(cha_url, headers=headers)
    with open("cha.jpg", 'wb') as f:
        f.write(cha_page.content)
        f.close()

def dama():
    # 软件ＩＤ，开发者分成必要参数。登录开发者后台【我的软件】获得！
    appid = 1
    # 软件密钥，开发者分成必要参数。登录开发者后台【我的软件】获得！
    appkey = '22cc5376925e9387a23cf797cb9ba745'
    # 初始化
    yundama = YDMHttp('z369217411', 'zxc5667456y', appid, appkey)
    # 登陆云打码
    uid = yundama.login();
    # 查询余额
    balance = yundama.balance();
    print('balance: %s' % balance)
    cid, result = yundama.decode('cha.jpg', 1005, 30);
    print('cid: %s, result: %s' % (cid, result))
    return result


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
# r.delete("cookie")
print(cookies)
r.sadd("cookie", *cookies)

logger.warning('Finished to get cookies. Num:%d.' % len(cookies))
    

    
    
    
    

    