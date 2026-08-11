"""more help on: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1_function.html"""

import argparse
import csv
import logging
import random
from collections.abc import Iterable
from pathlib import Path

import requests
from dotenv import dotenv_values
from rich.logging import RichHandler

from models import *


def load_proxies(frags_or_path: str | Iterable) -> list[Proxy]:
    if isinstance(frags_or_path, str):
        frags_or_path = Path(frags_or_path).read_text().split()
    return [proxy for uri in frags_or_path if (proxy := Proxy.from_uri(uri))]


def fetch_proxies(poolurls) -> list[Proxy]:
    frags = set()
    for i, url in enumerate(poolurls, 1):
        print(f"fetching source {i}/{len(poolurls)}", end="\r")
        try:
            response = requests.get(url)
        except KeyboardInterrupt:
            break
        except BaseException as err:
            logging.warning("skipping due to error: %s", err)
            continue
        if response.ok:
            frags.update(response.text.split())
    return load_proxies(frags)


def dump_results(results: list, filepath: str, mode="w", pingkey=None, no_invalids=True):
    if pingkey:
        if no_invalids:
            results = [res for res in results if res[pingkey] > 0]
        results.sort(key=lambda x: x[pingkey])

    with open(filepath, mode) as file:
        delimiter = ",\t"[filepath.endswith(".tsv")]
        writer = csv.writer(file, lineterminator="\n", delimiter=delimiter)
        writer.writerows(results)


def update_proxies(pools, filepath, shuffle=True):
    proxies = [(Proxy.to_uri(x),) for x in fetch_proxies(pools)]
    if shuffle:
        random.shuffle(proxies)
    dump_results(proxies, filepath)


def setup_logging(log_path, level=logging.INFO):
    file_handler = logging.FileHandler(log_path, "a")
    rich_handler = RichHandler(show_path=False, markup=True, show_time=False, show_level=False)
    handlers = [rich_handler, file_handler]
    FORMAT = "%(asctime)s %(levelname)-5s %(message)s"
    logging.basicConfig(level=level, handlers=handlers, format=FORMAT, datefmt="%X")


def parse_args(**defaults):
    # fmt:off
    parser = argparse.ArgumentParser(description="Telegram proxy tester")
    parser.add_argument("-u", "--update",
        action="store_true", default=False,
        help="Update proxy list from the provided pools and exit")
    parser.add_argument("-v", "--verbose",
        action="store_true", default=defaults.get("VERBOSE", False),
        help="Enable verbose logging")
    parser.add_argument("-m", "--mode",
        default=defaults.get("RESULTS_MODE", "a"),
        help="The mode using which to open the output file and save the results; available options: (a)ppend, over(w)rite")
    parser.add_argument("-f", "--file",
        default=defaults.get("PROXY_FILE", "proxies.txt"),
        help="The file containing proxies to be tested (overrides PROXY_FILE in .env)")
    parser.add_argument("-p", "--pools",
        default=defaults.get("PROXY_POOLS",'').split(),
        help="Space-separated URLs for proxy pools (overrides PROXY_POOLS in .env)")
    parser.add_argument("-r", "--results",
        default=defaults.get("RESULTS_FILE", "results.tsv"),
        help="Path to results file")
    parser.add_argument("-l", "--log-path",
        default=defaults.get("LOG_PATH", ".log"),
        help="Path to log file (overrides LOG_PATH in .env)")
    parser.add_argument("-b", "--batch-size",
        type=int, default=defaults.get("BATCH_SIZE", 64),
        help="Batch size for testing proxies")
    parser.add_argument("-t", "--tdlib-path",
        default=defaults.get("TDLIB_PATH", "./libtdjson.so"),
        help="Path to TDLib library (overrides TDLIB_PATH in .env)")
    return parser.parse_args()
    # fmt:on


def main():
    args = parse_args(**dotenv_values())

    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(args.log_path, log_level)

    if args.update:
        update_proxies(args.pools, args.file)
        return

    proxies = load_proxies(args.file)
    mint = Mint(args.tdlib_path)
    try:
        mint.test(proxies, batch_size=args.batch_size)
    except KeyboardInterrupt:
        logging.info("exit request received")
    finally:
        dump_results(mint.results, args.results, mode=args.mode, pingkey=0)
        mint.tg.stop()


if __name__ == "__main__":
    main()
