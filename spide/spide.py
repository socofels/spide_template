import threading
import time, os, requests, bs4
import pandas as pd
from threading import Thread, Timer, current_thread
from queue import Queue
from tqdm import tqdm
from fake_useragent import UserAgent
from units.unit import creat_dir,detect,GetOuterIP
import logging


# [url,header,data,params,task]
# TODO 需要定义func/validation/函数
# *****************************
# 根据url获取副本的下载链接,然后下载链接
def func(params, proxies):
    if params == "close":
        return "close"
    else:
        #  下载副本文件
        task = params["task"]
        dataid = task["查看"].split("dataid=")[1]
        url = "http://permit.mee.gov.cn/perxxgkinfo/syssb/wysb/hpsp/hpsp-company-sewage!showImage.action?dataid=%s" % dataid
        try:
            response = requests.get(url=url, headers=params["headers"], proxies=proxies)
            return response
        except Exception as e:
            print(e)
            return "error"


def validation(response):
    if response == "error":
        return "Expired proxy"
    elif response.content == "请您访问permit.mee.gov.cn，点击许可信息公开查询企业排污许可证信息，谢谢。" or response.history != []:
        return "Unexpected response"
    else:
        return True


def task_manage(thread_list):
    global running_state, q_tasks
    while running_state == "on running" or not q_tasks.empty():
        task_list = pd.DataFrame(columns=["线程", "状态", "运行时长", "已完成任务数"])
        for thread in thread_list:
            task_list=task_list.append({"线程": thread.ident, "状态": thread.is_alive(), "运行时长": thread.end_time - thread.start_time,
                              "已完成任务数": thread.completed}, True)

        print("\r%s"%task_list)
        time.sleep(1)


# ******************************

# 分别启动任务管理器,代理获取器,多个子线程.
def start(proxies_url, thread_num):
    task_publisher = Thread(target=get_task, name="task_publisher", daemon=True)
    proxies_publisher = Thread(target=get_proxies, name="proxies_publisher", args=[proxies_url])
    task_publisher.start()
    proxies_publisher.start()
    thread_list = []
    for i in range(0, thread_num):
        thread_list.append(ThreadTask(func, validation, accept_task(), accept_proxies()))
    for i in thread_list:
        i.start()
    task_manager=Thread(target=task_manage,name="task_manager",args=[thread_list])
    task_manager.start()
    for i in thread_list:
        i.join()
    task_publisher.join()
    proxies_publisher.join()
    task_manager.join()
    print("well done")


# todo 获取任务函数,添加内容到task里
# 一直加载任务,当所有任务加载完成时修改running_state为结束
def get_task():
    """获取任务,每隔0.1秒检测一次是否需要添加新任务"""
    global q_tasks, running_state
    task_list = pd.read_csv(r"C:\Users\fjh\PycharmProjects\spide_template\data\许可信息公开.csv")
    # task_list = pd.read_csv(r"C:\Users\fjh\PycharmProjects\spide_template\data\许可信息公开0.csv")

    # print(task_list)
    for i in task_list.index:
        if task_list.loc[i, "副本下载状态"] == 0:
            while True:
                if not q_tasks.full():
                    new_serise = {}
                    new_serise["task"] = dict(task_list.loc[i])
                    new_serise["url"] = "http://permit.mee.gov.cn" + new_serise["task"]["查看"]
                    new_serise["headers"] = {'user-agent': UserAgent().random}
                    q_tasks.put(new_serise)
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
            try:
                proxies_list = request_proxies(proxies_url)
                for i in proxies_list.index:
                    proxy = {"http": "http://%(ip)s:%(port)s" % proxies_list.loc[i, "data"]}
                    # print(proxy)
                    q_proxies.put(proxy)
            except:

                time.sleep(1)
        time.sleep(0.1)


# 返回一个proxies
def accept_proxies():
    while q_proxies.empty():
        # print("没有代理")
        time.sleep(0.1)
    return q_proxies.get()


# todo 返回代理的列表,一定确保能返回正确的列表,否则一直循环等待,
def request_proxies(proxies_url):
    proxies_list = pd.read_json(proxies_url)
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
        self.start_time = time.time()
        self.end_time = time.time()
        self.completed = 0

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
                        # print("执行任务")
                        result = self.func(self.task, self.proxy)
                        if result == "close":
                            flag = False
                            break
                        val = self.validation(result)
                        # print(val)
                        # validation应当给出三种结论代理失效,非正常页面,正常
                        if val == "Expired proxy" or val == "Unexpected response":
                            err_time = err_time + 1
                            self.proxy = accept_proxies()
                        else:
                            # print("没问题")
                            err_time = 0
                            # todo 修改为需要的操作--------
                            response = result
                            content = bs4.BeautifulSoup(response.text, "html.parser")
                            imageDiv = content.find("body").find("div", id="imageDiv")
                            # print("body")
                            imgCount = imageDiv.find("input", id="imgCount").get("value")
                            # print("input")
                            pkid = imageDiv.find("input", id="pkid").get("value")
                            # print("input")

                            dataid = self.task["task"]["查看"].split("dataid=")[1]
                            # print("没问题")
                            # print(imgCount)
                            for i in range(1, int(imgCount) + 1):
                                url = f"http://permit.mee.gov.cn/perxxgkinfo/syssb/xkgg/xkgg!downFilePng.action?datafileid={pkid}_{i}&fileType=pdffile&dataid={dataid}"
                                # print(url)
                                err_flag = 0
                                while err_flag < 10:
                                    self.end_time=time.time()
                                    try:
                                        logging.debug(url)
                                        img = requests.get(url, headers=self.task["headers"], proxies=self.proxy)
                                    except Exception as e:
                                        print(e)
                                        img = "error"
                                    finally:
                                        self.end_time = time.time()
                                    if validation(img) == "Expired proxy" or val == "Unexpected response":
                                        err_flag = err_flag + 1
                                        self.proxy = accept_proxies()
                                    else:
                                        while True:
                                            self.end_time = time.time()
                                            # 下载图片
                                            # print("下载图片")
                                            data = self.task["task"]
                                            index = data["index"]
                                            category = data["行业类别"]
                                            name = data["单位名称"]
                                            unique_id = data["许可证编号"]
                                            path = f'../data/许可信息公开/{category}/{name}{unique_id}/许可证副本/'
                                            creat_dir(path)
                                            file_path = path + str(i) + ".png"
                                            with open(file_path, 'wb') as f:
                                                f.write(img.content)
                                            if os.path.getsize(file_path) == 520:
                                                self.proxy = accept_proxies()
                                            else:
                                                # 准确无误的下载了一个文件
                                                self.completed += 1
                                                break
                                        break
                        # -------------------
                        self.task = accept_task()
                    except Exception as e:
                        print(e)
                        err_time = err_time + 1
                        self.proxy = accept_proxies()
                    finally:
                        self.end_time = time.time()
                # 更新任务
                task = accept_task()
                if task == "close":
                    flag = False
                time.sleep(sleep_time)
        print("线程 %s 已完成所有任务" % threading.currentThread().name)
import socket


def add_ip():
    ip=GetOuterIP()
    res=requests.get(f"http://pycn.yapi.3866866.com/index/index/save_white?neek=8887&appkey=7632dd76794bf3462378e3b7286bc70c&white={ip}")

if "__main__" == __name__:
    max_proxies = 1
    q_proxies = Queue(200)
    q_tasks = Queue(max_proxies)
    sleep_time = 1
    running_state = "on running"
    response_list = []
    logging.debug("start")
    proxies_url = "http://tiqu.pyhttp.taolop.com/getip?count=50&neek=8887&type=2&yys=0&port=1&sb=&mr=1&sep=0&ts=1&time=2"
    thred_num = 50
    add_ip()
    start(proxies_url, thred_num)
