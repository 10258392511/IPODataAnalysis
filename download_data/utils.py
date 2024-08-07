import requests
import os

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService

from ..global_configs import ROOT_DIR
from IPODataAnalysis.configs import CHROME_EXECUTABLE_PATH


def init_driver(url: str):
    driver = webdriver.Chrome(service=ChromeService(executable_path=CHROME_EXECUTABLE_PATH))
    driver.get(url)

    return driver


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


def download_and_save_file(url, save_filename: str = None):
    if os.path.isfile(save_filename):
       return
    resp = requests.get(url)
    if resp.status_code != 200:
        raise requests.HTTPError
    if save_filename is not None:
        save_dir = os.path.dirname(save_filename)
        if not os.path.isdir(save_dir):
            os.makedirs(save_dir)
        with open(save_filename, "wb") as wf:
            wf.write(resp.content)
