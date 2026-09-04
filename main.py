"""more help on: https://core.telegram.org/tdlib/docs"""

import logging
import random
from collections.abc import Iterable
from pathlib import Path

from common import *
from models import *


def proxies_from_uris(frags_or_path: str | Iterable[str]) -> list[Proxy]:
    if isinstance(frags_or_path, str):
        frags_or_path = Path(frags_or_path).read_text().split()
    return [proxy for uri in frags_or_path if (proxy := Proxy.from_uri(uri))]


def update_proxies(pools, filepath, shuffle=True):
    proxies = [(proxy,) for proxy in fetch_uris(pools, Proxy.from_uri)]
    if shuffle:
        random.shuffle(proxies)
    dump_rows(proxies, filepath)


def main():
    args = common()
    if args.update or args.U:
        update_proxies(args.pools, args.file)
    if args.update:
        return

    proxies = proxies_from_uris(args.file)
    mint = Mint(args.tdlib_path)
    try:
        mint.test(proxies, batch_size=args.batch_size)
    except KeyboardInterrupt:
        logging.info("exit request received")
    finally:
        mint.tg.stop()
        logging.info(f"saving the results to {args.results}...")
        dump_rows(mint.results, args.results, mode=args.mode, pingkey=1)


if __name__ == "__main__":
    main()
