#!/usr/bin/python
# encoding=utf-8


from bs4 import BeautifulSoup

from zhihu.network import DownloadPage
from zhihu.network import get_url_id
from zhihu.utility import remove_blank_lines
from zhihu.setting import ZHI_HU_URL
from zhihu import answer
from zhihu import user


class Collection(object):
    def __init__(self, url):
        self.download_page = DownloadPage.instance()
        response = self.download_page.get_request(url)
        self.soup = BeautifulSoup(response.content)
        self.url = url

    def get_collection_name(self):
        name = self.soup.find("h2", id="zh-fav-head-title").string
        name = remove_blank_lines(name)
        return name.encode("utf-8")

    def get_collection_id(self):
        return get_url_id(self.url)

    def get_collection_url(self):
        return self.url.encode("utf-8")

    def get_creator(self):
        soup = self.soup.find("h2", class_="zm-list-content-title")
        return user.User(ZHI_HU_URL + soup.a.get("href"))

    def get_answers_num(self):
        answer_urls = self.soup.find_all("a", class_="answer-date-link")
        return len(answer_urls)

    def get_answers(self):
        answer_urls = self.soup.find_all("a", class_="answer-date-link")
        for item in answer_urls:
            yield answer.Answer(ZHI_HU_URL + item.get("href"))

    def get_followers_num(self):
        follower_url = self.url.split("/")[-2:]
        follower_url = "/" + "/".join(follower_url)
        follower_url = follower_url + "/followers"
        soup = self.soup.find("a", href=follower_url)
        return int(soup.string)

    def get_followers(self):
        follower_url = self.url + "/followers"
        response = self.download_page.get_request(follower_url)
        if response is None:
            return

        follower_soup = BeautifulSoup(response.content)
        follower_list = follower_soup.find_all("a", class_="zg-link")
        for item in follower_list:
            yield user.User(item.get("href"))

        page_num = (self.get_followers_num() - 1) / 20 + 1

        if page_num <= 1:
            return

        xsrf = follower_soup.find(
            "input", attrs={"name": "_xsrf"}).get("value")
        data = {"_xsrf": xsrf, "offset": 0}

        for offset in range(20, (page_num * 20 + 20), 20):
            data["offset"] = offset
            response = self.download_page.post_request(follower_url, data=data)
            content = response.json()['msg'][1]
            follower_soup = BeautifulSoup(content)
            follower_list = follower_soup.find_all("a", class_="zg-link")
            for item in follower_list:
                yield user.User(item.get("href"))
