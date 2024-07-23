import numpy as np
import pandas as pd
import requests
import re
import datetime as dt
import time
import os

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from collections import defaultdict

from ..global_configs import ROOT_DIR
from IPODataAnalysis.configs import CHROME_EXECUTABLE_PATH


def retrieve_element(url: str, css_selector: str):
    driver = webdriver.Chrome(service=ChromeService(executable_path=CHROME_EXECUTABLE_PATH))
    driver.get(url)
    ele = driver.find_element(By.CSS_SELECTOR, css_selector)

    return ele


def retrieve_page(url: str) -> BeautifulSoup:
    resp = requests.get(url)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.content, "html.parser")
        return soup
    else:
        raise requests.HTTPError


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
    TODO: Handle:
    - No table
    - No link in the row
    - Can't find first and / or second round inquiry letter
    """
    div_ele = driver.find_element(By.XPATH, "//div[contains(text(), '问询与回复')]/following-sibling::div[1]")
    table_ele: WebElement = div_ele.find_element(By.CSS_SELECTOR, "table.info-disc-table")
    data_df = pd.read_html(table_ele.get_attribute("outerHTML"))[0]

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

    return first_round_df, second_round_df
