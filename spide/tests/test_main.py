from spide.units.nuit import getHeader, xunfei_orc, turn_to_list
import pandas as pd
import os

path = "F:\PL\ssl\spider_排污许可"


# 遍历文件夹，修改下载状态
def detect():
    header = getHeader()
    download_list = pd.DataFrame(columns=["path", "status", "content"])
    download_list.loc[0] = ["path", "status", "content"]
    xxgk = pd.read_csv("F:/PL/ssl/spider_排污许可/data/许可信息公开.csv")
    for i in xxgk.index:
        path = f"F:/PL/ssl/spider_排污许可/许可信息公开/{xxgk.loc[i, '行业类别']}/{xxgk.loc[i, '单位名称']}{xxgk.loc[i, '许可证编号']}/许可证副本"
        if os.path.exists(path + "/5.png"):
            if not os.path.getsize(path + "/5.png") == 520:
                content = turn_to_list(xunfei_orc(path + "/5.png"))
                download_list.loc[download_list.index[-1]+1]=[path,0,content]
                download_list.to_csv(r"F:\PL\ssl\spider_排污许可\data\副本orc识别信息.csv")
detect()
