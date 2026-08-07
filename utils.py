import csv
from collections.abc import Sequence
from pathlib import Path

from models import Proxy


def load_proxies(path="proxies.txt"):
    path = Path(path)
    uris = path.read_text().splitlines()
    return [proxy for uri in uris if (proxy := Proxy.from_uri(uri))]


def dump_results(results: Sequence[tuple[int, str]], path="results.csv", valid_only=True):
    if valid_only:
        results = [res for res in results if res[0] > 0]
    with open(path, "w") as file:
        writer = csv.writer(file)
        writer.writerows(results)
