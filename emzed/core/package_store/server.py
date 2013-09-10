from bottle import HTTPError, request, Bottle, ServerAdapter, debug, static_file
import os
import glob
import threading
import time
import functools


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


class FileServerApplication(object):

    """
    CONCEPT:

    1) For each user/account we have a subfolder or the root data_dir.

    2) In this account folder we have a .password file which contains text "passwort=xxxx".

    3) Files in the account folder are considered as "public", for hiding files each user_account
       folder may contain subfolders. This local subfolder is "secret", so only clients knowing
       this path can list them or download from it. For keeping them secret, such subfolders can
       not be listed by the web service.
       Files starting with "." are not considered as public !

    4) Public files must have a unique name across all user accounts !

    Some URLs look a bit complicated, but bottle had some problems resolving routes I tried
    before.

    """

    def __init__(self, data_dir):
        self.data_dir = data_dir.rstrip("/")

        self.app = Bottle()
        self.setup_routes()

    def setup_routes(self):

        # collects all public files and returns dictionary mapping file name to full path
        # in respect to root dir:
        self.app.route("/+files", method="GET", callback=self.list_public)

        # upload file. here path is related to the root folder, so it is the concatenation of
        # account name and subfolder in this account folder:
        self.app.route("/+files/<path:path>/<password>", method="PUT", callback=self.upload)

        # list files. here path is related to the root folder, so it is the concatenation of
        # account name and subfolder in this account folder:
        # FOR EASIER ROUTING, PASSWORD IS A DUMMY, SO THE CLIENT CAN USE WHAT IT WANTS !
        self.app.route("/+files/<path:path>/<password>", method="GET", callback=self.list_)

        # delete file. here path is related to the root folder, so it is the concatenation of
        # account name and subfolder in this account folder:
        self.app.route("/+files/<path:path>/<password>", method="DELETE", callback=self.delete)

        # fetch file from known path. no auth check here, as the path is considered to be "secret"
        # THIS ROUTE MUST BE THE LAST !
        self.app.route("/<path:path>", method="GET", callback=self.download)

    def run(self, server):
        self.app.run(server=server)

    def create_account(self, name, password):
        full_path = os.path.join(self.data_dir, name, ".password")
        if os.path.exists(full_path):
            raise Exception("account already exists")
        try:
            os.makedirs(os.path.dirname(full_path))
        except:
            pass
        with open(full_path, "wt") as fp:
            print >> fp, "password=%s" % password

    def check(self, password, repos):
        pw_file_path = os.path.join(self.data_dir, repos, ".password")
        password_tobe = parse_key_value_file(pw_file_path)["password"]
        if password != password_tobe:
            raise HTTPError(401)  # , "password '%s' does not match" % password)

    def dump_repos(self):
        for root, dirnames, filenames in os.walk(self.data_dir):
            print "FOLDER", root
            for d in dirnames:
                print "  DIR ", d
            for f in filenames:
                print "  FILE", f

    #
    # exposed methods start here !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #

    def convert_exception(fun):
        @functools.wraps(fun)
        def wrapped(*a, **kw):
            try:
                return fun(*a, **kw)
            except Exception, e:
                if isinstance(e, HTTPError):
                    raise e
                import traceback
                tb = traceback.format_exc()
                raise HTTPError(500, body=tb)
        return wrapped

    @convert_exception
    def upload(self, path, password):
        full_path = os.path.join(self.data_dir, path)
        repos, __, local_path = path.partition("/")
        is_public = os.path.dirname(local_path) == ""
        if is_public:
            f_name = os.path.basename(local_path)
            if f_name in self.list_public()["packages"].keys():
                raise HTTPError(409)

        self.check(password, repos)
        folder, filename = os.path.split(full_path)
        try:
            os.makedirs(folder)
        except:
            pass
        with open(full_path, "wb") as fp:
            fp.write(request.body.getvalue())

    @convert_exception
    def delete(self, path, password):
        full_path = os.path.join(self.data_dir, path)
        repos, __, __ = path.partition("/")
        self.check(password, repos)
        if os.path.exists(full_path):
            os.remove(full_path)
        else:
            raise HTTPError(404)

    @convert_exception
    def list_public(self):
        n = len(self.data_dir)
        files = glob.glob(os.path.join(self.data_dir, "*", "*"))
        files = [f for f in files if not os.path.basename(f).startswith(".") and os.path.isfile(f)]
        files = dict((os.path.basename(f), f[n:]) for f in files)
        return dict(packages=files)

    @convert_exception
    def list_(self, path, password):
        full_path = os.path.join(self.data_dir, path)
        files = os.listdir(full_path)
        files = [f for f in files
                 if not f.startswith(".") and os.path.isfile(os.path.join(full_path, f))]
        files = dict((os.path.basename(f), os.path.join("/", path, f)) for f in files)
        return dict(packages=files)

    @convert_exception
    def download(self, path):
        full_path = os.path.join(self.data_dir, path)
        if not os.path.exists(full_path):
            raise HTTPError(404)
        return static_file(path, root=self.data_dir)


class StopableWSGIRefServer(ServerAdapter):

    started = False
    srv = None

    def run(self, handler):  # pragma: no cover
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw):
                    pass
            self.options['handler_class'] = QuietHandler
        self.srv = make_server(self.host, self.port, handler, **self.options)
        self.srv.serve_forever()

    def stop(self):
        assert self.started
        startat = time.time()
        while self.srv is None and time.time() <= startat + 1.0:  # wait one secoond to come up
            time.sleep(0.1)
        if self.srv is None:
            raise Exception("sever did not come up !")
        self.srv.shutdown()


class BackgroundWebserver(threading.Thread):

    def __init__(self, app, port, host):
        self.port = port
        self.host = host
        self.url = "http://%s:%s" % (host, port)
        self.server = StopableWSGIRefServer(port=port, host=host)
        self.app = app
        super(BackgroundWebserver, self).__init__()

    def start(self):
        self.server.started = True
        super(BackgroundWebserver, self).start()
        import time
        time.sleep(1.0)  # wait to come up

    def run(self):
        self.app.run(self.server)

    def stop(self):
        self.server.stop()
        self.join()

    def is_alive(self):
        return super(BackgroundWebserver, self).is_alive()


def create_file_server(data_dir, port=37614, host="0.0.0.0"):
    return BackgroundWebserver(FileServerApplication(data_dir), port, host)


if __name__ == "__main__":
    import sys
    assert len(sys.argv) == 2, "need directory to server from"

    debug(True)
    ws = create_file_server(sys.argv[1])
    ws.start()
