from bottle import get, post, put, delete, run, HTTPError, request, ServerAdapter, debug, static_file
import os
import glob
import threading
import time


def parse_key_value_file(path):
    if not os.path.exists(path):
        raise HTTPError(401)
    dd = dict()
    for line in open(path, "r"):
        key, __, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        dd[key] = value
    return dd


def check(password, path):
    password_tobe = parse_key_value_file(os.path.join(path, ".password"))["password"]
    if password != password_tobe:
        raise HTTPError(401)# , "password '%s' does not match" % password)


@put("/+files/<path:path>/<password>")
def upload_package_to(path, password):
    repos, __, local_path =  path.partition("/")
    is_public = os.path.dirname(local_path) == ""
    if is_public:
        f_name = os.path.basename(local_path)
        if f_name in _list_public_packages()["packages"].keys():
            raise HTTPError(409)

    check(password, repos)
    folder, filename = os.path.split(path)
    try:
        os.makedirs(folder)
    except:
        pass
    with open(os.path.join(path), "wb") as fp:
        fp.write(request.body.getvalue())


@delete("/+files/<path:path>/<password>")
def delete_file_from(path, password):
    repos, __, __ =  path.partition("/")
    check(password, repos)
    if os.path.exists(path):
        os.remove(path)
    else:
        raise HTTPError(404)



def _list_public_packages():
    files = glob.glob("*/*")
    files = [ f for f in files if not f.startswith(".") and os.path.isfile(f)]
    files = dict( (os.path.basename(f), f) for f in files)
    return dict(packages=files)
list_public_packages = get("/+files")(_list_public_packages)

@get("/<path:path>")
def download_file(path):
    if not os.path.exists(path):
        raise HTTPError(404)
    return static_file(path, root=".")


class StopableWSGIRefServer(ServerAdapter):

    started = False
    srv = None

    def run(self, handler): # pragma: no cover
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            self.options['handler_class'] = QuietHandler
        self.srv = make_server(self.host, self.port, handler, **self.options)
        self.srv.serve_forever()

    def stop(self):
        assert self.started
        startat = time.time()
        while self.srv is None and time.time() <= startat + 1.0: # wait one secoond to come up
            time.sleep(0.1)
        if self.srv is None:
            raise Exception("sever did not come up !")
        self.srv.shutdown()


class BackgroundWebserver(threading.Thread):

    def __init__(self, path, port=54321, host="0.0.0.0"):
        self.path = path
        self.server = StopableWSGIRefServer(port=port, host=host)
        super(BackgroundWebserver, self).__init__()

    def create_account(self, name, password):
        full_path = os.path.join(self.path, name, ".password")
        if os.path.exists(full_path):
            raise Exception("account already exists")
        try:
            os.makedirs(os.path.dirname(full_path))
        except:
            pass
        with open(full_path, "wt") as fp:
            print >> fp, "password=%s" % password

    def start(self):
        self.server.started = True
        super(BackgroundWebserver, self).start()
        import time
        time.sleep(1.0) # wait to come up

    def run(self):
        os.chdir(self.path)
        run(server=self.server)

    def stop(self):
        self.server.stop()
        self.join()

    def is_alive(self):
        return super(BackgroundWebserver, self).is_alive()



if __name__ == "__main__":
    import sys
    assert len(sys.argv) == 2, "need directory to server from"

    debug(True)
    ws = BackgroundWebserver(sys.argv[1])
    ws.start()

