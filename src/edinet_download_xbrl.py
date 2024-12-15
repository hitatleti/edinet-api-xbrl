import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import datetime
from pathlib import Path
import pickle
import os
from dotenv import load_dotenv
import socket
import requests
from config import CFG
# import missingno as msno


EDINET_DIR = CFG.EDINET_DIR

env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

# これ以降、os.getenvで変数を取得可能
EDINET_URL = os.getenv("EDINET_URL")
EDINET_SUBSCRIPTION_KEY = os.getenv("EDINET_SUBSCRIPTION_KEY")


def last_day_of_month(year, month):
   # 翌月の1日から1日引いた日が, 当月月末
   if month == 12:
      return datetime.date(year, 12, 31)
   else:
      return datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)
  

def make_day_list(start_date, end_date):
    """
    start_dateからend_dateまでの日付のリストを返す
    """
    print("start_date: ", start_date)
    print("end_date: ", end_date)

    period = end_date - start_date
    period = int(period.days)
    day_list = []

    for d in range(period + 1):
        day = start_date + datetime.timedelta(days=d)
        day_list.append(day)

    return day_list


def make_doc_id_list(day_list):
  securities_report_doc_list = []
  for index, day in enumerate(day_list):
    url = f'{EDINET_URL}.json'
    params = {
        'date': day.strftime('%Y-%m-%d'),
        'type': 2,
        'Subscription-Key': EDINET_SUBSCRIPTION_KEY
    }

    res = requests.get(url, params=params, allow_redirects=False)
    json_data = res.json()
    print("day: ", day)

    if "results" in json_data:
      for num in range(len(json_data["results"])):
        ordinance_code = json_data["results"][num]["ordinanceCode"]
        form_code = json_data["results"][num]["formCode"]
        docInfoEditStatus = json_data["results"][num]["docInfoEditStatus"]

        if ordinance_code == "010" and form_code == "030000" and docInfoEditStatus != 2:
          print(json_data["results"][num]["filerName"], json_data["results"][num]["docDescription"],
                json_data["results"][num]["docID"])
          securities_report_doc_list.append(json_data["results"][num]["docID"])

  return securities_report_doc_list

def download_xbrl_in_zip(securities_report_doc_list, number_of_lists, year_month):

  # save directry
  save_dir = EDINET_DIR / "XBRL" / year_month
  if not os.path.exists(save_dir):
    os.makedirs(save_dir)

  for index, doc_id in enumerate(securities_report_doc_list):
    print(doc_id, ":", index + 1, "/", number_of_lists)
    url = f'{EDINET_URL}/{doc_id}'
    params = {
        "type": 1,
        "Subscription-Key": EDINET_SUBSCRIPTION_KEY
    }
    filename = os.path.join(save_dir, f"{doc_id}.zip")
    res = requests.get(url, params=params, stream=True, allow_redirects=False)
    
    try:
        if res.status_code == 200:
            with open(filename, "wb") as file:
                for chunk in res.iter_content(chunk_size=1024):
                    file.write(chunk)
        print(f"Downloaded and Saved: {filename}")
    except Exception as e:
        print(f"An error occurred: {e}")



def main():

  # 初期設定
  start_year = 2024
  start_month = 3
  end_year = 2024
  end_month = 11

  current_year = start_year
  current_month = start_month

  while (current_year < end_year) or (current_year == end_year and current_month <= end_month):
    start_date = datetime.date(current_year, current_month, 1)
    end_date = last_day_of_month(current_year, current_month)

    day_list = make_day_list(start_date, end_date)

    securities_report_doc_list = make_doc_id_list(day_list)
    number_of_lists = len(securities_report_doc_list)
    print("number_of_lists: ", number_of_lists)
    print("get_list: ", securities_report_doc_list)

    download_xbrl_in_zip(securities_report_doc_list, number_of_lists, start_date.strftime("%Y%m"))
    print("download finish")

    # 月を1つ進める
    if current_month == 12:
       current_year += 1
       current_month = 1
    else:
       current_month += 1
    
    

if __name__ == "__main__":
  main()

