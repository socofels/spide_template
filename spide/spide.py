import time
from threading import Thread, Timer
from queue import Queue
from tqdm import tqdm

max_proxies = 10
q_proxies = Queue(200)
q_tasks = Queue(max_proxies)
sleep_time = 1
running_state = "on running"


# 分别启动任务管理器,代理获取器,多个子线程.
def start(proxies_url, thread_num):
    task_publisher = Thread(target=get_task(), name="task_publisher", daemon=True)
    proxies_publisher = Thread(target=get_proxies(proxies_url), name="proxies_publisher")
    thread_list = []
    for i in range(0, thread_num):
        thread_list.append(ThreadTask(func, validation, q_tasks.get(), q_proxies.get()))
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
# 一直加载任务,当所有任务加载完成时修改running_state为结束
def get_task():
    """获取任务,每隔0.1秒检测一次是否需要添加新任务"""
    global q_tasks, running_state
    task_list = []
    for i in tqdm(task_list):
        while True:
            if not q_tasks.full():
                q_tasks.put(task_list)
                break
            else:
                time.sleep(0.1)
    running_state = "close"


def accept_task():
    while running_state == "on running" or not q_tasks.empty():
        if not q_tasks.empty():
            task = q_tasks.get()
            return task
        else:
            time.sleep(0.1)
    return "close"


# todo 获取proxies添加到队列中
def get_proxies(proxies_url):
    """获取任务,每隔0.1秒检测一次是否需要更新代理"""
    global q_proxies, max_proxies
    flag = True
    while flag:
        if q_proxies.empty():
            proxies_list = request_proxies(proxies_url)
            for i in proxies_list:
                q_proxies.put(i)
        time.sleep(0.1)


# todo 返回代理的列表,一定确保能返回正确的列表,否则一直循环等待,
def request_proxies(proxies_url):
    proxies_list = ?
    return proxies_list


# 多线程类
class ThreadTask(Thread):
    """单线程任务,需要给函数与参数
    """

    def __init__(self, func, validation, task, proxy):
        super().__init__()
        self.func = func
        self.validation = validation
        self.task = task
        self.proxy = proxy

    def run(self):
        # flag表示任务是否继续,当flag==False表示没有更多任务了
        flag = True
        while flag:
            if not flag:
                break
            else:
                # 执行任务:执行逻辑
                # 1.尝试获取内容
                # 2.如果超时则更换一次代理,并记上错误次数+1
                # 3.如果发现返回的页面非预期的页面则更换代理,并记上错误数+1
                # 4.如果得到正常页面则错误计数清零,开始下一个任务.
                # 5.当错误次数累计到一定值时更换任务并记录这条失败的任务
                err_time = 0
                while err_time < 10:
                    try:
                        result = self.func(self.task, self.proxy)
                        val = self.validation(result)
                        # validation应当给出三种结论代理失效,非正常页面,正常
                        if val == "Expired proxy" or val == "Unexpected response":
                            err_time = err_time + 1
                            proxy = q_proxies.get()
                        else:
                            err_time = 0
                            # todo 修改为需要的操作--------
                            print("任务完成")
                            # -------------------
                            self.task = accept_task()
                    except:
                        err_time = err_time + 1
                        proxy = q_proxies.get()

                # 更新任务
                task = accept_task()
                if task == "clsoe":
                    flag = False
                time.sleep(sleep_time)


if "__main__" == __name__:
    proxies_url = "123"
    thred_num = 10
    start(proxies_url, thred_num)
