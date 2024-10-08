import numpy as np
import pandas as pd
import requests
import re
import datetime as dt
import logging
import time
import os

from multiprocessing import Pool, Manager
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from collections import defaultdict

from ..global_configs import ROOT_DIR
from ..utils import make_directories
from IPODataAnalysis.configs import CHROME_EXECUTABLE_PATH
from .utils import download_and_save_file, init_driver


##### Index Page (e.g. IPO) #####
def is_table_ready(driver):
    div_total_pages = driver.find_element(By.CSS_SELECTOR, "div.current-page")

    return len(div_total_pages.text) > 0


def retrieve_table(html_ele: WebElement, if_retrieve_link=True):
    table_ele = html_ele.find_element(By.CSS_SELECTOR, "table.reg-table")
    time.sleep(0.5)  # Prevent Stale Element Reference Exception
    table_html = table_ele.get_attribute("outerHTML")
    table_df = pd.read_html(table_html)[0]

    def find_link(comp_name: str):
        xpath = f"//a[contains(text(), '{comp_name}')]"
        anchor_ele = table_ele.find_element(By.XPATH, xpath)
        link = anchor_ele.get_attribute("href")

        return link

    if if_retrieve_link:
        table_df["detail_page"] = table_df["发行人全称"].apply(find_link)

    return table_df


def retrieve_index_table(index_begin_url: str, wait_ready=30, save_dir=None):
    driver = webdriver.Chrome(service=ChromeService(executable_path=CHROME_EXECUTABLE_PATH))
    driver.get(index_begin_url)
    # WebDriverWait(driver, wait_ready).until(
    #     lambda driver: driver.execute_script("return document.readyState") == "complete"
    # )
    WebDriverWait(driver, wait_ready).until(is_table_ready)
    div_total_pages = driver.find_element(By.CSS_SELECTOR, "div.current-page")
    total_page_pattern = r"共[0-9]+页"
    matches = re.findall(total_page_pattern, div_total_pages.text)
    num_total_pages = int(matches[0][1:-1])

    table_dfs = [retrieve_table(driver)]
    for page_idx in range(num_total_pages - 1):
        next_button = driver.find_element(By.CSS_SELECTOR, "li.next a")
        next_button.click()
        table_df = retrieve_table(driver)
        last_table_df = table_dfs[-1]
        while table_df.iloc[0, 0] == last_table_df.iloc[0, 0]:
            table_df = retrieve_table(driver, if_retrieve_link=False)
            # time.sleep(0.1)
        table_df = retrieve_table(driver)
        table_dfs.append(table_df)

    table_df_out = pd.concat(table_dfs, axis=0)

    if save_dir is not None:
        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)
        table_df_out.to_csv(os.path.join(save_dir, "index_page.csv"), index=False, encoding="utf_8_sig")

    return table_df_out

#################################

##### Detail Page #####
def is_page_ready(driver):
    try:
        div_title: WebElement = driver.find_element(By.CSS_SELECTOR, "div.project-title")
        if len(div_title.text) > 0:
            return True
        return False
    except NoSuchElementException:
        return False


def extract_timeline(driver):
    data_dict = defaultdict(list)
    ul_ele: WebElement = driver.find_element(By.CSS_SELECTOR, "ul.project-dy-flow-con")
    all_li_ele = ul_ele.find_elements(By.CSS_SELECTOR, "li")
    for li_ele in all_li_ele:
        title_iter = li_ele.find_element(By.CSS_SELECTOR, "span.title").text
        date_iter = pd.to_datetime(li_ele.find_element(By.CSS_SELECTOR, "span.date").text)
        data_dict[title_iter].append(date_iter)

    data_df = pd.DataFrame(data_dict)

    return data_df


def extract_project_info(driver):
    data_dict = defaultdict(list)
    table_ele = driver.find_element(By.CSS_SELECTOR, "div.base-info.project-base-info")
    table_rows = table_ele.find_elements(By.CSS_SELECTOR, "tr")
    for table_row in table_rows:
        index_ele_all = table_row.find_elements(By.CSS_SELECTOR, "td.title")
        info_ele_all = table_row.find_elements(By.CSS_SELECTOR, "td.info")
        for index_ele, info_ele in zip(index_ele_all, info_ele_all):
            data_dict[index_ele.text].append(info_ele.text)

    data_df = pd.DataFrame(data_dict)

    return data_df


def extract_inquiries_and_replies(driver):
    """
    Handles:
    - No table (Done)
    - No link in the row, i.e a <span> instead of an <a>
    - Can't find first and / or second round inquiry letter

    Returns
    -------
    dict:
        filename: url
    """
    div_ele = driver.find_element(By.XPATH, "//div[contains(text(), '问询与回复')]/following-sibling::div[1]")
    table_ele: WebElement = div_ele.find_element(By.CSS_SELECTOR, "table.info-disc-table")
    data_df_all = pd.read_html(table_ele.get_attribute("outerHTML"))
    if len(data_df_all) == 0:
        return {}
    data_df = data_df_all[0]

    def find_broker_rows(title: str, key_word: str = None):
        """
        key_word: e.g. first round or second round
        """
        name_pattern = re.compile(r"[\u4e00-\u9fff]{2}函")
        if "发行人" in title and "保荐机构" in title and "回复" in title and ".pdf" in title:
            name_matches = re.findall(name_pattern, title)
            if len(name_matches) > 0 and name_matches[0] != "问询函":
                return False
            if key_word is None:
                return True
            if key_word in title:
                return True

        return False

    broker_mask = data_df["内容"].apply(find_broker_rows)
    broker_df = data_df[broker_mask]
    second_round_mask = broker_df["内容"].str.contains("第二轮")
    second_round_df = broker_df[second_round_mask].sort_values("更新日期", ascending=False)
    first_round_df = broker_df[~second_round_mask].sort_values("更新日期", ascending=False)

    out_dict = {}
    for df_iter in [first_round_df, second_round_df]:
        if len(df_iter) == 0:
            continue
        title_iter = df_iter["内容"].iloc[0]
        try:
            anchor_ele: WebElement = driver.find_element(By.XPATH, f"//a[contains(text(), '{title_iter}')]")
            out_dict[title_iter] = anchor_ele.get_attribute("href")
        except NoSuchElementException:
            out_dict[title_iter] = None

    return out_dict


def retrieve_detail_page(page_url: str, save_dir: str, wait_ready=30):
    """
    - extract_timeline(.)
    - extract_project_info(.)
    - extract_inquieies_and_replies(.): Download the pdfs

    Returns
    -------
    DataFrame: one row containing timeline and project info
    """
    driver = webdriver.Chrome(service=ChromeService(executable_path=CHROME_EXECUTABLE_PATH))
    driver.get(page_url)
    WebDriverWait(driver, wait_ready).until(is_page_ready)
    timeline_df = extract_timeline(driver)
    project_info_df = extract_project_info(driver)
    df_all = pd.concat([timeline_df, project_info_df], axis=1)
    url_dict = extract_inquiries_and_replies(driver)
    comp_name = df_all["公司简称"].iloc[0]
    save_dir_company = os.path.join(save_dir, comp_name)
    for filename, url in url_dict.items():
        filename_save = os.path.join(save_dir_company, filename)
        download_and_save_file(url, filename_save)

    return df_all


def __wrapper_retrieve_detail_page(page_url: str, save_dir: str, wait_ready: int, print_interval: int,
                                   total_num_urls: int, shared_list: list, logger: logging.Logger):
    try:
        df_all = retrieve_detail_page(page_url, save_dir, wait_ready)
        shared_list.append(df_all)
        if len(shared_list) % print_interval == 1:
            logger.debug(f"Current: {len(shared_list)}/{total_num_urls}")
    except Exception as e:
        logger.debug(e)


def retrieve_all_detail_pages(index_page_filename: str, save_dir: str, logger: logging.Logger, output_dir: str = None,
                              num_processes=8, **kwargs):
    """
    save_dir: Root directory for saving pdfs
    output_dir: Directory for saving the combined DF
    """
    wait_ready = kwargs.get("wait_ready", 30)
    print_interval = kwargs.get("print_interval", 50)

    index_page_df: pd.DataFrame = pd.read_csv(index_page_filename, header=[0])
    # index_page_df = index_page_df.loc[:10, :]
    detail_page_urls = list(index_page_df["detail_page"])

    with Manager() as manager:
        shared_list = manager.list()
        args_all = [(url_iter, save_dir, wait_ready, print_interval, len(detail_page_urls), shared_list, logger)
                    for url_iter in detail_page_urls]
        with Pool(processes=num_processes) as pool:
            pool.starmap(__wrapper_retrieve_detail_page, args_all)
        detail_all_df = pd.concat(shared_list, axis=0)

    combined_df = index_page_df.merge(detail_all_df, how="inner", left_on="发行人全称", right_on="公司全称")

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    combined_df.to_csv(os.path.join(output_dir, "detailed_info.csv"), index=False, encoding="utf_8_sig")
    logger.debug("Finished!")


def retrieve_latest_prospectus(driver: webdriver.Chrome, company_dir: str):
    div_ele = driver.find_element(By.XPATH, "//div[contains(text(), '信息披露')]/following-sibling::div[1]")
    tgt_td = div_ele.find_element(By.XPATH, "//td[contains(text(), '招股说明书')]/following-sibling::td[1]")
    all_anchors = tgt_td.find_elements(By.CSS_SELECTOR, "a")
    all_anchors = [anchor for anchor in all_anchors if anchor.get_attribute("href") is not None]
    all_anchors.sort(key=lambda anchor: pd.to_datetime(anchor.text), reverse=True)
    tgt_anchor = all_anchors[0]
    file_url = tgt_anchor.get_attribute("href")
    download_and_save_file(file_url, os.path.join(company_dir, f"招股说明书_{tgt_anchor.text}.pdf"))


def __wrap_retrieve_latest_prospectus(url: str, company_dir: str, wait_ready=30):
    try:
        driver = init_driver(url)
        WebDriverWait(driver, wait_ready).until(is_page_ready)
        retrieve_latest_prospectus(driver, company_dir)
    except Exception as e:
        pass


def retrieve_all_prospectuses(detail_info_filename: str, save_dir: str, num_processes=8, **kwargs):
    wait_ready = kwargs.get("wait_ready", 30)
    detail_info_df: pd.DataFrame = pd.read_csv(detail_info_filename, header=[0])
    comp_names = detail_info_df["公司简称"].tolist()
    detail_urls = detail_info_df["detail_page"].tolist()

    with Pool(processes=num_processes) as pool:
        args_all = [(url_iter, os.path.join(save_dir, comp_name_iter), wait_ready) for url_iter, comp_name_iter in
                    zip(detail_urls, comp_names)]
        pool.starmap(__wrap_retrieve_latest_prospectus, args_all)
