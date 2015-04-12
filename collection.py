#!/usr/bin/python
#encoding=utf-8


import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import re

from bs4 import BeautifulSoup
from zhihuBase import ZhiHuPage, ZHI_HU_URL
import answer
import question
import user

class Collection(ZhiHuPage):
    def __init__(self, url, name=None, collection_id = None, answer_num = None):
        self.name = name
        self.collection_id = collection_id
        self.answer_num = answer_num
        super(Collection, self).__init__(url)

    def get_collection_name(self):
        if self.name == None:
            self.name = self.soup.find("h2", 
                    id="zh-fav-head-title").string
        return self.name

    def get_collection_id(self):
        if self.collection_id == None:
            self.collection_id = int(self.url.split("/")[4])
        return self.collection_id

    def get_collection_url(self):
        return self.url
    
    def get_creator(self):
        soup = self.soup.find("h2", 
                class_="zm-list-content-title")
        creator_name = soup.a.string
        return user.User(ZHI_HU_URL + soup.a.get("href"), creator_name)

    def get_answers_num(self):
        if self.answer_num == None:
            answer_urls = self.soup.find_all("a", class_="answer-date-link") 
            self.answer_num = len(answer_urls)
        return self.answer_num

    def get_answers(self):
        answer_urls = self.soup.find_all("a", class_="answer-date-link") 
        if self.answer_num == None:
            self.answer_num = len(answer_urls)
        for item in answer_urls:
            yield answer.Answer(ZHI_HU_URL + item.get("href"))

    def get_followers_num(self):
        if hasattr(self, "followers_num"):
            return self.followers_num
        else:
            follower_url = self.url.split("/")[-2:]
            follower_url = "/" + "/".join(follower_url)
            follower_url = follower_url + "/followers" 

            soup = self.soup.find("a", href=follower_url)
            self.followers_num = int(soup.string)

        return self.followers_num


    def get_followers(self):
        follower_url = self.url + "/followers"
        follower_soup = self.get_page(follower_url)
        follower_list = follower_soup.find_all("a", class_="zg-link")
        for item in follower_list:
            yield user.User(item.get("href"), name = item.string)

        page_num = (self.get_followers_num() - 1) / 20 + 1

        if page_num <= 1:
            return

        xsrf = follower_soup.find("input", 
                    attrs={"name":"_xsrf"}).get("value")
        data = {
                "_xsrf": xsrf,
                "offset": 0
                }
        for offset in range(20, (page_num * 20 + 20), 20):
            data["offset"] = offset
            response = self.get_post(follower_url, data = data)
            content = response.json()['msg'][1]
            follower_soup = BeautifulSoup(content)
            follower_list = follower_soup.find_all("a",
                            class_="zg-link")
            for item in follower_list:
                yield user.User(item.get("href"), name = item.string)


if __name__ == '__main__':
    my_coll = Collection("http://www.zhihu.com/collection/19644235")
    #print my_coll.get_collection_name()
    #print my_coll.get_collection_id()
    #print my_coll.get_collection_url()
    #print 'creator:'
    #print my_coll.get_creator().get_user_name()
    #print my_coll.get_creator().get_agree_num()


    #print 'answer:'
    #print my_coll.get_answers_num()
    #for ans in my_coll.get_answers():
    #    print ans.get_auther().get_user_name()

    print 'followers:'
    print my_coll.get_followers_num()
    for foll in my_coll.get_followers():
        print foll.get_user_name()
