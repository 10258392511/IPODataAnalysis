import numpy as np
import pandas as pd
import fitz
import re
import os
import glob

from .extract_info import extract_content, extract_q_and_a
from ..utils import create_logger
from tqdm import tqdm
from typing import List


def create_schema(q_filename: str, a_filename: str):
    if not os.path.isfile(q_filename):
        cols = [
            "website",
            "comp",
            "filename",
            "round_number",
            "question_num",
            "question",
            "question_long",
            "page_from",
            "page_to",
        ]
        q_df = pd.DataFrame(columns=cols)
        q_dirname = os.path.dirname(q_filename)
        if not os.path.isdir(q_dirname):
            os.makedirs(q_dirname)
        q_df.to_csv(q_filename, index=False, encoding="utf_8_sig")

    if not os.path.isfile(a_filename):
        cols = [
            "website",
            "comp",
            "round_number",
            "question_num",
            "answer_entry_num",
            "page",
            "subtitle",
        ]
        a_df = pd.DataFrame(columns=cols)
        a_dirname = os.path.dirname(a_filename)
        if not os.path.isdir(a_dirname):
            os.makedirs(a_dirname)
        a_df.to_csv(a_filename, index=False, encoding="utf_8_sig")


def insert_q_and_a_entries(q_and_a_entries: List[dict], meta_info: dict, q_filename: str, a_filename: str):
    """
    Given the output of .extract_info.extract_q_and_a(.), insert it to the DB.
    The output(q_and_a_entries) is in the form of:
    [
        {
            "question": str,
            "pages": (from, to),
            "question_long": str,
            "ans_collection": [
                {
                    "page": int,
                    "subtitle": str,
                }...
            ]
        }...
    ]
    meta_info: dict
        {
            "website": str(e.g. szse),
            "comp": str(company's short name),
            "filename": str,
            "round_number": int,
        }
    """
    q_df = pd.read_csv(q_filename)
    a_df = pd.read_csv(a_filename)
    new_q_entries = []
    new_a_entries = []

    for i, q_and_a_iter in enumerate(q_and_a_entries):
        new_q_entry = meta_info.copy()
        new_q_entry.update({
            "question_num": i,
            "question": q_and_a_iter["question"],
            "question_long": q_and_a_iter["question_long"],
            "page_from": q_and_a_iter["pages"][0],
            "page_to": q_and_a_iter["pages"][1],
        })
        new_q_entries.append(new_q_entry)

        for j, a_entry_iter in enumerate(q_and_a_iter["ans_collection"]):
            new_a_entry = meta_info.copy()
            new_a_entry.pop("filename")
            new_a_entry.update({
                "question_num": i,
                "answer_entry_num": j,
                "page": a_entry_iter["page"],
                "subtitle": a_entry_iter["subtitle"],
            })
            new_a_entries.append(new_a_entry)

    new_q_df = pd.DataFrame(new_q_entries)
    new_a_df = pd.DataFrame(new_a_entries)
    q_df = pd.concat([q_df, new_q_df], axis=0).drop_duplicates()
    a_df = pd.concat([a_df, new_a_df], axis=0).drop_duplicates()
    q_df.to_csv(q_filename, index=False, encoding="utf_8_sig")
    a_df.to_csv(a_filename, index=False, encoding="utf_8_sig")


def __remove_white_space(text: str):
    pattern = re.compile(r"\s+")
    text_out = re.sub(pattern, "", text)

    return text_out


def query_one_q_and_a(website: str, comp: str, round_number: int, question_num: int, q_filename: str,
                      a_filename: str) -> dict:
    """
    Returns
    -------
    {
        "question": str,
        "question_long": str,
        "pages": (from, to),
        "answer": str (Each subtitle starts a new line),
    }
    """
    out_dict = {}
    q_df = pd.read_csv(q_filename)
    a_df = pd.read_csv(a_filename)
    q_mask = (q_df["website"] == website) & (q_df["comp"] == comp) & (q_df["round_number"] == round_number) \
             & (q_df["question_num"] == question_num)
    q_entry = q_df[q_mask].iloc[0]
    out_dict["question"] = q_entry["question"]
    out_dict["question_long"] = q_entry["question_long"]
    out_dict["pages"] = (q_entry["page_from"], q_entry["page_to"])
    a_mask = (a_df["website"] == website) & (a_df["comp"] == comp) & (a_df["round_number"] == round_number) \
             & (a_df["question_num"] == question_num)
    a_entries = a_df[a_mask].sort_values("answer_entry_num")

    a_str = "\n\n".join(a_entries["subtitle"].apply(__remove_white_space))
    out_dict["answer"] = a_str

    return out_dict


def __process_one_file(filename: str, q_filename: str, a_filename: str):
    round_pattern = re.compile(r"第[一二三四五六七八九十]+")
    comp_name_dirname = os.path.dirname(filename)
    comp_name = os.path.basename(comp_name_dirname)
    website_dir_name = os.path.dirname(comp_name_dirname)
    website = os.path.basename(website_dir_name)
    round_pattern_matches = re.findall(round_pattern, filename)
    round_number = 2
    if len(round_pattern_matches) == 0 or "第一" in round_pattern_matches[0]:
        round_number = 1
    meta_info = {
        "website": website,
        "comp": comp_name,
        "filename": filename,
        "round_number": round_number,
    }

    doc = fitz.open(filename)
    content_res = extract_content(doc)
    res = extract_q_and_a(doc, content_res)
    insert_q_and_a_entries(res, meta_info, q_filename, a_filename)


def construct_q_and_a_database_main(root_dir: str, log_filename: str, q_filename: str, a_filename: str):
    """
    root_dir: e.g. F:\Data\IPODataAnalysis\ipo_doc, i.e. parent directory of e.g. */szse/
    File system:
    $root_dir
        - szse
            - comp1
                - *.pdf
    """
    logger = create_logger("q_and_a_db", log_filename)
    create_schema(q_filename, a_filename)
    filenames = glob.glob(os.path.join(root_dir, "*/*/*.pdf"))
    for filename in tqdm(filenames):
        try:
            __process_one_file(filename, q_filename, a_filename)
        except Exception as e:
            logger.debug(f"{filename}: {e}")
