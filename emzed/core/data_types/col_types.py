import hashlib


class Blob(object):

    def __init__(self, data, type_=None):
        self.data = data
        self.unique_id = None
        if type_ is None:
            if data.startswith("\x89PNG"):
                type_ = "PNG"
            elif data[0] == "\xff":
                hex_header = "ff d8 ff e0 00 10 4a 46 49 46 00 01"
                jpg_soi_marker = "".join(chr(int(f, 16) for f in hex_header.split()))
                if jpg_soi_marker in data:
                    type_ = "JPG"
            elif data.startswith("emzed_version=2."):
                type_ = "TABLE"
            elif data.startswith("<?xml version=\""):
                type_ = "XML"
        self.type_ = type_

    def __str__(self):
        type_ = "unknown type" if self.type_ is None else "type %s" % self.type_
        return "<Blob %#x of %s>" % (id(self), type_)

    def uniqueId(self):
        if self.unique_id is None:
            h = hashlib.sha256()
            h.update(self.data)
            self.unique_id = h.hexdigest()
        return self.unique_id
