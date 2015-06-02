#!/usr/bin/python
#encoding=utf-8 

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import re
import os
import time
import multiprocessing
import redis

def incrvalue(r):
    from random import randint
    num = 2
    print 'Now Process is %d' % os.getpid()
    for i in range(num):
        r.incr('key3')
    print 'End Process is %d' % os.getpid()


if __name__ == '__main__':
    num_process = multiprocessing.cpu_count()
    r = redis.Redis(host='localhost', port=6379, db=0)
    pool = multiprocessing.Pool(processes=num_process,
                                initializer = incrvalue,
                                initargs = (r,),
                                )
    pool.close()
    pool.join()


