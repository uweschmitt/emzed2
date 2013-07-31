import pdb
# encoding:latin-1

import config
import requests
import urllib

def get_latest_emzed_version_from_pypi():
    url = config.get_url("testpypi", "url")
    response = requests.get(url + "emzed/json")
    response.raise_for_status()
    version_str = response.json()["info"]["version"]
    return tuple(map(int, version_str.split(".")))
