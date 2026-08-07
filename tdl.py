"""more help on: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1_function.html"""

import logging
from time import sleep

from dotenv import dotenv_values
from rich import print
from rich.logging import RichHandler
from telegram.client import Telegram

from models import *
from utils import load_proxies

TIMEOUT = 3


def test(tg: Telegram, proxies):
    results = []
    for i, proxy in enumerate(proxies, 1):
        logging.info(f"pinging {i}/{len(proxies)}...")
        ping = tg.call_method(
            "pingProxy",
            {"proxy": asdict(proxy)},
        )
        try:
            ping.wait(TIMEOUT, raise_exc=True)
        except TimeoutError:
            logging.warning("timed out (%d); skipping...", TIMEOUT)
            tg.call_method("close")
        except Exception as err:
            logging.error("tdlib error: %s", err)
        else:
            secs = float(ping.update.get("seconds", -1)) if ping.update else -2
            results.append((secs, proxy.uri))
    results.sort()
    return results


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
        sleep(1)
        # login_state = tg.login()
        # logging.info(login_state)
        proxies = load_proxies()
        results = test(tg, proxies)  # noqa: F841
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
