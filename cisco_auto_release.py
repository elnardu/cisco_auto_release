#!/usr/bin/env python3
import re
import sys
from pathlib import Path
import os
import json

try:
    import requests
    import certifi
except ImportError:
    print("Please install requests package")
    print("pip install requests")
    sys.exit(1)


CISCO_DISPATCHER_URL = "https://spam.itap.purdue.edu/Dispatcher"
DIR_PATH = Path(__file__).parent.absolute()
CERTS_PATH = DIR_PATH.joinpath("certs.pem")
CONFIG_PATH = DIR_PATH.joinpath("config.json")


message_id_re = re.compile(r"type=\"checkbox\"\W*value=\"([0-9]+)\"")
csrf_re = re.compile(r"var CSRFKey = '([^']+)';")
valid_auth_link_re = re.compile(
    r"https://spam\.itap\.purdue\.edu/Search\?h=[^&\s]+&email=\S+"
)


def get_session(auth_url):
    session = requests.Session()
    session.verify = str(CERTS_PATH)

    res = session.get(auth_url)
    res.raise_for_status()

    csrf = csrf_re.search(res.text).group(1)
    assert csrf
    return session, csrf


def get_message_ids(session, csrf):
    res = session.post(
        CISCO_DISPATCHER_URL,
        data={
            "action": "ChangeDisplay",
            "screen": "Search",
            "page": None,
            "ignore_escapes:criterion": None,
            "pg": None,
            "pageSize": 250,
            "message_action1": None,
            "message_action2": None,
            "CSRFKey": csrf,
        },
    )
    res.raise_for_status()
    return message_id_re.findall(res.text)


def release_message_ids(session, csrf, message_ids):
    res = session.post(
        CISCO_DISPATCHER_URL,
        data={
            "action": "Message:Release",
            "screen": "Search",
            "page": None,
            "ignore_escapes:criterion": None,
            "pg": None,
            "pageSize": 50,
            "mid[]": message_ids,
            "message_action1": "Release",
            "message_action2": None,
            "CSRFKey": csrf,
        },
    )
    res.raise_for_status()


def build_pem_file():
    # It seems like purdue's spam server is misconfigured. It does not supply
    # full certificate chain for ssl to work properly. See
    # https://www.ssllabs.com/ssltest/analyze.html?d=spam.itap.purdue.edu ->
    # "Chain issues: Incomplete"
    # This workaround downloads missing certificate: "InCommon RSA Server CA"

    with open(certifi.where()) as f:
        root_certs = f.read()

    incommon_intermediate_cert = requests.get(
        "https://www.incommon.org/custom/certificates/repository/sha384%20Intermediate%20cert.txt"
    ).text

    pem = root_certs + "\n" + incommon_intermediate_cert

    with open(CERTS_PATH, "w") as f:
        f.write(pem)


def setup_config():
    print("1. Open the last cisco email")
    print("2. At the bottom of that email find a link that looks like this:")
    print(
        '   "https://spam.itap.purdue.edu/Search?h=00000000000000000000&email=username%40purdue.edu%2Cusername%40purdue0.onmicrosoft.com"'
    )
    print("3. Copy and paste it here")

    valid = False
    while not valid:
        link = input("> ").strip()
        if valid_auth_link_re.fullmatch(link):
            valid = True
        else:
            print("Invalid link. Please try again")

    with open(CONFIG_PATH, "w") as f:
        json.dump({"cisco_auth_urls": [link]}, f)

    print("Success!")


if __name__ == "__main__":
    if not CERTS_PATH.is_file():
        build_pem_file()

    if not CONFIG_PATH.is_file():
        if sys.stdout.isatty():  # interactive terminal?
            setup_config()
        else:
            print("Could not find the config file")
            sys.exit(1)

    with open(CONFIG_PATH) as f:
        config = json.load(f)

    for auth_url in config["cisco_auth_urls"]:
        ses, csrf = get_session(auth_url)
        ids = get_message_ids(ses, csrf)

        if len(ids) != 0:
            release_message_ids(ses, csrf, ids)

