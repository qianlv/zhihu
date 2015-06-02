#encoding=utf-8
import sys
import os
import re
print os.path.abspath('../')
sys.path.append(os.path.abspath('../'))
import requests
from bs4 import BeautifulSoup
from zhihuBase import ZhiHuPage, login, get_number_from_string, link_db

import logging
logging_format = "%(asctime)s|%(filename)s|%(funcName)s:%(lineno)d|%(levelname)s: %(message)s"
logging.basicConfig(filename = os.path.join(os.getcwd(), "../log.txt"), 
                    level = logging.INFO,
                    format = logging_format
                    )


def check_ping(ip):
    import subprocess 
    com = 'ping -c 1 %s -W 1' %ip
    print com
    ret = subprocess.call(com, shell = True, 
                    stdout=open('/dev/null', 'w'),
                    stderr=subprocess.STDOUT)
    if ret != 0:
        return False
    return True

def crawl_cn_ip():
    url = 'http://cn-proxy.com'
    ips = []
    try:
        r = requests.get(url, timeout=5)
    except Exception, e:
        print str(e)
        return []
    soup = BeautifulSoup(r.content)
    table = soup.find('table', id='tablekit-table-1')
    trs = soup.find_all('tr')
    for tr in trs[2:]:
        tds = tr.find_all('td')
        try:
            if not check_ping(tds[0].string.strip()):
                continue
            ips.append((tds[0].string.strip(), tds[1].string.strip()))
        except IndexError:
            pass
    return ips

def crawl_kuai_ip():
    pre = "http://www.kuaidaili.com/free/"
    urls =['inha/', 'intr/', 'outha/', 'outtr/']
    urls = [pre + u for u in urls]
    ips = []
    for url in urls[0:2]:
        for i in range(1, 40):
            print url, i
            try:
                r = requests.get(url + str(i), timeout=5)
            except Exception, e:
                print str(e)
                continue
            soup = BeautifulSoup(r.content)
            table = soup.find('table', class_ = "table table-bordered table-striped")
            trs = soup.find_all('tr')
            for tr in trs[1:]:
                tds = tr.find_all('td')
                try:
                    if not check_ping(tds[0].string.strip()):
                        continue
                    ips.append((tds[0].string.strip(), tds[1].string.strip()))
                except IndexError:
                    pass
    return ips 

def crawl_proxy_ip():
    url = "http://www.proxy.com.ru/"
    ips = []
    for i in range(1, 11):
        try:
            r = requests.get(url + "list_" + str(i) + ".html", timeout = 5)
        except Exception, e:
            print str(e)
            continue
        print r.url
        soup = BeautifulSoup(r.content)
        table = soup.find_all('table')[7]
        if table is None:
            break
        trs = table.find_all('tr')
        for tr in trs[1:]:
            tds = tr.find_all('td')
            try:
                if not check_ping(tds[1].string.strip()):
                    continue
                ips.append((tds[1].string.strip(), tds[2].string.strip()))
            except IndexError:
                pass
    return ips

# 好代理
def crawl_haodailiip_ip():
    urls = ["http://www.haodailiip.com/guonei/",
           "http://www.haodailiip.com/guoji/"]
    ips = []
    for url in urls:
        for i in range(1, 11):
            import time
            time.sleep(1)
            try:
                r = requests.get(url + str(i), timeout = 5)
            except Exception, e:
                print str(e)
                continue
            print r.url
            soup = BeautifulSoup(r.content)
            table = soup.find("table", class_="proxy_table")
            trs = table.find_all('tr')
            for tr in trs[1:]:
                tds = tr.find_all('td')
                try:
                    if not check_ping(tds[0].string.strip()):
                        continue
                    ips.append((tds[0].string.strip(), tds[1].string.strip()))
                except IndexError:
                    pass
    return ips

def crawl_ip_daily_ip():
    def get_ip(url):
        try:
            r = requests.get(url, timeout=5)
        except Exception, e:
            print str(e)
            return []
        ma = re.compile(ur'(\d+\.\d+\.\d+\.\d+):(\d+)') 
        res = ma.findall(r.content)
        return [x for x in res if check_ping(x[0])]
        
    ips = []
    for i in range(3,6):
        url = "http://www.ip-daili.com/xw/?id=" + str(i)
        try:
            r = requests.get(url, timeout=5)
        except Exception, e:
            print str(e)
            continue
        soup = BeautifulSoup(r.content)
        ul = soup.find('div', class_="lmy-right-xw").ul
        lis = ul.find_all('li')
        for li in lis[0:5]:
            href = li.find_all('a')[1].get('href')
            ips.extend(get_ip(href))
    return ips

class CheckIp(ZhiHuPage):
    def __init__(self):
        self.urls = ['http://www.zhihu.com/people/momobye', 
                     'http://www.zhihu.com/question/28679480/answer/41714552',
                     'http://www.zhihu.com/question/21255529',
                     'http://www.zhihu.com/topic/19555542',
                     'http://www.zhihu.com/topic/19786485',
                     'http://www.zhihu.com/people/wangwenjie1314',
                     'http://zhuanlan.zhihu.com/queen',
                     'http://www.zhihu.com/question/30375859',
                     'http://www.zhihu.com/topic/19551052'
                     ]
        self.db = link_db()

    def check_content(self, content):
        soup = BeautifulSoup(content)
        ip_err = soup.find('div', attrs = {'class': 'page_form_wrap c r5px'})
        if ip_err is None:
            return False
        return True

    def check(self, ip, ip_type = 0):
        cursor = self.db.cursor()
        sql = "select * from `ippools` where `ip` = '%s' \
                and `port` = '%s' and `type` = %d" % (ip[0], ip[1], ip_type)
        cursor.execute(sql)
        res = cursor.fetchone()
        if res:
            return False
         
        proxies = {'http': os.path.pathsep.join([ip[0], ip[1]]) }
        from random import choice
        url = self.urls[choice(range(0, len(self.urls)))]
        res = self.get_page(url, proxies_flag = False, proxies = proxies)
        if res is None: 
            return False
        elif self.check_content(res.content):
            return False
        return True

    def save_db(self, ip, ip_type = 0):
        if not self.check(ip, ip_type):
            return

        cursor = self.db.cursor()
        insert_sql = "insert into `ippools` (`ip`, `port`, `type`) \
                        values ('%s', '%s', %d)" % (ip[0], ip[1], ip_type)
        cursor.execute(insert_sql)
        self.db.commit()

    def __call__(self, ips):
        ips = set(ips)
        map(self.save_db, ips)

#print check_ping('123.163.92.238')

my_check = CheckIp()
#ips = crawl_kuai_ip()
#my_check(ips)
#ips = crawl_haodailiip_ip()
#print len(ips)
#my_check(ips)
#ips = crawl_proxy_ip()
#print len(ips)
#my_check(ips)
#ips = crawl_cn_ip()
#print len(ips)
#my_check(ips)
ips = crawl_ip_daily_ip()
my_check(ips)


