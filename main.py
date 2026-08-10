"""more help on: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1_function.html"""

import argparse
import csv
import logging
import random
from collections.abc import Sequence
from pathlib import Path

import requests
from dotenv import dotenv_values
from rich.logging import RichHandler

from models import *

envvars: dict = dotenv_values()


def fetch_proxies(urls=None):
    urls = urls or envvars.get("PROXY_POOLS", "").split()
    news = set()
    for i, url in enumerate(urls, 1):
        print(f"fetching resource {i}/{len(urls)}...", end="\r")
        response = requests.get(url)
        if response.ok:
            news.update(response.text.splitlines())
    return news


def refine_proxy_file(filepath, shuffle=True):
    path = Path(filepath)
    uniques = set(path.read_text().splitlines())
    proxies = [u for u in uniques if Proxy.from_uri(u)]
    if shuffle:
        random.shuffle(proxies)
    path.write_text("\n".join(proxies))


def load_proxies(path):
    path = Path(path)
    uris = path.read_text().splitlines()
    return [proxy for uri in uris if (proxy := Proxy.from_uri(uri))]


def dump_results(results: Sequence, path, mode, valid_only=True):
    if valid_only:
        results = [res for res in results if res[0] > 0]
    with open(path, mode) as file:
        if mode == "a":
            file.write("\n")
        writer = csv.writer(file)
        writer.writerows(results)


def setup_logging(log_path, level=logging.INFO):
    file_handler = logging.FileHandler(log_path, "a")
    rich_handler = RichHandler(show_path=False, markup=True, show_time=False, show_level=False)
    handlers = [rich_handler, file_handler]
    FORMAT = "%(asctime)s %(levelname)5s %(message)s"
    logging.basicConfig(level=level, handlers=handlers, format=FORMAT, datefmt="%X")


def update_proxies(filename="proxies.txt"):
    with open(filename, "a") as file:
        file.write("\n")
        file.write("\n".join(fetch_proxies()))
    refine_proxy_file(filename)


def parse_args():
    # fmt:off
    parser = argparse.ArgumentParser(description="Telegram proxy tester")
    parser.add_argument("-u", "--update",
        action="store_true", default=False,
        help="Update proxy list from the provided pools and exit")
    parser.add_argument("-v", "--verbose",
        action="store_true", default=envvars.get("VERBOSE", False),
        help="Enable verbose logging")
    parser.add_argument("-m", "--mode",
        default=envvars.get("RESULTS_MODE", "a"),
        help="The mode using which to open the output file and save the results; available options: (a)ppend, over(w)rite")
    parser.add_argument("-p", "--proxies",
        default=envvars.get("PROXY_FILE", "proxies.txt"),
        help="Space-separated URLs for proxy pools (overrides PROXY_POOLS in .env)")
    parser.add_argument("-r", "--results",
        default=envvars.get("RESULTS_FILE", "results.csv"),
        help="Path to results file")
    parser.add_argument("-l", "--log-path",
        default=envvars.get("LOG_PATH", ".log"),
        help="Path to log file (overrides LOG_PATH in .env)")
    parser.add_argument("-b", "--batch-size",
        type=int, default=envvars.get("BATCH_SIZE", 64),
        help="Batch size for testing proxies")
    parser.add_argument("-t", "--tdlib-path",
        default=envvars.get("TDLIB_PATH", "./libtdjson.so"),
        help="Path to TDLib library (overrides TDLIB_PATH in .env)")
    return parser.parse_args()
    # fmt:on


def main():
    args = parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(args.log_path, log_level)

    if args.update:
        update_proxies(args.proxies)
        return

    proxies = load_proxies(args.proxies)
    mint = Mint(args.tdlib_path)
    try:
        mint.test(proxies, batch_size=args.batch_size)
        mint.results.sort()
    except KeyboardInterrupt:
        logging.info("exit request received")
    finally:
        dump_results(mint.results, path=args.results, mode=args.mode)
        mint.tg.stop()


if __name__ == "__main__":
    main()
