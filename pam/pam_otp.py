#!/usr/bin/env python3
import os
import pwd
import grp
import hmac
import time
import traceback
import pyotp
import json

"""
{
    "pingu"  : "JBSWY3DPEHPK3PXP",
    "@users" : "4EF6A46F1BCF2345"
}
"""

## Pam config (common-auth)
## before pam_unix:
# auth sufficient pam_python.so /usr/libexec/pam_otp.py

config_file = "/etc/otp-secrets.json"
state_dir = "/run/eta-otp"

# common-auth is shared by every pam service. The pin is meant for logging in
# at the board, it shouldn't replace the password for getting root.
skip_services = ["sudo", "sudo-i", "su", "su-l", "runuser", "runuser-l",
                 "polkit-1", "sshd"]

def pam_sm_authenticate(pamh, flags, argv):
    if pamh.service in skip_services:
        return pamh.PAM_IGNORE

    # fetch username
    try:
        user = pamh.get_user(None)
    except Exception as e:
        return pamh.PAM_AUTH_ERR

    # fetch otp
    if pamh.authtok is None:
        try:
            conv = pamh.conversation(pamh.Message(pamh.PAM_PROMPT_ECHO_OFF, "Password: "))
            pamh.authtok = conv.resp
        except:
            return pamh.PAM_AUTH_ERR

    # read config
    config = {}
    if not os.path.isfile(config_file):
        return pamh.PAM_AUTH_ERR
    with open(config_file, "r") as f:
        config = json.load(f)


    def check_otp(user):
        otp = pyotp.TOTP(config[user])
        now = time.time()
        token = pamh.authtok
        if not token:
            return False
        # compare bytes, compare_digest raises on str with non ascii
        # characters (a normal password like "şifre" goes through here too)
        if isinstance(token, str):
            token = token.encode()
        if not hmac.compare_digest(otp.at(now).encode(), token):
            return False

        # a code is valid for the whole 30 seconds, don't let it be used twice
        timestep = int(now // otp.interval)
        state_file = os.path.join(state_dir, user.replace("/", "_"))
        try:
            with open(state_file, "r") as f:
                if timestep <= int(f.read().strip()):
                    return False
        except (OSError, ValueError):
            pass
        try:
            os.makedirs(state_dir, mode=0o700, exist_ok=True)
            with open(state_file, "w") as f:
                f.write(str(timestep))
        except OSError:
            pass
        return True

    # check otp by group
    for group in grp.getgrall():
        if user in group.gr_mem and f"@{group.gr_name}" in config:
            if check_otp(f"@{group.gr_name}"):
                return pamh.PAM_SUCCESS

    # check otp
    if user in config:
        if check_otp(user):
            return pamh.PAM_SUCCESS

    return pamh.PAM_AUTH_ERR

def pam_sm_setcred(pamh, flags, argv):
    return pamh.PAM_SUCCESS
