import logging
from itertools import batched

from dotenv import dotenv_values
from telegram.tdjson import TDJson

from main import dump_results, load_proxies, setup_logging
from models import asdict
from proxy import Proxy


class Mint:
    """Mini Telegram Representative Object for TDJson's API, tailored for this specific purpose"""

    @classmethod
    def mock_params(cls):
        return {
            "@type": "setTdlibParameters",
            "api_id": 1,  # type matters
            "files_directory": ".tel",  # to keep the dir-tree clean
            "system_language_code": "en",
            "device_model": "mock",
            "application_version": "pock",
            "api_hash": "hock",  # all the provided keys are required
            "@extra": {"request_id": "params"},
        }

    def __init__(self):
        self.tg = self.init_telegram()
        self._pending = 0
        self.results = []

    def handle_result(self, result: dict):
        uri = result["@extra"]["rid"]
        i = result["@extra"]["i"]
        if result["@type"] == "seconds":
            ms = 1000 * result["seconds"]
            logging.info(" [%4d] %4d ms: %s", i, ms, uri)
            self.results.append((ms, uri))
        else:
            logging.debug("an error occurred while testing %s", uri)
            logging.error("[%4d] error code %3d: %s", i, result["code"], result["message"])

    def test(self, proxies: list[Proxy], batch_size=10):
        i = 0
        for batch in batched(proxies, batch_size):
            for proxy in batch:
                query = {
                    "@type": "pingProxy",
                    "proxy": asdict(proxy),
                    "@extra": {"rid": proxy.uri, "i": i},
                }
                self.tg.send(query)
                i += 1
            for proxy in batch:
                result = self.tg.receive()
                if result:
                    self.handle_result(result)

    def init_telegram(self):
        envvars = dotenv_values()
        tg = TDJson(envvars["LIB_PATH"], 0)
        tg.send(self.mock_params())
        # to keep receiving updates until the
        # expected initial communication ends
        while True:  # ...
            value = tg.receive() or {}
            if value.get("@type") == "updateConnectionState":
                break
        return tg


def main():
    setup_logging()
    proxies = load_proxies()
    mint = Mint()
    try:
        mint.test(proxies, 64)
        mint.results.sort()
        dump_results(mint.results)
    except KeyboardInterrupt:
        pass
    finally:
        mint.tg.stop()


if __name__ == "__main__":
    main()
