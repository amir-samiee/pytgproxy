import argparse
import csv
import logging
import random
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter
from typing import Any

import requests
from dotenv import dotenv_values
from rich.logging import RichHandler


def fetch_uris(pools, validator: Callable[[Any], bool] | None = None, normalize=True) -> list[str]:
    fragments = set()
    uris = []
    for i, url in enumerate(pools, 1):
        print(f"fetching source {i}/{len(pools)}", end="\r")
        try:
            response = requests.get(url)
        except KeyboardInterrupt:
            break
        except Exception as err:
            logging.warning("skipping due to error: %s", err)
            continue
        if response.ok:
            fetched = response.text.split()
            if validator:
                fetched = filter(validator, fetched)
            if normalize:
                url, _, proto = url.partition("#")
                fetched = (resolve_schema(uri, proto) for uri in fetched)
            uris.extend(frg for frg in fetched if frg not in fragments)
            fragments.update(fetched)
    return uris


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
    rich_handler = RichHandler(
        show_path=False,
        markup=True,
        show_time=True,
        show_level=True,
    )
    handlers = [rich_handler, file_handler]
    # FORMAT = "%(asctime)s %(levelname)-5s %(message)s"
    FORMAT = "%(message)s"
    logging.basicConfig(level=level, handlers=handlers, format=FORMAT, datefmt="%X")


def resolve_schema(uri: str, schema: None | str = "http"):
    uri = uri.strip()
    if "://" not in uri and schema:
        uri = f"{schema}://{uri}"
    return uri


def dump_uris_from_pools(pools, filepath, validator=None, normalize=True, shuffle=True):
    uris = [uri for uri in fetch_uris(pools, validator)]
    if normalize:
        uris = [resolve_schema(uri) for uri in uris]
    if shuffle:
        random.shuffle(uris)
    uris = [(uri,) for uri in uris]
    dump_rows(uris, filepath)


def parse_args(**defaults):
    # fmt:off
    parser = argparse.ArgumentParser(description="Telegram proxy tester (and also other proxy types)")
    parser.add_argument("-l", "--logfile", default=defaults.get("LOG_PATH", ".log"), help="Path to log file (overrides LOG_PATH in .env)")
    parser.add_argument("-m", "--method", default=defaults.get("UPDATE_METHOD", "a"), choices="aw", help="Method using which to open the output file and update the results")
    parser.add_argument("-o", "--out", default=defaults.get("RESULTS_FILE", "results.tsv"), help="Path to output (results) file")
    parser.add_argument("-p", "--proxies", default=defaults.get("PROXY_FILE", "proxies.txt"), help="File containing proxies to be tested (overrides PROXY_FILE in .env)")
    parser.add_argument("-P", "--pools", default=defaults.get("PROXY_POOLS",'').split(), help="Space-separated URLs for proxy pools (overrides PROXY_POOLS in .env); optionally you can add a literal # followed by a protocol (e.g. http, socks5) to add all proxies from that pool with the identified protocol")
    parser.add_argument("-r", "--use-requests", default=False, help="Test proxies the regular way (using requests module) and not with TDLib, also works with a variety of proxy types other than Telegram-specific ones", action="store_true")
    parser.add_argument("-t", "--tdlib-path", default=defaults.get("TDLIB_PATH", "./libtdjson.so"), help="Path to TDLib binary (overrides TDLIB_PATH in .env)")
    parser.add_argument("-T", "--target", default=defaults.get("TARGET_URL", "https://1.1.1.1"), help="Target URL to test proxies against")
    parser.add_argument("-u", "--update", default=False, help="Update proxy list from the provided pools and exit", action="store_true")
    parser.add_argument("-U", default=False, help="Similar to -u but also runs the program as usual after the update, instead of exiting", action="store_true")
    parser.add_argument("-v", "--verbose", default=defaults.get("VERBOSE", False), help="Enable verbose logging", action="store_true")
    parser.add_argument("-w", "--max-workers", type=int, default=defaults.get("BATCH_SIZE", 32), help="Batch size for testing proxies")
    return parser.parse_args() 
    # fmt:on


def init_with_args(**kwargs):
    """mutual initialization code"""
    defaults = {k: v for k, v in dotenv_values().items() if v}
    args = parse_args(**defaults)

    log_level = kwargs.get("log_level", logging.DEBUG if args.verbose else logging.INFO)
    setup_logging(args.logfile, log_level)

    return args


def handle_threading(proxies, submitter, max_workers=64):
    """
    given an iterable of proxies and a tester (submitter) function which
    provides implementation of the proxy testing for a single proxy,
    creates a pool of threads and handles the threading part of testing

    for best results, use:
    ```
    results = []
    try:
        results.extend(handle_threading(proxies, submitter))
    except KeyboardInterrupt:
        ...
    except Exception as exception:
        ...  # (rest of handling)
    ```

    NOTE: the elements of proxies and the single argument of the
    submitter can be of any type, as long as they're type-compatible
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(submitter, proxy) for proxy in proxies]
        try:
            for future in as_completed(futures):
                yield future.result()
        except KeyboardInterrupt:
            message = "[yellow] canceling pending futures and awaiting running works..."
            logging.warning(message, extra={"markup": True})
            raise
        finally:
            executor.shutdown(cancel_futures=True)


def ping_url(url, do_raise=False, **kwargs):
    try:
        start = perf_counter()
        requests.get(url, **kwargs)
    except Exception:
        if do_raise:
            raise
        return 0
    else:
        return int((perf_counter() - start) * 1000)
