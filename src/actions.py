#!/usr/bin/env python3
import sys
import os
import json

CONFIG_FILE = "/etc/otp-secrets.json"
DEFAULT_SECRET = "JBSWY3DPEHPK3PXP"

# Load existing config
config = {}
try:
    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
        os.chown(CONFIG_FILE, 0, 0)
        os.chmod(CONFIG_FILE, 0o600)
except:
    pass

def save(secret=DEFAULT_SECRET):
    """Global secret for all users"""
    config['global'] = secret
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)
    os.chown(CONFIG_FILE, 0, 0)
    os.chmod(CONFIG_FILE, 0o600)

def load():
    """Return global secret"""
    if 'global' in config:
        print(config['global'])

def remove():
    """Remove global secret"""
    if 'global' in config:
        config.pop('global')
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)
    os.chown(CONFIG_FILE, 0, 0)
    os.chmod(CONFIG_FILE, 0o600)

def status():
    return 'global' in config

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "save":
            save(sys.argv[2])
        elif cmd == "load":
            load()
        elif cmd == "remove":
            remove()
        elif cmd == "status":
            if status():
                print("true")
                sys.exit(0)
            else:
                print("false")
                sys.exit(1)
    else:
        print("actions.py [save|load|remove|status] (secret)")
