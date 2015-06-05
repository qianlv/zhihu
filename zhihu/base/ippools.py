#encoding=utf-8

import os

from zhihu.base.database import link_db
from zhihu.setting import PROXIES_FAIL, PROXIES_MIN_USE_COUNT
import random

def get_proxies(fail,  ip_type = 0):
    db = link_db()
    cursor = db.cursor()
    sql = "select * from `ippools`"
    cursor.execute(sql)
    resutls = cursor.fetchall()
    res = []
    for item in resutls:
        if ip_type != item[3] or item[2] > fail:
            continue
        ip_address = ':'.join(item[0:2])
        res.append({'http': ip_address})
    db.close()
    return res

def update_fail_ip(ip_address, ip_type = 0):
    db = link_db()
    cursor = db.cursor()
    ip, port = ip_address.split(':')
    sql = "update `ippools` set `fail` = `fail` + 1  \
          where `ip` = '%s' and `port` = '%s' and `type` = %d" \
          % (ip, port, ip_type)
    cursor.execute(sql)
    db.commit()
    db.close()  

def delete_fail_ip(fail, ip_type = 0):
    db = link_db()
    cursor = db.cursor()
    sql = "delete from `ippools` where `fail` = %d" % fail
    cursor.execute(sql)
    db.commit()
    db.close()

def delete_ip(ip_address, ip_type = 0):
    db = link_db()
    cursor = db.cursor()
    ip, port = ip_address.split(':')
    sql = "delete from `ippools` where `ip` = '%s'" % ip
    cursor.execute(sql)
    db.commit()
    db.close()

cur_proxies =  None
cur_proxies_fail = PROXIES_FAIL
def get_cur_proxies():
    global cur_proxies
    if cur_proxies is None:
        cur_proxies = get_random_proxies()
    return cur_proxies

def get_random_proxies():
    #return {}
    global cur_proxies_fail
    proxies = get_proxies(cur_proxies_fail)
    while len(proxies) == 0:
        proxies = get_proxies(cur_proxies_fail)
        cur_proxies_fail += 1
    return random.choice(proxies)

def change_cur_proxies():
    global cur_proxies
    if cur_proxies:
        cur_proxies = get_random_proxies()

def fail_cur_proxies():
    if cur_proxies:
        update_fail_ip(cur_proxies['http'])
def set_cur_proxies(ip_address):
    global cur_proxies
    cur_proxies = ip_address

