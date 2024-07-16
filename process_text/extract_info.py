import fitz
import sys
import re

from ..global_configs import ROOT_DIR
from IPODataAnalysis.configs import PATTERNS


def extract_content(doc: fitz.Document):
    """
    output:
    {
        "question": str,
        "link": {
            "kind": 1,
            "page": int,
        }
    }
    """
    content_entry_pattern = re.compile(PATTERNS["content_entry"])
    content_pages = []
    has_found_content = False
    for page_id in range(len(doc)):
        page = doc.load_page(page_id)
        matches = re.findall(content_entry_pattern, page.get_text())
        if len(matches) == 0 and has_found_content:
            break
        if len(matches) > 0:
            content_pages.append(page)
            has_found_content = True


    # print(page_id)
    # print(content_pages)
    res = []
    for page in content_pages:
        matches = re.findall(content_entry_pattern, page.get_text())
        links = page.get_links()
        for match, link in zip(matches, links):
            match = re.sub(r"[\n\.]", "", match)
            match = match.strip()
            link_kind = link.get("kind", -1)
            if link_kind == -1:
                continue
            res.append({
                "question": match,
                "link": {
                    "kind": link.get("kind", -1),
                    "page": link.get("page", -1),
                }
            })

    return res


def extract_q_and_a(doc: fitz.Document, content_res: list):
    """
    content_res is output of extract_content(.)
    """
    pass


def process_ans(doc: fitz.Document, start_page: int, end_page: int, reply_str: str, buffer=100):
    """
    buffer: heuristic to include multiline subtitle

    Returns
    -------
    [
        {
            "page": int,
            "subtitle": str,
        }...
    ]
    """
    subtitle_pattern = re.compile(PATTERNS["subtitle"])
    res = []

    for i, page_idx in enumerate(range(start_page, end_page + 1)):
        page_str = doc.load_page(page_idx).get_text()
        if i == 0:
            sep_idx = page_str.find(reply_str)
            page_str = page_str[sep_idx + len(reply_str):]
        matches = re.findall(subtitle_pattern, page_str)
        for match in matches:
            sep_idx = page_str.find(match)
            res.append({
                "page": page_idx,
                "subtitle": page_str[sep_idx:sep_idx + buffer].strip(),
            })

    return res


def process_q_and_a(doc: fitz.Document, start_page: int, end_page: int):
    """
    Returns
    -------
    {
        "question_long": str,
        "ans_collection": list[dict] (output of process_ans(.)),
    }
    """
    # Find "回复：" pattern
    reply_pattern = re.compile(PATTERNS["reply"])
    reply_page_idx = -1
    reply_str = None
    for page_idx in range(start_page, end_page + 1):
        page = doc.load_page(page_idx)
        page_text = page.get_text()
        matches = re.findall(reply_pattern, page_text)
        if len(matches) > 0:
            reply_page_idx = page_idx
            reply_str = matches[0]
            break
    # print(repr(reply_str))
    if reply_page_idx == -1:
        raise IndexError("Cannot find '回复：' pattern!")

    res = {}
    # Store the question
    q_str = ""
    for page_idx in range(start_page, reply_page_idx):
        page = doc.load_page(page_idx)
        q_str += page.get_text()
    page = doc.load_page(page_idx)
    page_str = page.get_text()
    sep_idx = page_str.find(reply_str)
    q_str += page_str[:sep_idx]
    res["question_long"] = q_str

    # Store the reply
    # Ignore the last page since there's no sufficient content to make a substantial subsection
    # in order to prevent overlap with the next question
    ans_list = process_ans(doc, reply_page_idx, end_page - 1, reply_str)
    res["ans_collection"] = ans_list

    return res


# def extract_bold_text_from_pdf(pdf_path):
#     doc = fitz.open(pdf_path)
#     bold_text = []
#
#     for page_num in range(len(doc)):
#         page = doc.load_page(page_num)
#         blocks = page.get_text("dict")["blocks"]
#
#         for block in blocks:
#             if "lines" in block:
#                 for line in block["lines"]:
#                     for span in line["spans"]:
#                         if span["flags"] & 2:  # Check if the text is bold (bold flag is 2)
#                             bold_text.append(span["text"])
#
#     doc.close()
#     return bold_text
#
#
# def print_bold_text(bold_text):
#     for text in bold_text:
#         print(text)
#
#
# # Define the path to your PDF file
# pdf_path = "path/to/your/pdf/file.pdf"  # Update this path
#
# # Extract bold text from the PDF
# bold_text = extract_bold_text_from_pdf(pdf_path)
#
# # Print the extracted bold text
# print_bold_text(bold_text)
