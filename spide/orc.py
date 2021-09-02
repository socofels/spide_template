import time, json, base64, hashlib, requests, os,tqdm,math
import pandas as pd
from threading import Thread,Lock
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


def xunfei_orc(img_url,headers):
    # 上传文件并进行base64位编码
    with open(img_url, 'rb') as f:
        f1 = f.read()
    f1_base64 = str(base64.b64encode(f1), 'utf-8')
    data = {
        'image': f1_base64
    }
    r = requests.post(URL, data=data, headers=headers)
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
def find_inf(word):
    data=[0,0]
    flag=False
    for k in word:
        if "518" in k:
            data[0]=k
            flag=True
        if "简化管理" in k:
            data[1] = "简化管理"
        if "重点管理" in k:
            data[1] = "重点管理"
    if flag:
        return data
    else:
        return []
# 获取文件
# 如果副本下载状态为2，
# 而且图片5存在的话则下载图片5
# 寻找信息，如果找到了邮编信息则保存邮编信息,与管理类型
# 如果图片5找不到信息则下载图片6，
# 寻找信息，如果找到了邮编信息则保存邮编信息,与管理类型
# 保存到文件
lock=Lock()
def write_data(path,index,column,value):
    lock.acquire()
    datafram=pd.read_csv(path)
    datafram.loc[index,column]=value
    datafram.to_csv(path)
    lock.release()
def orc(myrange):
    headers = getHeader()
    xxgk = pd.read_csv("F:\PL\ssl\spide_template\data\许可信息公开.csv", index_col=0)
    for i in tqdm.tqdm(range(myrange[0],myrange[1])):
        yb=str(xxgk.loc[i, "邮编"])
        if xxgk.loc[i, "副本下载状态"] == 2:
            if not yb:
                if "518" in yb:
                    continue
            else:
                path = f"F:\PL\ssl\spider_排污许可\许可信息公开/{xxgk.loc[i, '行业类别']}/{xxgk.loc[i, '单位名称']}{xxgk.loc[i, '许可证编号']}/许可证副本"
                if os.path.exists(path + "/5.png"):
                    try:
                        if os.path.getsize(path + "/5.png") != 520:
                            word = turn_to_list(xunfei_orc(path + "/5.png",headers))
                            xxgk.loc[i,"第五页"]=str(word)
                            find_word=find_inf(word)
                            if find_word:
                                xxgk.loc[i, "邮编"] = find_word[0]
                                xxgk.loc[i, "管理类型"] = find_word[1]
                            else:
                                if os.path.exists(path + "/6.png"):
                                    word = turn_to_list(xunfei_orc(path + "/6.png",headers))
                                    xxgk.loc[i, "第六页"] = str(word)
                                    find_word = find_inf(word)
                                    if find_word:
                                        xxgk.loc[i, "邮编"] = find_word[0]
                                        xxgk.loc[i, "管理类型"] = find_word[1]
                    except Exception as e:
                        print(e)
            write_data("F:\PL\ssl\spide_template\data\许可信息公开.csv", i, xxgk.loc[i, "邮编"], xxgk.loc[i, "管理类型"])


q1=Thread(target=orc,args=([[0,1000]]))
q2=Thread(target=orc,args=([[1000,2000]]))
q3=Thread(target=orc,args=([[2000,3000]]))
q4=Thread(target=orc,args=([[3000,4000]]))
q5=Thread(target=orc,args=([[4000,5000]]))
q6=Thread(target=orc,args=([[5000,5270]]))

q1.start()
q2.start()
q3.start()
q4.start()
q5.start()
q6.start()

q1.join()
q2.join()
q3.join()
q4.join()
q5.join()
q6.join()

