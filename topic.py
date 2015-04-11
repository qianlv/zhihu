#!/usr/bin/python
#encoding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import re

from bs4 import BeautifulSoup
from zhihuBase import ZhiHuPage, is_num_by_except
import question


class Topic(ZhiHuPage):
    def __init__(self, url):
        if url[-1] == '/':
            url = url[0:-1]
        url_list = url.split('/')
        if url_list[-1] != 'questions':
            if url_list[-1] in ('hot', 'top-answers'):
                url_list[-1] = 'questions'
            else:
                url_list.append('questions')
        url = '/'.join(url_list)
        super(Topic, self).__init__(url)

    def get_topic_name(self):
        if hasattr(self, "topic_name"):
            return self.topic_name

        try:
            soup = self.soup.find("div", attrs={"class": "topic-name", "id": "zh-topic-title"})
            self.topic_name = soup.h1.get_text()
        except AttributeError, e:
            print e
            self.topic_name = None
        return self.topic_name

    def get_topic_page_num(self):
        if hasattr(self, "topic_page_num"):
            return self.topic_page_num

        try:
            soup = self.soup.find("div", 
                    attrs={"class": "zm-invite-pager"})
            spans = soup.strings
            self.topic_page_num = max([int(num) for num in spans if is_num_by_except(num)])
        except AttributeError, e:
            print e
            self.topic_page_num = 1
        return self.topic_page_num

    def get_topic_follower_num(self):
        if hasattr(self, "topic_follower_num"):
            return self.topic_follower_num

        try:
            num = self.soup.find("div", attrs={"class": "zm-topic-side-followers-info"}).strong.get_text()

            if is_num_by_except(num):
                self.topic_follower_num = int(num)
            else:
                self.topic_follower_num = 0
        except AttributeError, e:
            print e
            self.topic_follower_num = 0

        return self.topic_follower_num 


    def get_questions(self):
        for page in xrange(1, self.get_topic_page_num() + 1):
            url = self.url + "?page=" + str(page)
            page_soup = self.get_page(url) 
            question_links = page_soup.find_all("a", attrs={"target": "_blank", "class": "question_link"})
            for link in question_links:
                url = "http://www.zhihu.com" + link.get('href')
                #print url
                yield question.Question(url)


if __name__ == '__main__':
    my_topic = Topic("http://www.zhihu.com/topic/19603857/hot/")
    print my_topic.get_topic_name()
    print my_topic.get_topic_page_num()
    print my_topic.get_topic_follower_num()
    my_question = my_topic.get_questions().next()
    print my_question.get_title()
    print my_question.get_detail()
    print my_question.get_answer_num()
    print my_question.get_follower_num()
    for topic in my_question.get_topics():
        print topic.get_topic_name()
    
