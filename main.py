"""more help on: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1_function.html"""

import argparse
import csv
import logging
from collections.abc import Sequence
from pathlib import Path

import requests
from dotenv import dotenv_values
from rich.logging import RichHandler

from models import *

proxy_pools = (dotenv_values()["PROXY_POOLS"] or "").split()


def fetch_proxies(urls=proxy_pools):
    news = set()
    for i, url in enumerate(urls, 1):
        print(f"fetching resource {i}/{len(urls)}...", end="\r")
        response = requests.get(url)
        if response.ok:
            news.update(response.text.splitlines())
    return news


def refine_proxy_file(filepath, key=len):
    path = Path(filepath)
    proxies = set(path.read_text().splitlines())
    proxies = filter(lambda p: Proxy.from_uri(p), proxies)
    if key:
        proxies = sorted(proxies, key=key)
    path.write_text("\n".join(proxies))


def load_proxies(path="proxies.txt"):
    path = Path(path)
    uris = path.read_text().splitlines()
    return [proxy for uri in uris if (proxy := Proxy.from_uri(uri))]


def dump_results(results: Sequence, path="results.csv", valid_only=True, mode="w"):
    if valid_only:
        results = [res for res in results if res[0] > 0]
    with open(path, mode) as file:
        if mode == "a":
            file.write("\n")
        writer = csv.writer(file)
        writer.writerows(results)


def setup_logging(level=logging.INFO):
    handlers = [
        RichHandler(log_time_format="%X", show_path=False),
        logging.FileHandler(".log", "a"),
    ]
    logging.basicConfig(level=level, handlers=handlers)


def update_proxies(filename="proxies.txt"):
    with open(filename, "a") as file:
        file.write("\n")
        file.write("\n".join(fetch_proxies()))
    refine_proxy_file(filename)


def parse_args():
    # fmt:off
    parser = argparse.ArgumentParser(description="Telegram proxy tester")
    parser.add_argument("-p", "--proxies", default="proxies.txt",
                       help="Path to proxy file")
    parser.add_argument("-r", "--results", default="results.csv",
                       help="Path to results file")
    parser.add_argument("-b", "--batch-size", type=int, default=64,
                       help="Batch size for testing proxies")
    parser.add_argument("-u", "--update", action="store_true",
                       help="Update proxy list from the provided pools and exit")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Enable verbose logging")
    parser.add_argument("-m", "--mode",  default="a", choices=["a", "w"],
                       help="the mode using which to open the output file and \
                       save the results; available options: (a)ppend, over(w)rite")
    return parser.parse_args()
    # fmt:on


def main():
    args = parse_args()

    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    setup_logging(log_level)

    if args.update:
        update_proxies(args.proxies)

    proxies = load_proxies(args.proxies)
    mint = Mint()
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
