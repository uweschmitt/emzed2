import requests

def get_json(url):
    from config import global_config
    user = global_config.get("emzed_store_user")
    password = global_config.get("emzed_store_password")
    return requests.get(url, headers=dict(Accept="application/json"), auth=(user, password))
