from spide.units.nuit import getHeader, xunfei_orc, turn_to_list
import pandas as pd
import os

path = "F:\PL\ssl\spider_排污许可"


# 遍历文件夹，修改下载状态
def detect():
    header = getHeader()
    download_list = pd.DataFrame(columns=["path", "status", "第五页信息", "第六页信息"])
    download_list.loc[0] = ["path", "status", "第五页信息", "第六页信息"]
    xxgk = pd.read_csv(r"F:\PL\ssl\spide_template\data\许可信息公开.csv", index_col=0)
    for i in xxgk.index:
        if xxgk.loc[i, "识别状态"] != 2:
            try:
                path = f"F:/PL/ssl/spider_排污许可/许可信息公开/{xxgk.loc[i, '行业类别']}/{xxgk.loc[i, '单位名称']}{xxgk.loc[i, '许可证编号']}/许可证副本"
                if os.path.exists(path + "/5.png"):
                    if not os.path.getsize(path + "/5.png") == 520:
                        content5 = turn_to_list(xunfei_orc(path + "/5.png", header))
                        # content6 = turn_to_list(xunfei_orc(path + "/6.png",header))
                        download_list.loc[download_list.index[-1] + 1] = [path, 0, content5, ""]
                        download_list.to_csv(r"F:\PL\ssl\spide_template\data\副本orc识别信息.csv")
                        xxgk.loc[i, "识别状态"] = 2
                    else:
                        # 需要重新下载
                        xxgk.loc[i, "识别状态"] = 3
                xxgk.to_csv("F:\PL\ssl\spide_template\data\许可信息公开.csv")
            except Exception as e:
                print(e)
detect()
