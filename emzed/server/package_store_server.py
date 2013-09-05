from bottle import route, run, HTTPError, request, ServerAdapter
import os
import glob
import threading
import time


def parse_key_value_file(path):
    dd = dict()
    for line in open(path, "r"):
        key, __, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        dd[key] = value
    return dd

#def set_password(repos, password):


def check(password, path):
    password_tobe = parse_key_value_file(os.path.join(path, ".password"))["password"]
    assert password == password_tobe

    tobe = open(os.path.join(path, "_"), "r").read()
    return tobe.strip() == secret


def set_visible(path, secret):
    open(os.path.join(path, "_"), "w").write(secret)


def _public_files():
    files = [f for f in glob.glob("*/public/*")]
    return dict(packages={os.path.basename(p): p for p in files})

public_files = route("/", method="GET")(_public_files)

@route("/+password/<user>/<password>", method="GET")
def set_password(user, password):
    with open(os.path.join(user, ".password")) as fp:
        fp.write("password=%s" % password.strip())


@route("/<folder:path>", method="GET")
    def list_packages(folser):
    files = [ f for f in os.listdir(folder) if not f.startswith(".") and not f.endswith("_")]
    return dict(packages=files)


@route("/<password>/<secret>/<repos:path>/<filename>", method="PUT")
def upload_package(password, secret, repos, filename):
    check(password, repos)
    assert filename not in os.listdir(repos)
    with open(os.path.join(repos, filename), "wb") as fp:
        fp.write(request.body.getvalue())
        set_visible(os.path.join(repos, filename), secret)


@route("/<password>/<repos:path>/<filename>", method="DELETE")
def delete_package(password, repos, filename):
    check(password, repos)
    assert filename in os.listdir(repos)
    os.remove(os.path.join(repos, filename))
    os.remove(os.path.join(repos, filename, "_"))


@route("/<secret>/<repos:path>/<filename>", method="GET")
def get_package(secret, repos, filename):
    if is_visible(os.path.join(repos, filename), secret):
        return open(os.path.join(repos, filename))



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

    ws = BackgroundWebserver(sys.argv[1])
    ws.start()

