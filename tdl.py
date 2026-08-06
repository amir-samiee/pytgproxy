"""more help on: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1_function.html"""

import logging
from pathlib import Path

from dotenv import dotenv_values
from rich import print
from rich.logging import RichHandler
from telegram.client import Telegram

from models import *

TIMEOUT = 10


def test(tg: Telegram, proxy_uris):
    for i, uri in enumerate(proxy_uris, 1):
        logging.info(f"pinging {i}/{len(proxy_uris)}...")
        proxy = Proxy.from_uri(uri)
        ping = tg.call_method(
            "pingProxy",
            {"proxy": asdict(proxy)},
        )
        try:
            ping.wait(TIMEOUT)
        except TimeoutError:
            logging.warning("timed out (%d); skipping...", TIMEOUT)
        else:
            logging.info("ping: %s", ping.update)


def main():
    try:
        envvars: dict = dotenv_values()
        tg = Telegram(
            tdlib_verbosity=0,
            files_directory=envvars.get("FILES_DIR"),
            api_id=int(envvars["API_ID"]),
            api_hash=envvars["API_HASH"],
            bot_token=envvars["BOT_TOKEN"],
            library_path=envvars["LIB_PATH"],
            database_encryption_key=envvars["ENCRYPTION_KEY"],
        )
        # login_state = tg.login()
        # logging.info(login_state)
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
        "Running this script INSIDE WSL might not "  ##
        "work if there's a proxy running OUTSIDE WSL"
    )
    main()
