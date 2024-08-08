import pandas as pd
import fitz
import re
import os
import glob

from functools import cmp_to_key
from tqdm import tqdm
from ..utils import TO_BYTE_FACTORS, ZH2NUM


def compare_inquery_letter_filename(filename1: str, filename2: str):
    matches1 = re.findall(r"第[一二三四五六七八九十]", filename1)
    matches2 = re.findall(r"第[一二三四五六七八九十]", filename2)
    if len(matches1) == 0 and len(matches2) == 0:
        return 0
    if len(matches1) == 0:
        return -1
    if len(matches2) == 0:
        return 1

    match1 = matches1[0][1]
    match2 = matches2[0][1]
    return ZH2NUM[match1] - ZH2NUM[match2]


def compare_key_func_prospectus_filename(filename: str):
    dt_extracted = re.findall(r"\d{4}-\d{2}-\d{2}", filename)[0]
    dt_extracted = pd.to_datetime(dt_extracted)

    return dt_extracted


def update_file(doc: fitz.Document, old_filename: str, max_file_size_bytes: float):
    """
    Returns
    -------
    bool
        True: Updated the file
        False: Didn't update the file and a new file should be started
    """
    if not os.path.isfile(old_filename):
        doc.save(old_filename)
        return True

    temp_filename = "temp_file.pdf"
    dir_name = os.path.dirname(old_filename)
    temp_filename_full = os.path.join(dir_name, temp_filename)
    doc.save(temp_filename_full)
    new_file_size = os.path.getsize(temp_filename_full)
    if new_file_size <= max_file_size_bytes:
        os.remove(old_filename)
        os.rename(temp_filename_full, old_filename)
        return True
    else:
        os.remove(temp_filename_full)
        return False


def combine_pdf_from_comp_names(comp_names: list, prospectus_dir: str, inquery_dir: str, output_dir: str,
                                out_filename: str = "combined", max_file_size: float = 576.,
                                max_file_size_unit: str = "MB"):
    """
    temp_dir: for temporarily saving file to compute file size
    """
    max_file_size_bytes = max_file_size * TO_BYTE_FACTORS[max_file_size_unit]

    def combine_pdf_from_comp_names_iter(comp_name: str):
        """
        Sort the input filenames: the latest prospectus and sorted inquery letters from earliest to latest
        """
        out_filenames = []

        prospectus_filenames = glob.glob(os.path.join(prospectus_dir, f"{comp_name}", "*.pdf"))
        if len(prospectus_filenames) == 0:
            # Ignore companies without any propectus
            return out_filenames

        prospectus_filenames.sort(key=compare_key_func_prospectus_filename, reverse=True)
        # if len(prospectus_filenames) > 1:
        #     print(prospectus_filenames)
        out_filenames.append(prospectus_filenames[0])

        inquery_filenames = glob.glob(os.path.join(inquery_dir, f"{comp_name}", "*.pdf"))
        if len(inquery_filenames) == 0:
            # Ignore companies without any inquery letters
            return []
        inquery_filenames.sort(key=cmp_to_key(compare_inquery_letter_filename))
        out_filenames += inquery_filenames

        return out_filenames


    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    combined_pdf = fitz.open()
    part_num = 0
    cur_out_filename = os.path.join(output_dir, f"{out_filename}_{part_num}.pdf")

    for comp_name in tqdm(comp_names):
        out_filenames_iter = combine_pdf_from_comp_names_iter(comp_name)
        # print(list(map(lambda filename: os.path.basename(filename), out_filenames_iter)))
        if len(out_filenames_iter) == 0:
            continue
        for loc_filename in out_filenames_iter:
            with fitz.open(loc_filename) as doc:
                combined_pdf.insert_pdf(doc, from_page=0, to_page=doc.page_count)
                has_updated_file = update_file(combined_pdf, cur_out_filename, max_file_size_bytes)
                if not has_updated_file:
                    combined_pdf.close()
                    combined_pdf = fitz.open()
                    combined_pdf.insert_pdf(doc, from_page=0, to_page=doc.page_count)
                    part_num += 1
                    cur_out_filename = os.path.join(output_dir, f"{out_filename}_{part_num}.pdf")
