import requests
import json

from ..global_configs import ROOT_DIR

API_FILENAME = r"D:\testings\Python\TestingPython\IPODataAnalysis\data\configs\api_keys.json"
with open(API_FILENAME, "r") as rf:
    API_DICT = json.load(rf)
URL = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={API_DICT['api_key']}&" \
      f"client_secret={API_DICT['secret_key']}"
MODEL_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-speed-128k?access_token={access_token}"


def get_access_token():
    payload = json.dumps("")
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    response = requests.request("POST", URL, headers=headers, data=payload)

    return response.json().get("access_token")


def get_response(prompt: dict):
    payload = json.dumps(prompt)
    headers = {
        'Content-Type': 'application/json'
    }

    post_url = MODEL_URL.format(access_token=get_access_token())
    response = requests.request("POST", post_url, headers=headers, data=payload)
    resp_dict = json.loads(response.text)
    if "result" not in resp_dict:
        raise ValueError("Unsuccessful to retrieve a reply")

    return resp_dict["result"]
