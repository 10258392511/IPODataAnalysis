PATTERNS = {
    "content": r"目录[ ]*\n",
    "content_entry": r".*[一二三四五六七八九十0-9]+.*[\n ]*\.{2,}",
    "reply": r"(?<!\S)[【\[]?回复[ ]*[】\]]?[ \n:：]*\n",  # Start of the str or not be proceeded by a non-whitespace char
    "subtitle": r"[A-Za-z0-9一二三四五六七八九十]{1,2}、[^\n]*\n|[(（]+[A-Za-z0-9一二三四五六七八九十]{1,2}[)）]+[^\n]*\n",
}

CHROME_EXECUTABLE_PATH = r"F:\chromedriver-win64\chromedriver.exe"
