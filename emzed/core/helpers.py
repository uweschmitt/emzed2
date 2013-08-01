import requests
def get_json(url):
    return requests.get(url, headers=dict(Accept="application/json"))
