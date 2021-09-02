import os, bs4
from fake_useragent import UserAgent
import requests
import time
import hashlib
import base64
import json
import pandas as pd


def creat_dir(path):
    """创建目录"""
    if not os.path.exists(path):
        os.makedirs(path)


def read_html(html):
    tables = pd.read_html(html)
    if tables == []:
        return False
    else:
        return tables


# from urllib import parse
# 印刷文字识别 webapi 接口地址
URL = "https://webapi.xfyun.cn/v1/service/v1/ocr/general"
# 应用ID (必须为webapi类型应用，并印刷文字识别服务，参考帖子如何创建一个webapi应用：http://bbs.xfyun.cn/forum.php?mod=viewthread&tid=36481)
APPID = "cfabcd3d"
# 接口密钥(webapi类型应用开通印刷文字识别服务后，控制台--我的应用---印刷文字识别---服务的apikey)
API_KEY = "e1365d96f278fcf5c0ffde3607ca7b95"


def getHeader():
    #  当前时间戳
    curTime = str(int(time.time()))
    #  支持语言类型和是否开启位置定位(默认否)
    param = {"language": "cn|en", "location": "false"}
    param = json.dumps(param)
    paramBase64 = base64.b64encode(param.encode('utf-8'))

    m2 = hashlib.md5()
    str1 = API_KEY + curTime + str(paramBase64, 'utf-8')
    m2.update(str1.encode('utf-8'))
    checkSum = m2.hexdigest()
    # 组装http请求头
    header = {
        'X-CurTime': curTime,
        'X-Param': paramBase64,
        'X-Appid': APPID,
        'X-CheckSum': checkSum,
        'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8',
    }
    return header


def xunfei_orc(img_url):
    # 上传文件并进行base64位编码
    with open(img_url, 'rb') as f:
        f1 = f.read()
    f1_base64 = str(base64.b64encode(f1), 'utf-8')
    data = {
        'image': f1_base64
    }
    r = requests.post(URL, data=data, headers=getHeader())
    result = str(r.content, 'utf-8')
    # 错误码链接：https://www.xfyun.cn/document/error-code (code返回错误码时必看)
    return result


def turn_to_list(orc_result):
    line = json.loads(orc_result)["data"]["block"][0]["line"]
    inf = []
    for i in line:
        for j in i["word"]:
            inf.append(j["content"])
    return inf


# 目前效果不理想的ORC
# def orc(img_path):
#     """需要安装tesseract,并且需要修改文件pytesseract_cmd为安装路径.例如下面
#     tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
#     """
#     print(os.path.exists(img_path))
#     text=pytesseract.image_to_string(Image.open(img_path),lang="chi_sim")
#     print(text)
#
# orc(r"C:/Users/fjh/Desktop/2e8dbdd2c51a460fbd88958193a9bae3_5.png")


# 遍历文件夹,检测副本是否正确完整
def detect():
    xxgk = pd.read_csv("../../data/许可信息公开.csv", index_col=0)
    for i in xxgk.index:
        if xxgk.loc[i, "副本下载状态"] == 0 or xxgk.loc[i, "副本下载状态"] == 1:
            path = f"../../data/许可信息公开/{xxgk.loc[i, '行业类别']}/{xxgk.loc[i, '单位名称']}{xxgk.loc[i, '许可证编号']}/许可证副本"

            if not os.path.exists(path):
                xxgk.loc[i, "副本下载状态"] = 0
            elif os.path.exists(path + "/5.png") and os.path.exists(path + "/6.png"):
                if os.path.getsize(path + "/5.png") == 520 or os.path.getsize(path + "/6.png") == 520:
                    xxgk.loc[i, "副本下载状态"] = 0
                else:
                    xxgk.loc[i, "副本下载状态"] = 2
            else:
                xxgk.loc[i, "副本下载状态"] = 0

    xxgk.to_csv("../../data/许可信息公开.csv")


# 删除空文件夹，空文件
def clean_empty_dir_and_file(path):
    """
    清理空文件夹和空文件
    param path: 文件路径，检查此文件路径下的子文件
    """
    print('*' * 30)
    try:
        files = os.listdir(path)  # 获取路径下的子文件(夹)列表
        print(files)
        for file in files:
            print('遍历路径：' + os.fspath(path + '/' + file))
            if os.path.isdir(os.fspath(path + '/' + file)):  # 如果是文件夹
                print(file + '是文件夹')
                if not os.listdir(os.fspath(path + '/' + file)):  # 如果子文件为空
                    print(file + '是空文件夹,即将执行删除操作')
                    os.rmdir(os.fspath(path + '/' + file))  # 删除这个空文件夹
                else:
                    print(file + '不是空文件夹')
                    clean_empty_dir_and_file(os.fspath(path + '/' + file))  # 遍历子文件
                    if not os.listdir(os.fspath(path + '/' + file)):  # 如果子文件为空
                        print(file + '是空文件夹,即将执行删除操作')
                        os.rmdir(os.fspath(path + '/' + file))  # 删除这个空文件夹
            elif os.path.isfile(os.fspath(path + '/' + file)):  # 如果是文件
                print(file + '是文件')
                if os.path.getsize(os.fspath(path + '/' + file)) == 0:  # 文件大小为0
                    print(file + '是空文件，即将执行删除操作！')
                    os.remove(os.fspath(path + '/' + file))  # 删除这个文件
        return
    except FileNotFoundError:
        print("文件夹路径错误")


def GetOuterIP():
    url = r'http://www.net.cn/static/customercare/yourip.asp'

    r = requests.get(url)
    # print(r.text)
    content = bs4.BeautifulSoup(r.text, 'html.parser')
    ip = content.find("center").find("h2").text
    return ip
detect()