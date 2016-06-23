#!/usr/bin/python
# encoding=utf-8


from bs4 import BeautifulSoup

from zhihu.network import default_net_request
from zhihu.network import get_url_id
from zhihu.utility import remove_blank_lines
from zhihu.setting import ZHI_HU_URL
import zhihu.answer
import zhihu.user


class Collection(object):
    def __init__(self, url):
        response = default_net_request.get_request(url)
        self.soup = BeautifulSoup(response.content, "lxml")
        self.url = url

    def get_collection_name(self):
        """ 收藏夹名称
            rtype: str
        """
        name = self.soup.find("h2", id="zh-fav-head-title").get_text()
        print name
        name = remove_blank_lines(name)
        return name.encode("utf-8")

    def get_collection_id(self):
        """ 收藏夹ID
            rtype: str
        """
        return get_url_id(self.url)

    def get_collection_url(self):
         """ 收藏夹URL
             rtype: str
         """
         return self.url.encode("utf-8")

    def get_creator(self):
        """ 收藏夹创建者
            rtype: User.Iterable
        """
        soup = self.soup.find("h2", class_="zm-list-content-title")
        return zhihu.user.User(ZHI_HU_URL + soup.a.get("href"))

    def get_answers_num(self):
        """ 收藏夹回答数量
            rtype: int
        """
        answer_urls = self.soup.find_all("a", class_="answer-date-link")
        return len(answer_urls)

    def get_answers(self):
        """ 收藏夹收藏回答
            rtype: Answer.Iterable
        """
        answer_urls = self.soup.find_all("a", class_="answer-date-link")
        for item in answer_urls:
            yield zhihu.answer.Answer(ZHI_HU_URL + item.get("href"))

    def get_followers_num(self):
        """ 收藏夹关注数量
            rtype: int
        """
        follower_url = self.url.split("/")[-2:]
        follower_url = "/" + "/".join(follower_url)
        follower_url = follower_url + "/followers"
        soup = self.soup.find("a", href=follower_url)
        return int(soup.get_text())

    def get_followers(self):
        """ 收藏夹关注者
            rtype: User.Iterable
        """
        follower_url = self.url + "/followers"
        response = default_net_request.get_request(follower_url)
        if response is None:
            return

        follower_soup = BeautifulSoup(response.content, "lxml")
        follower_list = follower_soup.find_all("a", class_="zg-link")
        for item in follower_list:
            yield zhihu.user.User(item.get("href"))

        page_num = (self.get_followers_num() - 1) / 20 + 1

        if page_num <= 1:
            return

        xsrf = follower_soup.find(
            "input", attrs={"name": "_xsrf"}).get("value")
        data = {"_xsrf": xsrf, "offset": 0}

        for offset in range(20, (page_num * 20 + 20), 20):
            data["offset"] = offset
            response = default_net_request.post_request(follower_url, data=data)
            content = response.json()['msg'][1]
            follower_soup = BeautifulSoup(content, "lxml")
            follower_list = follower_soup.find_all("a", class_="zg-link")
            for item in follower_list:
                yield zhihu.user.User(item.get("href"))
