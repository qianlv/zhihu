#!/usr/bin/python
# encoding=utf-8

import json

from bs4 import BeautifulSoup

from zhihu.network import DownloadPage
from zhihu.network import get_url_id
from zhihu.utility import get_number_from_string
from zhihu.setting import ZHI_HU_URL
# from zhihu.logger import logger
from zhihu import answer
from zhihu import question
from zhihu import topic
from zhihu import collection


class User(object):
    ''' Parse zhihu the web page of user.
        User(url, [name, user_id])
        url: the url of user.
        name: the name of user.
        user_id: the id of user.
    '''
    def __init__(self, url):
        if url and url[-1] == '/':
            url = url[0:-1]
        self.download_page = DownloadPage.instance()
        response = self.download_page.get_request(url)
        self.soup = BeautifulSoup(response.content)
        self.url = url

    def __nonzero__(self):
        if self.url is None or self.soup is None:
            return False
        return True

    def get_user_name(self):
        ''' return the name of user, return None when user doesn't exist.
        '''
        soup = self.soup.find(
            "div",
            attrs={"class": "title-section ellipsis"}
        )
        user_name = soup.span.string
        return user_name.encode("utf-8")

    def get_user_id(self):
        ''' Return the id of user '''
        return get_url_id(self.url)

    def get_upvote_num(self):
        ''' Return upvote(up vote) number of user.'''
        soup = self.soup.find(
            "span",
            attrs={"class": "zm-profile-header-user-agree"}
            ).strong
        agrees_num = int(soup.string)
        return agrees_num

    def get_thanks_num(self):
        ''' Return thanks number of user.'''
        soup = self.soup.find(
            "span",
            attrs={"class": "zm-profile-header-user-thanks"}
            ).strong
        thanks_num = int(soup.string)

        return thanks_num

    def get_asks_num(self):
        ''' Return ask number of user.'''
        return self.get_action_num()[0]

    def get_answers_num(self):
        ''' Return answers number of user.'''
        return self.get_action_num()[1]

    # 专栏文章数
    def get_posts_num(self):
        ''' Return post number of user.'''
        return self.get_action_num()[2]

    def get_collections_num(self):
        ''' Return collection number of user. '''
        return self.get_action_num()[3]

    def get_logs_num(self):
        ''' Return log number of user. '''
        return self.get_action_num()[4]

    def get_action_num(self):
        action_num = []
        soup = self.soup.find(
            "div",
            attrs={"class": "profile-navbar clearfix"})
        for num in soup.find_all("a")[1:]:
            action_num.append(int((num.span.string)))

        return action_num

    def get_followers_num(self):
        ''' Return follower number of user.'''
        soup = self.soup.find(
            "div",
            attrs={"class": "zm-profile-side-following zg-clear"})
        follower_num = int(soup.find_all("strong")[1].string)

        return follower_num

    def get_followees_num(self):
        ''' Return the number of user which current user follow.'''
        soup = self.soup.find(
            "div",
            attrs={"class": "zm-profile-side-following zg-clear"})
        followees_num = int(soup.find_all("strong")[0].string)

        return followees_num

    # 获取我关注的人信息
    def get_followees(self, threshold=2):
        ''' Return iterable of user (url, name) which current user follow.
            threshold is to filter some user which the number of follower,
            ask, answer, upvote more than 0 less than threshold.
        '''
        return self.__get_followees_or_follwers(
            self.url + "/followees",
            self.get_followees_num(),
            threshold)

    def get_followees_user(self, threshold=2):
        ''' Return iterable of User class which current user follow.
            threshold is to filter some user which the number of follower,
            ask, answer, upvote more than 0 less than threshold.
        '''
        followees_iter = self.get_followees(threshold)
        for url, name in followees_iter:
            yield User(url)

    def get_followers(self, threshold=2):
        ''' Return iterable of user (url, name) which follow current user.
            threshold is to filter some user which the number of follower,
            ask, answer, upvote more than 0 less than threshold.
        '''
        return self.__get_followees_or_follwers(
            self.url + "/followers",
            self.get_followers_num(),
            threshold)

    # 获取关注我的人的信息
    def get_followers_user(self, threshold=2):
        ''' Return iterable of User which follow current user.
            threshold is to filter some user which the number of follower,
            ask, answer, upvote more than 0 less than threshold.
        '''
        followers_iter = self.get_followers(threshold)
        for url, name in followers_iter:
            yield User(url)

    def __get_followees_or_follwers(self, url, num, threshold):
        if num is None or num <= 0:
            return

        # 判断这个用户是否符合条件
        def check(all_a_tag):
            threshold_list = [
                get_number_from_string(item.string)[0]
                for item in all_a_tag[1:]]
            threshold_value = reduce(
                lambda x, y: x + (1 if y > 0 else 0),
                threshold_list, 0)
            if threshold_value < threshold or \
                    all_a_tag[0].get("title") == u'[已重置]':
                return False
            return True

        page_num = (num - 1) / 20 + 1
        response = self.download_page.get_request(url)
        follow_soup = BeautifulSoup(response.content)
        follow_tag = follow_soup.find(
            "div", attrs={"class": "zh-general-list clearfix"})
        follow_div = follow_tag.find_all(
            "div", attrs={"class": "zm-list-content-medium"})
        for follow_user in follow_div:
            all_a_tag = follow_user.find_all("a")
            if not check(all_a_tag):
                continue

            url = all_a_tag[0].get("href")
            yield (url, all_a_tag[0].get("title"))

        if page_num <= 1:
            return
        # 初始化data数据
        data_init = json.loads(follow_tag.get("data-init"), encoding='utf-8')
        input_tag = follow_soup.find(
            "input", attrs={"type": "hidden", "name": "_xsrf"})
        value = input_tag.get("value")
        post_url = ZHI_HU_URL + "/node/" + data_init['nodename']

        for offset in range(20, page_num * 20 + 20, 20):
            data_init["params"]["offset"] = offset
            data = {
                "_xsrf": value,
                "method": "next",
                "params": json.dumps(data_init["params"])
            }
            response = self.download_page.post_request(post_url, data)
            for content in response.json()['msg']:
                soup = BeautifulSoup(content)
                follow_div = soup.find(
                    "div", attrs={"class": "zm-list-content-medium"})
                all_a_tag = follow_div.find_all("a")
                if not check(all_a_tag):
                    continue
                url = all_a_tag[0].get("href")
                yield (url, all_a_tag[0].get("title"))

    # 关注话题数
    def get_topics_num(self):
        ''' Return topic number which user follow.'''
        url = self.url.replace(ZHI_HU_URL, "") + "/topics"
        topics_num = get_number_from_string(
            self.soup.find("a", href=url).strong.string)[0]
        return topics_num

    # 关注的话题
    def get_topics(self):
        ''' Return Topic iterable which current user follow.'''
        num = self.get_topics_num()
        if num is None or num <= 0:
            return
        page_num = (num - 1) / 20 + 1

        post_url = self.url + "/topics"
        response = self.download_page.get_request(post_url)
        topic_soup = BeautifulSoup(response.content)
        topic_tag = topic_soup.find(
            "div", attrs={"id": "zh-profile-topic-list"})
        topic_a = topic_tag.find_all(
            "a", attrs={"class": "zm-list-avatar-link"})
        for a_tag in topic_a:
            url = ZHI_HU_URL + a_tag.get("href")
            yield topic.Topic(url)

        if page_num <= 1:
            return

        # 初始化data数据
        input_tag = topic_soup.find(
            "input", attrs={"type": "hidden", "name": "_xsrf"})
        value = input_tag.get("value")
        for offset in range(20, page_num * 20 + 20, 20):
            data = {
                "_xsrf": value,
                "offset": offset,
                "start": 0
            }
            response = self.download_page.post_request(post_url, data)
            content = response.json()['msg'][1]
            soup = BeautifulSoup(content)
            topic_a = soup.find_all(
                "a", attrs={"class": "zm-list-avatar-link"})
            for a_tag in topic_a:
                url = ZHI_HU_URL + a_tag.get("href")
                yield topic.Topic(url)

    # 关注的专栏数
    def get_follow_posts_num(self):
        ''' Return follow post number. '''
        url = self.url.replace(ZHI_HU_URL, "") + "/columns/followed"
        follow_posts_num = get_number_from_string(
            self.soup.find("a", href=url).strong.string)[0]
        return follow_posts_num

    # 回答的问题
    def get_answers(self):
        ''' Return Answer of user.'''
        num = self.get_answers_num()
        if num is None or num <= 0:
            return
        page = (num + 19) / 20

        for i in range(1, page + 1):
            get_url = "%s/answers?page=%d" % (self.url, i)
            response = self.download_page.get_request(get_url)
            soup = BeautifulSoup(response.content)
            answer_list = soup.find(
                "div", id="zh-profile-answer-list"
            ).find_all("a", class_="question_link")
            for item in answer_list:
                url = ZHI_HU_URL + item.get("href")
                yield answer.Answer(url)

    # 提的问题
    def get_asks(self):
        ''' Return Question which current user asked.'''
        num = self.get_asks_num()
        if num is None or num <= 0:
            return
        page = (num + 19) / 20

        for i in range(1, page + 1):
            get_url = "%s/asks?page=%d" % (self.url, i)
            response = self.download_page.get_request(get_url)
            soup = BeautifulSoup(response.content)
            ask_list = soup.find(
                "div", id="zh-profile-ask-list"
            ).find_all("a", class_="question_link")
            for item in ask_list:
                url = ZHI_HU_URL + item.get("href")
                yield question.Question(url)

    # 收藏夹
    def get_collections(self):
        ''' Return Collection which user created.'''
        num = self.get_collections_num()
        if num is None or num <= 0:
            return
        page = (num + 19) / 20

        for i in range(1, page + 1):
            get_url = "%s/collections?page=%d" % (self.url, i)
            response = self.download_page.get_request(get_url)
            soup = BeautifulSoup(response.content)
            collection_list = soup.find_all(
                "a", class_="zm-profile-fav-item-title")
            for item in collection_list:
                url = ZHI_HU_URL + item.get("href")
                yield collection.Collection(url)


class UserBrief(object):
    ''' Get zhihu user brief information.'''
    def __init__(self, user_id):
        params = {"url_token": user_id}
        params = {"params": json.dumps(params)}
        self.user_id = user_id
        self.url = ZHI_HU_URL + "/node/MemberProfileCardV2"
        self.download_page = DownloadPage.instance()
        response = self.download_page.get_request(self.url, params=params)
        self.soup = BeautifulSoup(response.content)

    def get_user_id(self):
        ''' Return the id of user.'''
        return self.user_id

    def get_user_name(self):
        ''' Return the name of user.'''
        user_name = self.soup.find("span", class_="name").string
        return user_name

    def deal_num(self, num):
        return num

    def get_followers_num(self):
        ''' Return follower number of user.'''
        followers_num = self.soup.find_all(
            "span", class_="value")[2].string
        followers_num = self.deal_num(followers_num)
        return followers_num
