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
        url = self.deal_url(url)
        super(Topic, self).__init__(url)

    def deal_url(self, url):
        if url[-1] == '/':
            url = url[0:-1]
        url_list = url.split('/')
        if url_list[-1] != 'questions':
            if url_list[-1] in ('hot', 'top-answers'):
                url_list[-1] = 'questions'
            else:
                url_list.append('questions')
        url = '/'.join(url_list)
        return url

    def get_topic_url(self):
        return self.url

    def get_topic_id(self):
        return self.get_id()

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
            question_links = page_soup.find_all("a", 
                    attrs={"target": "_blank", "class": "question_link"})
            for link in question_links:
                url = "http://www.zhihu.com" + link.get('href')
                #print url
                yield question.Question(url) 

    def get_child_topics(self):
        cur_topic_node = TopicNode(self.url + "/organize/entire",
                                   name = self.get_topic_name(),
                                   topic_id = self.get_topic_id())

        for child in cur_topic_node:
            yield Topic(child.get_topic_url())
                                   

class TopicNode(ZhiHuPage):
    def __init__(self, url, name = None, topic_id = None):
        self.node_name = name
        self.topic_id = topic_id
        super(TopicNode, self).__init__(url)

    def get_node_name(self):
        if self.node_name == None:
            soup = self.soup.find("h1")
            self.node_name = soup.string
        return self.node_name
    
    def get_node_url(self):
        return self.url

    def get_topic_id(self):
        if self.topic_id == None:
            self.topic_id = self.get_id()
        return self.topic_id

    def get_topic_url(self):
        url = self.url.split("/")
        return "/".join(url[0:-2])

    def get_topic(self):
        return Topic(self.get_topic_url())

    def get_parent_node(self):
        pass

    def get_children_nodes(self):
        xsrf = self.soup.find("input", 
            attrs={"name":"_xsrf", "type":"hidden"}).get("value")
        data = { "_xsrf": xsrf }

        post_url = self.url
        while True:
            data_token, data_parent = None, None
            response = self.get_post(post_url, data)
            if response == None:
                return 

            msg = response.json()["msg"]
            topic_list = msg[1]
            for item in topic_list:
                if item[0][0] == "topic":
                    url = "http://www.zhihu.com/topic/%s/organize/entire" % item[0][2]
                    yield TopicNode(url, name = item[0][1], topic_id = item[0][2])
                elif item[0][0] == "load":
                    data_token = item[0][2]
                    data_parent = item[0][3]
            if data_token == None and data_parent == None:
                return
            post_url = "?child=%s&parent=%s" % (data_token, data_parent)
            post_url = self.url + post_url

if __name__ == '__main__':
    #my_topic = Topic("http://www.zhihu.com/topic/19570098")
    #print my_topic.get_topic_name()
    #print my_topic.get_topic_page_num()
    #print my_topic.get_topic_follower_num()
    #my_question = my_topic.get_questions().next()
    #print my_question.get_title()
    #print my_question.get_detail()
    #print my_question.get_answer_num()
    #print my_question.get_follower_num()
    #for topic in my_question.get_topics():
    #    print topic.get_topic_name()
    #
    my_topic_node = TopicNode("http://www.zhihu.com/topic/19587463/organize/entire")
    print "节点名字:", my_topic_node.get_node_name()
    print "节点URL:", my_topic_node.get_node_url()
    print "话题ID:", my_topic_node.get_topic_id()
    print "话题URL:", my_topic_node.get_topic_url()
    print "话题问题页数:", my_topic_node.get_topic().get_topic_page_num()
    print "子节点:"
    childs = my_topic_node.get_children_nodes()
    for child in childs:
        print child.get_node_name()
