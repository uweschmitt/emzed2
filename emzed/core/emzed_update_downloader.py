# encoding: utf-8
from __future__ import print_function


from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256

import requests
from base64 import b64decode, b64encode

"""
to reformat one very long line from public key file with vim:
1. mark key code line
2. !fold -w 90
3. remove id resp. email adress at end !
"""

public_key="""
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDiqXuqRPcBuuYU8AxdFwHB0Cg9PfyG/8zpNtVdPIIJswAlD3XqsA
f+EqCeqvgiuwvY+PotGhhXmW3OYM/SGdkMk237i/Gu4e3FfgZdHHdS4ara9dJRXPcB6ztJv5aXap0OYrqA4nqys+AY
FrIB9cRzHXKm+NLORa5dt3z4Mhje4doPeMsNH0X/mX4sPrrZ29CM/XyzVQsp1+hhZJJp6Dsmvz2Zhdx28AEr5RQAYL
gt5a7PaxfQEEWjMM1AR7qiV+ZK+ioGiZ3yYICLtdgBCp9Kf1rTn1x9tw0+CfCDHOSYo3t5uSCA1BcHQ4s8sIg1kWl9
+HM0HFsKy8EoO3VC1qmL
""".replace("\n", "")


def verify_sign(signature, message, public_key=public_key):
    '''
    Verifies with a public key from whom the data came that it was indeed signed by their private
    key.

    param: public_key_loc Path to public key
    param: signature String signature to be verified
    return: Boolean. True if the signature is valid; False otherwise.
    '''

    rsakey = RSA.importKey(public_key)
    signer = PKCS1_v1_5.new(rsakey)
    digest = SHA256.new()
    # Assumes the data is base64 encoded to begin with
    digest.update(message.encode("utf-8"))
    return signer.verify(digest, b64decode(signature))


def fetch_code_and_signature():
    base_url = "http://emzed.ethz.ch/downloads"
    update_script = "updater.py"
    signature_file = "updater.py.signature"

    signature = requests.get(base_url + "/" + signature_file).text.strip()
    script_code = requests.get(base_url + "/" + update_script).text.encode("utf-8")

    return script_code, signature


def check(script_code, signature):
    if not verify_sign(signature, script_code):
        raise Exception("signature and updater code do not match")


def import_from_string(script_code):

    # we mimic a "module" (name space) for the downloaded code here:

    class Updater(object):
        pass

    updater = Updater()
    exec script_code.encode("utf-8") in updater.__dict__
    return updater


def check_module(module):

    for fun_name in ("version", "description", "run_update"):
        assert hasattr(module, fun_name), "update has no function '%s'" % fun_name
        assert callable(getattr(module, fun_name)), "update has no function '%s'" % fun_name


def load_updater_from_website():

    script_code, signature = fetch_code_and_signature()
    check(script_code, signature)
    module = import_from_string(script_code)
    check_module(module)
    module.code = script_code
    return module


def trim_left(txt):
    txt = txt.strip("\n")
    first_indent = len(txt) - len(txt.lstrip(" "))
    lines = [line[first_indent:] for line in txt.split("\n")]
    return "\n".join(lines)


if __name__ == "__main__":

    updater = load_updater_from_website()
    print("new version is:", updater.version())
    print("description:\n\n", trim_left(updater.description()), sep="")
