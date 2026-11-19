import argparse
import csv
import logging
import random
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter
from typing import Any

import dotenv
import requests
from rich.logging import RichHandler
from urllib3.util import parse_url


def is_generic(uri: str):
    """specifies whether a uri can be a non-telegram-specific proxy or not"""
    return not any(tg_schema in uri for tg_schema in ["tg://", "t.me/"])


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
    # FORMAT = "%(asctime)s %(levelname)-5s %(message)s %(filename)s:%(lineno)s"
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


def _parse_args():
    # TODO: once for always resolve this passed (and unpassed) parameters
    # e = anything from .env
    # a = anything from args
    # r = anything required (in case not set)
    # r | e | a
    # TODO: update readme and .env.example
    # fmt:off
    parser = argparse.ArgumentParser(
        description="Telegram proxy tester (and also other proxy types)"
    )
    parser.add_argument("-l", "--logfile", help="Path to log file (overrides `logfile` in .env)")
    parser.add_argument("-m", "--method", choices="aw", help="Method using which to open the output file and update the results")
    parser.add_argument("-o", "--out", help="Path to output (results) file")
    parser.add_argument("-p", "--proxyfile", help="File containing proxies to be tested (overrides `proxyfile` in .env)")
    parser.add_argument("-P", "--pools", nargs="+", help="Whitespace-separated URLs for proxy pools (overrides `pools` in .env); optionally you can add a literal # followed by a protocol (e.g. http, socks5) to add all proxies from that pool with the identified protocol")
    # parser.add_argument("-r", "--use-requests", default=False, help="Test proxies the regular way (using requests module) and not with TDLib, also works with a variety of proxy types other than Telegram-specific ones", action="store_true")
    parser.add_argument("-t", "--tdlib-path", help="Path to TDLib binary (overrides `tdlib-path` in .env)")
    parser.add_argument("-T", "--target", help="Target URL to test proxies against")
    parser.add_argument("-u", "--update", help="Update proxy list from the provided pools and exit", action="store_true")
    parser.add_argument("-U", "--update-run", help="Similar to -u but also runs the program as usual after the update, instead of exiting", action="store_true")
    parser.add_argument("-v", "--verbose", help="Enable verbose logging", action="store_true")
    parser.add_argument("-w", "--max-workers", type=int, help="Batch size for testing proxies")
    return parser.parse_args()
    # fmt:on


def handle_clargs():
    """mutual initialization code"""
    from_dotenv = {k: v for k, v in dotenv.dotenv_values().items() if v}
    from_args = {k: v for k, v in _parse_args().__dict__.items() if v is not None}
    required_defaults = {
        "logfile": ".log",
        "tdlib_path": "tdjson.dll",
        "proxyfile": "proxies.txt",
        "max-workers": 20,
        "method": "w",
    }
    config = required_defaults | from_dotenv | from_args
    setup_logging(config["logfile"], logging.DEBUG if config.get("verbose") else logging.INFO)
    target = config.get("target")
    if not config.get("out"):
        no_ext = parse_url(target).host if target else "tg_proxies"
        config["out"] = f"{no_ext}.tsv"
    config["pools"] = config.setdefault("pools", "").split()
    return config


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
            message = "[yellow]canceling pending futures and awaiting running works..."
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
