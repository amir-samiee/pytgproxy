"""more help on: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1_function.html"""

import logging
from pathlib import Path

from dotenv import dotenv_values
from rich import print
from rich.logging import RichHandler
from telegram.client import Telegram

from models import *

TIMEOUT = 5


def test(tg: Telegram):
    uris = Path("proxies.txt").read_text().splitlines()
    for i, uri in enumerate(uris, 1):
        logging.info(f"pinging {i}/{len(uris)}...")
        proxy = Proxy.from_uri(uri)
        try:
            ping = tg.call_method("pingProxy", {"proxy": asdict(proxy)}, block=True)
            logging.debug(ping.request)
            ping.wait(TIMEOUT)
        except TimeoutError:
            logging.warning(
                "timed out. \tupdate:%s\tok:%s",
                ping.update,
                ping.ok_received,
            )
        except Exception as exc:
            logging.error(exc)
            ping = tg.call_method("pingProxy", {"proxy": None})
        else:
            print("ping:", ping.update)


def main():
    try:
        envvars = dotenv_values()
        ai = envvars["API_ID"]
        ah = envvars["API_HASH"]
        lp = envvars["LIB_PATH"]
        bt = envvars["BOT_TOKEN"]
        ek = envvars["ENCRYPTION_KEY"]
        assert ai and ah and bt and ek
        tg = Telegram(
            api_hash=ah,
            bot_token=bt,
            api_id=int(ai),
            library_path=lp,
            database_encryption_key=ek,
        )
        login_state = tg.login()
        logging.info(login_state)
        test(tg)
    except KeyboardInterrupt:
        logging.info("user demanded exit")
    finally:
        tg.stop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        handlers=[RichHandler()],
    )
    main()
