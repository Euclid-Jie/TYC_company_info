import pandas as pd
from tianyancha.client import TycClient
import warnings
import requests
import json
from Utils.MongoClient import MongoClient
import time
from tqdm import tqdm
import numpy as np
from retrying import retry
import threading

warnings.filterwarnings("ignore")

# proxies = {
#     "http": "http://127.0.0.1:12345",
#     "https": "http://127.0.0.1:12345",
# }

proxies = None


def get_base_info(key_word: str):
    companies = pd.DataFrame(TycClient().search(key_word).src)
    companies["name"] = companies["name"].apply(
        lambda x: x.replace("<em>", "").replace("</em>", "")
    )
    return companies[["id", "name"]]


def _get_data_list(
    company_id: str,
    page_size=10,
    page_num=1,
) -> tuple[int, dict]:
    base_url = f"https://capi.tianyancha.com/cloud-business-state/certificate/list?_={int(time.time()*1000)}&graphId={company_id}&pageSize={page_size}&pageNum={page_num}&type="
    header = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Host": "capi.tianyancha.com",
        "Version": "TYC-Web",
        "X-Auth-Token": "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxMzI4MTEwNjM4NSIsImlhdCI6MTcwOTk3NjIwOSwiZXhwIjoxNzEyNTY4MjA5fQ.nmaR2x9Kts7Axw0Bg-GjFJF3bQ2-Nh5QDwJ5hqPqC9L0toD4p58zv7mCo3wGl9BXhVYK5koZkN0DEPI0pnVhwA",
    }
    res = requests.get(base_url, headers=header, proxies=proxies)
    data = json.loads(res.content.decode("utf-8"))["data"]
    count = data["count"]
    if count == 0:
        return count, []
    else:
        return count, [
            i for i in data["resultList"] if "管理体系认证" in i["certificateName"]
        ]


def get_data_list(
    company_id: str,
    page_size=100,
    page_num=1,
) -> dict:
    all_data_list = []
    count, data_list = _get_data_list(company_id, page_size, page_num)
    all_data_list.extend(data_list)
    if count > page_size:
        # for page_i in range(2, count // page_size + 2):
        #     _, data_list = _get_data_list(company_id, page_size, page_i)
        #     all_data_list.extend(data_list)
        print(f"{company_id} has {count} records")
    return count, all_data_list


@retry(stop_max_attempt_number=3)
def get_detail(id: str):
    AUTHORIZATION = "0###TYC_NODE_SERVER_88888888_88888888###1711716499650"
    X_AUTH_TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxMzI4MTEwNjM4NSIsImlhdCI6MTcwOTk3NjIwOSwiZXhwIjoxNzEyNTY4MjA5fQ.nmaR2x9Kts7Axw0Bg-GjFJF3bQ2-Nh5QDwJ5hqPqC9L0toD4p58zv7mCo3wGl9BXhVYK5koZkN0DEPI0pnVhwA"
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        # "Authorization": AUTHORIZATION,
        # "x-auth-token": X_AUTH_TOKEN,
        # "Connection": "keep-alive",
        # "Accept": "application/json, text/plain, */*",
        # "Accept-Encoding": "gzip, deflate, br",
        # "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5",
        # "Content-Type": "application/json",
        # "Host": "napi-huawei.tianyancha.com",
        # "Origin": "https://www.tianyancha.com",
        # "Referer": "https://www.tianyancha.com/",
        # "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Microsoft Edge";v="122"',
        # "Sec-Ch-Ua-Mobile": "?0",
        # "Sec-Ch-Ua-Platform": "Windows",
        # "Sec-Fetch-Dest": "empty",
        # "Sec-Fetch-Mode": "cors",
        # "Sec-Fetch-Site": "same-site",
        "Version": "TYC-Web",
        # "X-Tycid": "cd728fe0ddf411eeb270bfb0c7eda9da",
    }
    response = requests.get(
        f"https://napi-huawei.tianyancha.com/services/v3/expanse/certificateDetail?_={int(time.time()*1000)}&id={id}",
        headers=header,
        proxies=proxies,
    )
    data = json.loads(response.text)["data"]
    data_dict = {item["title"]: item["content"] for item in data["detail"]}
    return data_dict


def main_run():
    raw_data_col = MongoClient("supply", "四川-天眼查待匹配")
    data_col = MongoClient("supply", "四川-天眼查-资质结果")
    random_doc = raw_data_col.aggregate([{"$sample": {"size": 1}}])
    for company in random_doc:
        key_word = company["company"]
        if "dealed" in company:
            if company["dealed"] == 1:
                continue
            else:
                company_info = get_base_info(key_word)
                count, data_list = get_data_list(company_info["id"].values[0])
                with tqdm(data_list) as pbar:
                    pbar.set_description(f"{company_info['name'].values[0]}")
                    for data in pbar:
                        data.update(
                            {
                                "raw_company_name": key_word,
                                "company_name": company_info["name"].values[0],
                                "company_id": company_info["id"].values[0],
                                "all_count": count,
                                "data_len": len(data_list),
                            }
                        )
                        detail = get_detail(data["id"])
                        data.update(detail)
                        for key in data:
                            if isinstance(data[key], np.int64):
                                data[key] = data[key].item()
                        data_col.insert_one(data)
                raw_data_col.update_one(
                    {"_id": company["_id"]}, {"$set": {"dealed": 1}}
                )
        else:
            company_info = get_base_info(key_word)
            count, data_list = get_data_list(company_info["id"].values[0])
            with tqdm(data_list) as pbar:
                pbar.set_description(f"{company_info['name'].values[0]}")
                for data in pbar:
                    data.update(
                        {
                            "raw_company_name": key_word,
                            "company_name": company_info["name"].values[0],
                            "company_id": company_info["id"].values[0],
                            "all_count": count,
                            "data_len": len(data_list),
                        }
                    )
                    detail = get_detail(data["id"])
                    data.update(detail)
                    for key in data:
                        if isinstance(data[key], np.int64):
                            data[key] = data[key].item()
                    data_col.insert_one(data)
            raw_data_col.update_one({"_id": company["_id"]}, {"$set": {"dealed": 1}})


if __name__ == "__main__":
    raw_data_col = MongoClient("supply", "四川-天眼查待匹配")

    def worker():
        while True:
            try:
                main_run()
            except Exception as e:
                print(e)
                time.sleep(3)
                continue

    # 创建多个线程
    num_threads = 4
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    # 等待所有线程完成
    for t in threads:
        t.join()
