import fitz
import sys
import re

from ..global_configs import ROOT_DIR
from IPODataAnalysis.configs import PATTERNS


def extract_content(doc: fitz.Document):
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
