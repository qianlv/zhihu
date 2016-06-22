#!/usr/bin/python
# encoding=utf-8

from bs4 import BeautifulSoup

from zhihu.network import default_net_request
from zhihu.network import get_url_id
from zhihu.utility import is_num_by_except
from zhihu.setting import ZHI_HU_URL
import zhihu.question 


class Topic(object):
    def __init__(self, url):
        response = default_net_request.get_request(url)
        self.soup = BeautifulSoup(response.content, "lxml")
        self.url = url

    def __nonzero__(self):
        if self.url is None or self.soup is None:
            return False
        return True

    def get_topic_url(self):
        """ 话题URL
            rtype: str
        """
        return self.url

    def get_topic_id(self):
        """ 话题ID
            rtype: str
        """
        return get_url_id(self.url)

    def get_topic_name(self):
        """ 话题名
            rtype: str
        """
        soup = self.soup.find(
            "div", attrs={"class": "topic-name", "id": "zh-topic-title"})
        topic_name = soup.h1.get_text()

        return topic_name.encode("utf-8")

    def get_topic_page_num(self):
        soup = self.soup.find("div", attrs={"class": "zm-invite-pager"})
        if soup:
            spans = soup.strings
            topic_page_num = max([int(num) for num in spans
                                  if is_num_by_except(num)])
        else:
            topic_page_num = 1

        return topic_page_num

    def get_topic_follower_num(self):
        """ 话题关注数量
            rtype: int
        """
        num = self.soup.find(
            "div", class_="zm-topic-side-followers-info").strong.get_text()

        if is_num_by_except(num):
            topic_follower_num = int(num)
        else:
            topic_follower_num = 0

        return topic_follower_num

    def get_questions(self):
        """ 话题下的问题
            rtype: Question.Iterable
        """
        for page in xrange(1, self.get_topic_page_num() + 1):
            url = "{0}?page={1}".format(self.url, str(page))

            response = default_net_request.get_request(url)
            if not response:
                page_soup = BeautifulSoup(response.content, "lxml")
                question_links = page_soup.find_all(
                    "a", attrs={"target": "_blank", "class": "question_link"})

                for link in question_links:
                    url = ZHI_HU_URL + link.get('href')
                    yield zhihu.question.Question(url)
            return

    def get_child_topics(self):
        """ 话题的子话题
            rtype: TopicNode.Iterable
        """
        url = "{0}/organize/entire".format(self.url)
        cur_topic_node = TopicNode(url)

        for child in cur_topic_node:
            yield Topic(child.get_topic_url())

    def get_child_ids(self):
        """ 话题的子话题ID
            rtype: int iterable
        """
        url = "{0}/organize/entire".format(self.url)
        cur_topic_node = TopicNode(url)
        for child in cur_topic_node:
            yield child.get_topic_id()


class TopicNode(object):
    """ 话题节点
    """
    def __init__(self, url):
        response = default_net_request.get_request(url)
        self.soup = BeautifulSoup(response.content, "lxml")
        self.url = url

    def __nonzero__(self):
        if self.url is None or self.soup is None:
            return False
        return True

    def get_node_name(self):
        """ 话题节点名
            rtype: str
        """
        soup = self.soup.find("h1", class_="zm-editable-content")
        node_name = soup.string
        return node_name.encode("utf-8")

    def get_node_url(self):
        """ 话题节点URL
            rtype: str
        """
        return self.url

    def get_topic_id(self):
        """ 话题ID
            rtype: str
        """
        return get_url_id(self.url)

    def get_topic_url(self):
        """ 话题URL
            rtype: str
        """
        url = self.url.split("/")
        return "/".join(url[0:-2])

    def get_topic(self):
        """ 节点话题
            rtype: Topic
        """
        return Topic(self.get_topic_url())

    def get_parent_node(self):
        pass

    def get_children_nodes(self):
        """ 话题子节点
            rtype: TopicNode.Iterable
        """
        xsrf = self.soup.find(
            "input", attrs={"name": "_xsrf", "type": "hidden"}).get("value")

        data = {"_xsrf": xsrf}

        post_url = self.url
        while True:
            data_token, data_parent = None, None

            response = default_net_request.post_request(post_url, data=data)
            msg = response.json()["msg"]
            topic_list = msg[1]

            for item in topic_list:
                if item[0][0] == "topic":
                    url = "{0}/topic/{1}/organize/entire".\
                        format(ZHI_HU_URL, item[0][2])
                    yield TopicNode(url)
                elif item[0][0] == "load":
                    data_token = item[0][2]
                    data_parent = item[0][3]

            if data_token is None and data_parent is None:
                return
            post_url = "{0}?child={1}&parent={2}".\
                format(self.url, data_token, data_parent)
