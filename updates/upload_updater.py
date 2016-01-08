# encoding: utf-8
from __future__ import print_function


from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256

from base64 import b64decode, b64encode

from subprocess import check_output, call

def sign(message, private_key):
    key = RSA.importKey(private_key)
    h = SHA256.new(message.encode("utf-8"))
    signer = PKCS1_v1_5.new(key)
    signature = signer.sign(h)
    return b64encode(signature)


def check_consitency_of_key_pair():
    from emzed.core.emzed_update_downloader import public_key
    private_key = open("updater_key", "r").read()
    public_key_tobe = check_output("ssh-keygen -y -f updater_key".split(" ")).replace("\n", "")
    print("current public key in emzed:")
    print(repr(public_key))
    print()
    print("public key associated with intended upload:")
    print(repr(public_key_tobe))
    print()
    assert public_key == public_key_tobe, ("please update public key in "
                                           "emzed.core.emzed_update_downloader first")
    return private_key

def write_signature_file(private_key):
    updater_code = open("updater.py").read()
    signature = sign(updater_code, private_key)
    with open("updater.py.signature", "wb") as fh:
        fh.write(signature)

def upload_stuff():
    call("scp updater.py emzed:htdocs/downloads".split(" "))
    call("scp updater.py.signature emzed:htdocs/downloads".split(" "))


def main():
    private_key = check_consitency_of_key_pair()
    write_signature_file(private_key)
    upload_stuff()


if __name__ == "__main__":
    main()
