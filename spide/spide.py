import time
from threading import Thread, Timer,current_thread
from queue import Queue
from tqdm import tqdm

max_proxies = 2
q_proxies = Queue(200)
q_tasks = Queue(max_proxies)
sleep_time = 1
running_state = "on running"

# TODO 需要定义func/validation/函数
# *****************************

def func(url):
    err_time = 0
    item = q_data.get()
    index = item["index"]
    category = item["行业类别"]
    name = item["单位名称"]
    unique_id = item["许可证编号"]
    dataid = item["查看"].split("dataid=")[1]
    path = f'许可信息公开/{category}/{name}{unique_id}/'
    print("正在下载第%s个文件\n" % index)
    # 创建文件夹
    for floder in ["基础信息", "许可证副本", "大气污染物排放信息", "水污染物排放信息", "其他许可内容"]:
        if not os.path.exists(path + floder):
            os.makedirs(path + floder)
    # 分别列出大气,水,其他的url,然后对每一个进行循环
    base_url = "http://permit.mee.gov.cn/perxxgkinfo/xkgkAction!xkgk.action?xkgk=getxxgkContent&dataid=%s" % dataid
    air_url = "http://permit.mee.gov.cn/perxxgkinfo/xkgkAction!xkgk.action?xkgk=approveAtmosphere_xkzgk&dataid=%s&isVersion=&operate=readonly" % dataid
    water_url = "http://permit.mee.gov.cn/perxxgkinfo/xkgkAction!xkgk.action?xkgk=approveWater_xkzgk&dataid=%s&isVersion=&operate=readonly" % dataid
    other_url = "http://permit.mee.gov.cn/perxxgkinfo/xkgkAction!xkgk.action?xkgk=approveothercon_xkzgk&dataid=%s&operate=readonly" % dataid
    flag = True
    while True:
        if err_time > 10:
            data.loc[index, "副本下载状态"] = 3
            break
        try:
            #  下载副本文件
            url_base = "http://permit.mee.gov.cn/perxxgkinfo/syssb/wysb/hpsp/hpsp-company-sewage!showImage.action?dataid=%s" % dataid
            # todo 加代理
            # 分析页面得到id这些内容,再使用他们去获取附件文件的路径,再去下载附件.
            response = requests.get(url_base, proxies=proxies, timeout=timeout)

            # 获取到的文字是没有重定向且不为空的
            if response.text == "":
                data.loc[index, "副本下载状态"] = 3
                print(f"------------------{index}-----")
                break
            elif response.history != []:
                print("重新定向")
                proxies, expire_time = q_proxies.get()
                check()
                break

            content = bs4.BeautifulSoup(response.text, "html.parser")
            imageDiv = content.find("body").find("div", id="imageDiv")
            imgCount = imageDiv.find("input", id="imgCount").get("value")
            pkid = imageDiv.find("input", id="pkid").get("value")
            for i in range(1, int(imgCount) + 1):
                url = f"http://permit.mee.gov.cn/perxxgkinfo/syssb/xkgg/xkgg!downFilePng.action?datafileid={pkid}_{i}&fileType=pdffile&dataid={dataid}"
                flag = True
                while True:
                    img = requests.get(url, proxies=proxies)
                    if response.text == "":
                        data.loc[index, "副本下载状态"] = 3
                        print(f"------------------{index}--------------------------------")
                        flag = False
                        break
                    elif response.history != []:
                        proxies, expire_time = q_proxies.get()
                    else:
                        break
                if flag:
                    with open(path + "许可证副本/" + str(i) + ".png", 'wb') as f:
                        f.write(img.content)
            break
        except:
            proxies, expire_time = q_proxies.get()
            err_time = err_time + 1
            check()
    if not data.loc[index, "副本下载状态"] == 3:
        data.loc[index, "副本下载状态"] = 2
    check()


    return current_thread().name


def validation(content):
    print(Thread.isAlive(content))
    return Thread.isAlive(content)
# ******************************

# 分别启动任务管理器,代理获取器,多个子线程.
def start(proxies_url, thread_num):
    task_publisher = Thread(target=get_task, name="task_publisher", daemon=True)
    proxies_publisher = Thread(target=get_proxies, name="proxies_publisher",args=proxies_url)
    thread_list = []
    for i in range(0, thread_num):
        print(accept_task(), q_proxies.get())
        thread_list.append(ThreadTask(func, validation, accept_task(), q_proxies.get()))
    for i in thread_list:
        i.start()
    for i in thread_list:
        i.join()
    print("well done")





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
    proxies_list = proxies_url
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
    proxies_url = "proxies_url"
    thred_num = 2
    start(proxies_url, thred_num)
