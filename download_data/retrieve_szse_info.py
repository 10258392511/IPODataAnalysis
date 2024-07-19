import numpy as np
import pandas as pd
import re
import time
import os

from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait

from ..global_configs import ROOT_DIR
from IPODataAnalysis.configs import CHROME_EXECUTABLE_PATH


def retrieve_element(url: str, css_selector: str):
    driver = webdriver.Chrome(service=ChromeService(executable_path=CHROME_EXECUTABLE_PATH))
    driver.get(url)
    ele = driver.find_element(By.CSS_SELECTOR, css_selector)

    return ele


def is_table_ready(driver):
    div_total_pages = driver.find_element(By.CSS_SELECTOR, "div.current-page")

    return len(div_total_pages.text) > 0


def retrieve_table(html_ele: WebElement, if_retrieve_link=True):
    table_ele = html_ele.find_element(By.CSS_SELECTOR, "table.reg-table")
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
            time.sleep(0.1)
        table_df = retrieve_table(driver)
        table_dfs.append(table_df)

    table_df_out = pd.concat(table_dfs, axis=0)

    if save_dir is not None:
        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)
        table_df_out.to_csv(os.path.join(save_dir, "index_page.csv"), index=False, encoding="utf_8_sig")

    return table_df_out
