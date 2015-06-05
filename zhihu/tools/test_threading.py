#encoding=utf-8
import threading
import time

class timer(threading.Thread):
    def __init__(self, num, interval):
        threading.Thread.__init__(self)
        self.thread_num = num
        self.num = 0
        self.interval = interval
        self.thread_stop = False
    def run(self):
        while not self.thread_stop:
            print 'Thread Object(%d), Time:%s, num:%d, name:%s\n' % \
                (self.thread_num, time.ctime(), self.num, self.getName())
            self.num += 1
            time.sleep(self.interval)
    def stop(self):
        self.thread_stop = True

import thread
mylock = thread.allocate_lock()
num = 0
def add_num(name):
    global num
    while True:
        mylock.acquire()
        print 'Thread %s locked! num = %d' % (name, num)
        if num >= 5:
            print 'Thread %s released! num = %d' % (name, num)
            mylock.release()
            thread.exit_thread()
        num += 1
        print 'Thread %s released! num = %d' % (name, num)
        mylock.release()

def test_add():
    try:
        thread.start_new_thread(add_num, ('A',))
        thread.start_new_thread(add_num, ('B',))
    except:
        print 'error'

def test():
    thread1 = timer(1,1)
    thread2 = timer(2,2)
    thread1.start()
    thread2.start()
    time.sleep(10)
    thread1.stop()
    thread2.stop()

if __name__ == '__main__':
    test()
    test_add()
            
