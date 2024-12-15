import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import datetime
from pathlib import Path
import pickle
import socket
from arelle import ModelManager
from arelle import Cntlr
import os
import glob
import zipfile
import shutil

from config import CFG

def make_edinet_company_info_list(xbrl_files):
    edinet_company_info_list = []
    for index, xbrl_file in enumerate(xbrl_files):
        company_data = {
            "EDINETCODE": "",
            "企業名": "",
            "営業利益（IFRS）": "",
        }
        ctrl = Cntlr.Cntlr()
        model_manager = ModelManager.initialize(ctrl)
        model_xbrl = model_manager.load(xbrl_file)

        print("loading XBRL file:", index + 1, "/", len(xbrl_files))

        for fact in model_xbrl.facts:
            # Search EDINET code
            if fact.concept.qname.localName == "EDINETCodeDEI":
                company_data["EDINETCODE"] = fact.value
            # Search company name
            elif fact.concept.qname.localName == "FilerNameInJapaneseDEI":
                company_data["企業名"] = fact.value
            # 営業利益（IFRS）を探す
            elif fact.concept.qname.localName == "OperatingProfitLossIFRS":
                if fact.contextID == "CurrentYearDuration" and company_data["営業利益（IFRS）"] == "":
                    company_data["営業利益（IFRS）"] = fact.value
        # 見つけたデータをリストに入れる
        edinet_company_info_list.append([company_data["EDINETCODE"],
                                        company_data["企業名"],
                                        company_data["営業利益（IFRS）"]])

    return edinet_company_info_list

def main():
    xbrl_files = []
    extracted_dirs = []
    zip_dir = CFG.EDINET_DIR / "XBRL"
    zip_files = glob.glob(os.path.join(zip_dir, "*.zip"))
    for zip_file_path in zip_files:
        base_name = os.path.splitext(os.path.basename(zip_file_path))[0]
        extract_dir = os.path.join(zip_dir, base_name)

        # 解凍先フォルダが存在しない場合は作成
        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir)

        # ZIPファイル解凍
        with zipfile.ZipFile(zip_file_path, 'r') as zf:
            zf.extractall(extract_dir)
        
        # 解凍フォルダ内からXBRLファイルを取得
        xbrl_file_list = glob.glob(os.path.join(extract_dir, 'XBRL', 'PublicDoc', '*.xbrl'))
        if xbrl_file_list:
            xbrl_files.append(xbrl_file_list[0])
        extracted_dirs.append(extract_dir)

    company_info = make_edinet_company_info_list(xbrl_files)
    for info in company_info:
        print(info)

    print("extract finish")

    for d in extracted_dirs:
        # 処理完了後、解凍先フォルダを削除
        shutil.rmtree(d)
        print(f"Deleted temporary folder: {d}")


if __name__ == "__main__":
    main()