from arelle import ModelManager
from arelle import Cntlr
import os
import glob
import zipfile
import shutil
import re
from bs4 import BeautifulSoup
import pandas as pd
from config import CFG

def make_edinet_info_list(edinetcodedlinfo_filepath):
    try:
        edinet_info = pd.read_csv(edinetcodedlinfo_filepath, skiprows=1, encoding='cp932')
        edinet_info = edinet_info[["ＥＤＩＮＥＴコード", "提出者業種"]]
        edinet_info_list = edinet_info.values.tolist()
        return edinet_info_list
    except Exception as e:
        print("Failed loading EDINET info")
        return []

def make_edinet_company_info_list(xbrl_files, edinet_info_list):
    edinet_company_info_list = []
    for index, xbrl_file in enumerate(xbrl_files):
        company_data = {
            "EDINETCODE": None,
            "企業名": None,
            "seccode": None,
            "業種": None,
            "発行済株式総数": None,
            # "営業利益（IFRS）": None,
            # "事業等のリスク": None,
        }

        try:
            ctrl = Cntlr.Cntlr()
            model_manager = ModelManager.initialize(ctrl)
            model_xbrl = model_manager.load(xbrl_file)
            print("loading XBRL file: ", index + 1, "/", len(xbrl_files))
        except Exception as e:
            print(f"Failed loaing XBRL files. ({xbrl_file}): {e}")
            edinet_company_info_list.append(list(company_data.values()))
            continue

        try:
            for fact in model_xbrl.facts:
            # Search EDINET code
                if fact.concept.qname.localName == "EDINETCodeDEI":
                    company_data["EDINETCODE"] = fact.value
                    # Setting SECTOR based on EDINETCODE
                    for code_name in edinet_info_list:
                        if code_name[0] == company_data["EDINETCODE"]:
                            company_data["業種"] = code_name[1]
                            break
                # Search ConmpanyName
                elif fact.concept.qname.localName == "FilerNameInJapaneseDEI":
                    company_data["企業名"] = fact.value
                
                # Search Securities Code
                elif fact.concept.qname.localName == "SecurityCodeDEI":
                        company_data["seccode"] = fact.value

                # 発行済株式総数を探す
                elif fact.concept.qname.localName == "NumberOfIssuedSharesAsOfFilingDateIssuedSharesTotalNumberOfSharesEtc":
                    if fact.contextID =="FilingDateInstant":
                        issued_shares = fact.value
                        company_data["発行済株式総数"] = fact.value
                elif issued_shares is None:
                    if fact.concept.qname.localName == "TotalNumberOfIssuedSharesSummaryOfBusinessResults":
                        if fact.contextID == "CurrentInstant":
                            company_data["発行済株式総数"] = fact.value


                # # 営業利益（IFRS）を探す
                # elif fact.concept.qname.localName == "OperatingProfitLossIFRS":
                #     if fact.contextID == "CurrentYearDuration":
                #         company_data["営業利益（IFRS）"] = fact.value

                # # 事業等のリスクを探す
                # elif fact.concept.qname.localName == "BusinessRisksTextBlock":
                #     if fact.contextID == "FilingDateInstant":
                #         raw_risk = fact.value
                #         # Eliminate HTML-Tag by using BeautifulSoup
                #         soup = BeautifulSoup(raw_risk, "html.parser")
                #         company_data["事業等のリスク"] = re.sub(r'\s', '', soup.get_text()).strip()

        except Exception as e:
            print(f"An Error occurs in processing. ({xbrl_file}): {e}")
        
        # add to list
        edinet_company_info_list.append(list(company_data.values()))

    return edinet_company_info_list


def write_csv(edinet_company_info_list):
    try:
        xbrl_frame = pd.DataFrame(edinet_company_info_list,
                                  columns=['EDINETCODE',
                                           '企業名',
                                           "seccode",
                                           "業種",
                                           "発行済株式総数",
                                        #    "営業利益（IFRS）",
                                        #    '事業等のリスク',
                                           ])
        # Sorted by EDINETCODE
        xbrl_frame_sorted = xbrl_frame.sort_values(by="EDINETCODE", ascending=True)
        # output csv file
        output_path = CFG.DATA_ROOT / "issuedshares-data" / "xbrl_book.csv"
        xbrl_frame_sorted.to_csv(output_path, encoding="utf-8-sig", index=False)

    except Exception as e:
        print("An Error occurs in writing CSV.")


def main():
    # Add EDINETCODE list
    edinetcodedlinfo_filepath = CFG.DATA_ROOT / "EdinetcodeDlInfo.csv"
    edinet_info_list = make_edinet_info_list(edinetcodedlinfo_filepath)
    
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

    edinet_company_info_list = make_edinet_company_info_list(xbrl_files, edinet_info_list)
    
    # output csv file to inputs directry
    write_csv(edinet_company_info_list)

    print("extract finish")

    for d in extracted_dirs:
        # 処理完了後、解凍先フォルダを削除
        shutil.rmtree(d)
        # print(f"Deleted temporary folder: {d}")


if __name__ == "__main__":
    main()