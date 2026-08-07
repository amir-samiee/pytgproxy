"""more help on: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1_function.html"""

import logging
from time import sleep

from dotenv import dotenv_values
from rich import print
from rich.logging import RichHandler
from telegram.client import Telegram

from models import *
from utils import *

TIMEOUT = None


def test_proxies(tg: Telegram, proxies):
    results = []
    for i, proxy in enumerate(proxies, 1):
        logging.info(f"pinging {i}/{len(proxies)}...")
        ping = tg.call_method(
            "pingProxy",
            {"proxy": asdict(proxy)},
        )
        try:
            ping.wait(TIMEOUT, raise_exc=False)
        except TimeoutError:
            logging.warning("timed out (%d); skipping...", TIMEOUT)
        except Exception as err:
            logging.error("tdlib error: %s", err)
        else:
            secs = float(ping.update.get("seconds", -1)) if ping.update else -2
            uri = proxy.uri
            if secs > 0:
                logging.info("ping: %f \t proxy: %s", secs, uri)
            results.append((secs, uri))
    results.sort()
    return results


def main():
    envvars: dict = dotenv_values()
    try:
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
        login_state = tg.login()
        logging.info(login_state)
        proxies = load_proxies()
        results = test_proxies(tg, proxies)
        dump_results(results)
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
    main()
