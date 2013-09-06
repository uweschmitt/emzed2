import requests
import functools

def improve(fun):
    @functools.wraps(fun)
    def wrapped(base_url, resource, *a):
        base_url = base_url.rstrip("/")
        assert resource.startswith("/")
        resp = fun(base_url + resource, *a)
        try:
            resp.raise_for_status()
        except:
            print "URL=", resp.url
            raise
        return resp
    return wrapped

get = improve(requests.get)
post = improve(requests.post)
put = improve(requests.put)
delete = improve(requests.delete)

def get_json(base_url, resource):
    return get(base_url, resource).json()


def list_public_packages(base_url):
    return get_json(base_url, "/+files")["packages"]

def list_files(base_url, account_name, folder):
    return get_json(base_url, "/+files/%s%s/:" % (account_name, folder))["packages"]

def upload_file(base_url, account_name, password, path, fp):
    put(base_url, "/+files/%s%s/%s" % (account_name, path, password), fp)

def download_file(base_url, account_name,  path):
    return get(base_url, "/%s%s" % (account_name, path)).content

def delete_file(base_url, account_name, password,  path):
    delete(base_url, "/+files/%s%s/%s" % (account_name, path, password))

