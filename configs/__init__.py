PATTERNS = {
    "content": r"目录[ ]*\n",
    "content_entry": r".*[一二三四五六七八九十0-9]+.*[\n ]*\.{2,}",
    "reply": r"[【\[]?回复[】\]]?[ ]*[:：]+[ ]*\n",
    "subtitle": r"[A-Za-z0-9]+、[^\n]*\n|[(（]+[A-Za-z0-9]+[)）]+[^\n]*\n",
}
