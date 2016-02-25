
# about this folder.

We keep this folder outside the emzed Python package to hide the private key used to sign the
emzed updater script updater.py.

The private key must not be checked in to the github repository and the file name should be
listed in the local .gitignore file.

To create a new keypair run `create_key_pair.sh` script, this writes the private key to
`updater_key` and the public key to `updater_key.pub`. To keep emzed in sync with the key pair
you have to edit `emzed/core/emzed_update_downloader.py` manually. This script contains
instructions what to do.

# to create and upload a new updater

- edit `updater.py` in this folder and test it.

- run `upload_updater.py` to sign the new updater script and to upload signaure and script to
  the emzed website.

