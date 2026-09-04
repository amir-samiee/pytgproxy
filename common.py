import argparse
import csv
import logging
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests
from dotenv import dotenv_values
from rich.logging import RichHandler


def fetch_uris(poolurls, validator: Callable[[Any], bool] | None = None):
    fragments = set()
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
            fetched = response.text.split()
            fragments.update(filter(validator, fetched) if validator else fetched)
    return list(fragments)  # returning list for ease of use


def dump_rows(results: Iterable, filepath: str, mode="w", pingkey=None, no_invalids=True):
    results = list(results)
    if pingkey is not None:
        if no_invalids:
            results = [res for res in results if res[pingkey] > 0]
        results.sort(key=lambda x: x[pingkey])

    with open(filepath, mode) as file:
        delimiter = ",\t"[filepath.endswith(".tsv")]
        writer = csv.writer(file, lineterminator="\n", delimiter=delimiter)
        writer.writerows(results)


def setup_logging(log_path, level=logging.INFO):
    file_handler = logging.FileHandler(log_path, "a")
    rich_handler = RichHandler(show_path=False, markup=True, show_time=False, show_level=False)
    handlers = [rich_handler, file_handler]
    FORMAT = "%(asctime)s %(levelname)-5s %(message)s"
    logging.basicConfig(level=level, handlers=handlers, format=FORMAT, datefmt="%X")


def parse_args(**defaults):
    # fmt:off
    parser = argparse.ArgumentParser(description="Telegram proxy tester")
    parser.add_argument("-U",
        action="store_true", default=False,
        help="similar to -u but also runs the program as usual after the update, instead of exiting")
    parser.add_argument("-u", "--update",
        action="store_true", default=False,
        help="Update proxy list from the provided pools and exit")
    parser.add_argument("-v", "--verbose",
        action="store_true", default=defaults.get("VERBOSE", False),
        help="Enable verbose logging")
    parser.add_argument("-m", "--mode",
        default=defaults.get("MODE", "t"), choices="ta",
        help="run mode; select t to test telegram proxies (requires TDLib binary), otherwise a for any proxy type")
    parser.add_argument("-M", "--method",
        default=defaults.get("UPDATE_METHOD", "a"), choices="aw",
        help="The method using which to open the output file and update the results")
    parser.add_argument("-p", "--proxies",
        default=defaults.get("PROXY_FILE", "proxies.txt"),
        help="The file containing proxies to be tested (overrides PROXY_FILE in .env)")
    parser.add_argument("-P", "--pools",
        default=defaults.get("PROXY_POOLS",'').split(),
        help="Space-separated URLs for proxy pools (overrides PROXY_POOLS in .env)")
    parser.add_argument("-o", "--out",
        default=defaults.get("RESULTS_FILE", "results.tsv"),
        help="Path to output (results) file")
    parser.add_argument("-l", "--logfile",
        default=defaults.get("LOG_PATH", ".log"),
        help="Path to log file (overrides LOG_PATH in .env)")
    parser.add_argument("-w", "--max-workers",
        type=int, default=defaults.get("BATCH_SIZE", 32),
        help="Batch size for testing proxies")
    parser.add_argument("-t", "--tdlib-path",
        default=defaults.get("TDLIB_PATH", "./libtdjson.so"),
        help="Path to TDLib binary (overrides TDLIB_PATH in .env)")
    return parser.parse_args()
    # fmt:on


def init_with_args():
    """mutual initialization code"""
    defaults = {k: v for k, v in dotenv_values().items() if v}
    args = parse_args(**defaults)

    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(args.log_path, log_level)

    return args


def handle_threading(proxies, submitter, max_workers=64):
    """
    given an iterable of proxies and a tester (submitter) function which
    provides implementation of the proxy testing for a single proxy,
    creates a pool of threads and handles the threading part of testing

    NOTE: the elements of proxies and the single argument of the
    submitter can be of any type, as long as they're type-compatible
    """
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(submitter, proxy) for proxy in proxies]
        try:
            for future in as_completed(futures):
                results.append(future.result())
        except KeyboardInterrupt:
            message = "[yellow] canceling pending futures and awaiting running works..."
            logging.warning(message, extra={"markup": True})
            raise
        else:
            return results
        finally:
            executor.shutdown(cancel_futures=True)
