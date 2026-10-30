#!/usr/bin/env python3
import sys
import os
import pwd
import json
import base64
import binascii

config_file = "/etc/otp-secrets.json"
config = {}
try:
    if os.path.isfile(config_file):
        with open(config_file, "r") as f:
            config = json.load(f)

        os.chown(config_file, 0, 0)
        os.chmod(config_file, 0o600)

except:
    pass

def find_user(uid):
    # pwd goes through nss, so domain (sssd/ldap) users are found too
    try:
        return pwd.getpwuid(int(uid)).pw_name
    except (KeyError, ValueError):
        return None

def write_config():
    # create the new file as 0600 from the start, then move it in place
    tmp_file = config_file + ".tmp"
    fd = os.open(tmp_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(config, f)
    os.chown(tmp_file, 0, 0)
    os.chmod(tmp_file, 0o600)
    os.replace(tmp_file, config_file)

def valid_secret(secret):
    # pam_otp.py can't use a secret that doesn't decode, it would raise there.
    # No length limit: the "from key" option in the gui can make short ones.
    if not secret:
        return False
    try:
        # decoded the same way pyotp does it
        base64.b32decode(secret + "=" * (-len(secret) % 8), casefold=True)
    except (binascii.Error, ValueError):
        return False
    return True

def save(user, secret):
    if not valid_secret(secret):
        print("invalid secret", file=sys.stderr)
        sys.exit(1)
    config[user] = secret
    write_config()

def load(user):
    if user in config:
        print(config[user])

def remove(user):
    if user in config:
        config.pop(user)
    write_config()

def status(user):
    return user in config

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if "PKEXEC_UID" in os.environ:
            user = find_user(os.environ["PKEXEC_UID"])
        else:
            user = input()
        if not user:
            print("user not found", file=sys.stderr)
            sys.exit(1)
        if sys.argv[1] == "save":
            secret = input()
            save(user, secret)
        elif sys.argv[1] == "remove":
            remove(user)
        elif sys.argv[1] == "load":
            load(user)
        elif sys.argv[1] == "status":
            if status(user):
                print("true")
                sys.exit(0)
            else:
                print("false")
                sys.exit(1)
    else:
        print("actions.py [save|load|remove|status] (secret)")

