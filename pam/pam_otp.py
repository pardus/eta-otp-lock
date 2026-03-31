#!/usr/bin/env python3
import os
import pyotp
import json

CONFIG_FILE = "/etc/otp-secrets.json"

# OTP kullanılmayacak kullanıcılar
SKIP_USERS = ["root", "etapadmin"]

def pam_sm_authenticate(pamh, flags, argv):
    # kullanıcıyı al
    try:
        user = pamh.get_user(None)
    except:
        return pamh.PAM_AUTH_ERR

    # 🔥 bu kullanıcılar OTP kullanmaz → direkt skip
    if user in SKIP_USERS:
        return pamh.PAM_IGNORE

    # fetch OTP (senin yapı aynen korunuyor)
    if pamh.authtok is None:
        try:
            conv = pamh.conversation(
                pamh.Message(pamh.PAM_PROMPT_ECHO_OFF, "Password: ")
            )
            pamh.authtok = conv.resp
        except:
            return pamh.PAM_AUTH_ERR

    # read config
    if not os.path.isfile(CONFIG_FILE):
        return pamh.PAM_IGNORE   # 🔥 fallback: parola çalışsın

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    if 'global' in config:
        otp = pyotp.TOTP(config['global'])

        # ✔ OTP doğruysa giriş
        if otp.now() == pamh.authtok:
            return pamh.PAM_SUCCESS

    # 🔥 OTP yanlış → parola denemeye izin ver
    return pamh.PAM_IGNORE


def pam_sm_setcred(pamh, flags, argv):
    return pamh.PAM_SUCCESS
