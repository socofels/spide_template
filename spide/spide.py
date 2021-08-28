import time
from threading import Thread, Timer
from queue import Queue

max_proxies=10
q_proxies = Queue(200)
q_tasks = Queue(max_proxies)

# 分别启动任务管理器,代理获取器,多个子线程.
def start(proxies_url, thread_num):
    task_publisher=Thread(target=get_task(),name="task_publisher",daemon=True)
    proxies_publisher=Thread(target=get_proxies(proxies_url),name="proxies_publisher")
    thread_list=[]
    for i in range(0,thread_num):
        thread_list.append(ThreadTask(func,validation,q_tasks.get()))
    for i in thread_list:
        i.start()
    for i in thread_list:
        i.join()
    print("well done")
# todo 需要定义func/validation/函数
def func():
    pass

def validation():
    pass

# todo 获取任务函数,添加内容到task里
def get_task():
    """获取任务,每隔0.1秒检测一次是否需要添加新任务"""
    global q_tasks
    flag = True
    task_list = []
    while flag:
        for i in task_list:
            while True:
                if not q_tasks.full():
                    q_tasks.put(task_list)
                    break
                else:
                    time.sleep(0.1)
        flag = False


# todo 获取proxies添加到队列中
def get_proxies(proxies_url):
    """获取任务,每隔0.1秒检测一次是否需要更新代理"""
    global q_proxies,max_proxies
    flag = True
    while flag:
        if q_proxies.empty():
            proxies_list = request_proxies(proxies_url)
            for i in proxies_list:
                q_proxies.put(i)
        time.sleep(0.1)


# todo 返回代理的列表,一定确保能返回正确的列表,否则一直循环等待,
def request_proxies(proxies_url):
    proxies_list = [["proxies"]]
    return proxies_list


# 多线程类
class ThreadTask(Thread):
    """单线程任务,需要给函数与参数
    """

    def __init__(self, func, validation, *args):
        super().__init__()
        self.func = func
        self.validation = validation
        self.args = args

    def run(self):
        result = self.func(self.args)
        if self.validation(result):
            return result


if "__main__" == __name__:
    proxies_url = "123"
    thred_num = 10
    start(proxies_url, thred_num)
