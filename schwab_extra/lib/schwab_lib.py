"""
standard schwab-py interface from extras
"""
import os
import sys
from schwab.auth import easy_client, client_from_token_file
import schwab_extra.schwab_setup_env as se


def ensure_env_vars():
    missing = [name for name in se.VARS if not os.environ.get(name)]
    if missing:
        print("The following environment variables are missing:")
        for name in missing:
            print(f"  • {name}")
        sys.exit(1)

def fetch_env_creds():
    """ check for schwab environment vars"""

    ensure_env_vars()

    token_path   = os.environ["schwab_token_path"]
    api_key      = os.environ["schwab_api_key"]
    app_secret   = os.environ["schwab_app_secret"]
    callback_url = os.environ["schwab_callback_url"]

    return token_path, api_key, app_secret, callback_url


def authenticate():
    """ authenticate a client for schwab-py  """
    token_path, api_key, app_secret, callback_url = fetch_env_creds()
    client = client_from_token_file(token_path, api_key, app_secret)
    return client
