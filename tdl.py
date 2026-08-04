"""more help on: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1_function.html"""

import logging
from pathlib import Path

from dotenv import dotenv_values
from rich import print
from rich.logging import RichHandler
from telegram.client import Telegram

from pytgproxy.models import *

TIMEOUT = 10


def test(tg: Telegram):
    uris = Path("proxies.txt").read_text().splitlines()
    for i, uri in enumerate(uris, 1):
        proxy = Proxy.from_uri(uri)
        print(f"pinging {i}/{len(uris)}...", end=" \t")
        # ping = tg.call_method("pingProxy", asdict(proxy))
        # ping = tg._send_data(asdict(PingProxy(proxy)))
        ping = tg.call_method("pingProxy", {"proxy": asdict(proxy)})
        # ping = tg.call_method("pingProxy", {"proxy": None})
        print(ping.request)
        try:
            ping.wait(TIMEOUT, raise_exc=True)
        except TimeoutError:
            # print("timed out")
            print(ping.update)
        except Exception as e:  # noqa: BLE001
            print("TDLib error:", e)
        else:
            print("ping:", ping.update)




def main():
    try:
        envvars = dotenv_values()
        ek = envvars["ENCRYPTION_KEY"]
        assert ek
        tg = Telegram(
            api_id=123456,
            api_hash="api_hash",
            bot_token=envvars["BOT_TOKEN"],
            database_encryption_key=ek,
        )
        test(tg)
    finally:
        tg.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])
    main()
