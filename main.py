#encoding=utf-8
from zhihu.webparse import answer, topic, question
from zhihu.webparse import user, collection

def test_answer():
    my_answer = answer.Answer("http://www.zhihu.com/question/28626263/answer/41992632")
    print "所属问题:", my_answer.get_question().get_title()
    print "作者:", my_answer.get_auther().get_user_name()
    print "赞同数:", my_answer.get_voter_num()
    voters = my_answer.get_voters().next()
    print "其中一个赞同者:", voters[0], voters[1]
    print "回答时间:", my_answer.get_answer_time()
    print "属于的话题:"
    for tp in my_answer.get_topics_name_and_url():
        print tp[0], tp[1]
    print "回答内容:", my_answer.get_content()


def test_topic():
    my_topic = topic.Topic("http://www.zhihu.com/topic/19570098")
    print "话题名:", my_topic.get_topic_name()
    print "话题问题页数:", my_topic.get_topic_page_num()
    print "话题下的关注数:", my_topic.get_topic_follower_num()
    print "其中一个问题:"
    my_question = my_topic.get_questions().next()
    print my_question.get_title()
    print my_question.get_detail()
    print my_question.get_answers_num()
    print my_question.get_follower_num()
    for tp in my_question.get_topics():
        print tp.get_topic_name()
    
    print '话题树的一个节点:'
    my_topic_node = topic.TopicNode("http://www.zhihu.com/topic/19612637/organize/entire")
    print "节点名字:", my_topic_node.get_node_name()
    print "节点URL:", my_topic_node.get_node_url()
    print "话题ID:", my_topic_node.get_topic_id()
    print "话题URL:", my_topic_node.get_topic_url()
    print "话题问题页数:", my_topic_node.get_topic().get_topic_page_num()
    print "子节点:"
    childs = my_topic_node.get_children_nodes()
    for child in childs:
        print child.get_node_name()

def test_question():
    url = u'http://www.zhihu.com/question/22808635'
    problem = question.Question(url)
    print "问题题目:", problem.get_title()
    print "问题详细描述:", problem.get_detail()
    print "问题回答个数:", problem.get_answers_num()
    print "问题关注数量:", problem.get_follower_num()
    print "问题所属话题:"
    topics = problem.get_topics()
    for my_topic in topics:
        print my_topic.get_topic_name()
    print '回答作者:'
    count = 0
    for ans in problem.get_answers():
        count +=1
        print '------', count
        print ans.get_auther().get_user_name()


#print '--------Test Answer--------'
#test_answer()
#print '------- Test Topic -------'
#test_topic()
print '------ Test Question ------'
test_question()
