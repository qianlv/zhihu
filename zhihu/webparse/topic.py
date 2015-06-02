#!/usr/bin/python
#encoding=utf-8 

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import re
import logging

from bs4 import BeautifulSoup

from zhihu.base.network import ZhiHuPage, login
from zhihu.base import is_num_by_except
from zhihu.setting import ZHI_HU_URL
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
            return self.topic_name.encode("utf-8")

        try:
            soup = self.soup.find("div", 
                   attrs={"class": "topic-name", "id": "zh-topic-title"})
            self.topic_name = soup.h1.get_text()
        except (AttributeError, ValueError), e:
            logging.warn("Topic get_topic_name error|%s|%s", self.url, str(e))
            return None 

        return self.topic_name.encode("utf-8")

    def get_topic_page_num(self):
        if hasattr(self, "topic_page_num"):
            return self.topic_page_num

        try:
            soup = self.soup.find("div", 
                    attrs={"class": "zm-invite-pager"})
            if soup: 
                spans = soup.strings
                self.topic_page_num = max([int(num) for num in spans 
                                           if is_num_by_except(num)])
            else:
                self.topic_page_num = 1
        except (AttributeError, ValueError), e:
            logging.warn("Topic get_topic_page_num error|%s|%s", 
                            self.url, str(e))
            return None 
        return self.topic_page_num

    def get_topic_follower_num(self):
        if hasattr(self, "topic_follower_num"):
            return self.topic_follower_num

        try:
            num = self.soup.find("div", 
                  class_="zm-topic-side-followers-info").strong.get_text()

            if is_num_by_except(num):
                self.topic_follower_num = int(num)
            else:
                self.topic_follower_num = 0
        except (AttributeError, ValueError), e:
            logging.warn("Topic get_topic_follower_num error|%s|%s", self.url, str(e))
            return None 

        return self.topic_follower_num 


    def get_questions(self):
        for page in xrange(1, self.get_topic_page_num() + 1):
            url = self.url + "?page=" + str(page)
            try:
                page_soup = BeautifulSoup(self.get_page(url).content)
                question_links = page_soup.find_all("a", 
                        attrs={"target": "_blank", "class": "question_link"})
            except AttributeError, e:
                logging.warn("Topic get_questions error|%s|%s", self.url, str(e))
                return 

            for link in question_links:
                url = ZHI_HU_URL + link.get('href')
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
            try:
                soup = self.soup.find("h1", class_="zm-editable-content")
                self.node_name = soup.string
            except AttributeError, e:
                logging.warn("TopicNode get_node_name error|%s|%s", 
                            self.url if self.url else '', str(e))

                return None

        return self.node_name.encode("utf-8")
    
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
        try:
            xsrf = self.soup.find("input", 
                    attrs={"name":"_xsrf", "type":"hidden"}).get("value")
        except AttributeError, e:
            logging.warn("TopicNode get_children_nodes can't find xsrf value \
                          |%s|%s", self.url if self.url else '', str(e))
            # 返回出错的url用于重新处理
            yield self.url
            return

        data = { "_xsrf": xsrf }

        post_url = self.url
        while True:
            data_token, data_parent = None, None

            try:
                response = self.get_post(post_url, data)
                msg = response.json()["msg"]
                topic_list = msg[1]
            except (AttributeError, KeyError), e:
                logging.warn("TopicNode get_children_nodes post_url and self_url \
                                |%s|%s|%s", post_url, self.url, str(e))
                # 返回出错的url用于重新处理
                yield post_url
                return

            for item in topic_list:
                if item[0][0] == "topic":
                    url = "http://www.zhihu.com/topic/%s/organize/entire" % item[0][2]
                    yield TopicNode(url, name = item[0][1], topic_id = int(item[0][2]))
                elif item[0][0] == "load":
                    data_token = item[0][2]
                    data_parent = item[0][3]
            if data_token == None and data_parent == None:
                return
            post_url = "?child=%s&parent=%s" % (data_token, data_parent)
            post_url = self.url + post_url
