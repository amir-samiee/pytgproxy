"""more help on: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1_function.html"""

# import os

# for x in os.environ:
#     if "prox" in x.lower():
#         os.environ.pop(x)

import logging
from pathlib import Path

from dotenv import dotenv_values
from rich import print
from rich.logging import RichHandler
from telegram.client import Telegram

from models import *

TIMEOUT = 5


def test(tg: Telegram, proxy_uris):
    for i, uri in enumerate(proxy_uris, 1):
        logging.info(f"pinging {i}/{len(proxy_uris)}...")
        proxy = Proxy.from_uri(uri)
        ping = tg.call_method(
            "pingProxy",
            # "testProxy",
            {
                "proxy": None,
                # asdict(proxy),
                # "tc_id": 2,
                # "timeout": 10.0,
            },
        )
        ping.wait()
        try:
            ...
        except KeyboardInterrupt:
            break
        except BaseException as err:
            ...
        else:
            ...


def main():
    try:
        envvars = {k: v for k, v in dotenv_values().items() if v}
        tg = Telegram(
            tdlib_verbosity=0,
            api_id=int(envvars["API_ID"]),
            api_hash=envvars["API_HASH"],
            bot_token=envvars["BOT_TOKEN"],
            library_path=envvars["LIB_PATH"],
            database_encryption_key=envvars["ENCRYPTION_KEY"],
        )
        login_state = tg.login()
        logging.info(login_state)
        uris = Path("proxies.txt").read_text().splitlines()
        test(tg, uris)
    except KeyboardInterrupt:
        print("", end="\r")
        logging.info("user demanded exit")
    finally:
        tg.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            RichHandler(),
            logging.FileHandler(".log", "w"),
        ],
    )
    logging.warning(
        "Running this script INSIDE WSL might not "
        "work if there's a proxy running OUTSIDE WSL"
    )
    main()
