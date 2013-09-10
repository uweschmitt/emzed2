import requests
import functools
import os

import html2text


def guard(fun):
    @functools.wraps(fun)
    def wrapped(base_url, resource, *a, **kw):
        base_url = base_url.rstrip("/")
        assert resource.startswith("/")
        resp = fun(base_url + resource, *a, **kw)
        if resp.status_code != 200:
            formatted = html2text.html2text(resp.content)
            e = requests.HTTPError(resp.status_code)
            e.message = formatted
            e.response = resp
            raise e
        return resp
    return wrapped


get = guard(requests.get)
post = guard(requests.post)
put = guard(requests.put)
delete = guard(requests.delete)


def get_json(base_url, resource):
    return get(base_url, resource).json()


def list_public_files(base_url, silent=False):
    if not silent:
        print "list public packages from %s" % base_url
    return get_json(base_url, "/+files")["packages"]


def list_files(base_url, account_name, folder, silent=False):
    if not silent:
        print "list packges from %s in %s at %s" % (account_name, folder, base_url)
    return get_json(base_url, "/+files/%s%s/:" % (account_name, folder))["packages"]


def upload_file(base_url, account_name, password, path, fp, silent=False):
    if not silent:
        print "upload %s to %s on %s" % (path, account_name, base_url)
    put(base_url, "/+files/%s%s/%s" % (account_name, path, password), fp)


def download_file(base_url, path, download_to, silent=False):
    if not silent:
        print "download %s from %s" % (path, base_url)
    if not os.path.exists(download_to):
        os.makedirs(download_to)
    if os.path.isdir(download_to):
        download_to = os.path.join(download_to, os.path.basename(path))
    # only chunkwize download stream for lowering memory consumption:
    stream = get(base_url, "/%s" % path, stream=True)
    print stream.headers
    with open(download_to, "wb") as fp:
        for data in stream.iter_content(chunk_size=100000):
            fp.write(data)


def delete_file(base_url, account_name, password, path, silent=False):
    if not silent:
        print "delete %s from %s on %s" % (path, account_name, base_url)
    delete(base_url, "/+files/%s%s/%s" % (account_name, path, password))
