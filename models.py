import logging
from dataclasses import dataclass, fields, is_dataclass
from itertools import batched
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from telegram.tdjson import TDJson


@dataclass
class ProxyTypeSocks5:
    username: str = ""
    password: str = ""

    @property
    def type(self):
        return "proxyTypeSocks5"


@dataclass
class ProxyTypeHttp:
    username: str = ""
    password: str = ""
    http_only: bool = False

    @property
    def type(self):
        return "proxyTypeHttp"


@dataclass
class ProxyTypeMtproto:
    secret: str

    @property
    def type(self):
        return "proxyTypeMtproto"


ProxyType = ProxyTypeSocks5 | ProxyTypeHttp | ProxyTypeMtproto

TYPES = {
    "proxy": ProxyTypeMtproto,
    "socks": ProxyTypeSocks5,
    "http": ProxyTypeHttp,
}


@dataclass
class Proxy:
    server: str
    port: int
    type: ProxyType

    @property
    def uri(self):
        return Proxy.to_uri(self)

    @classmethod
    def from_uri(cls, uri: str):
        try:
            parsed = urlparse(uri)

            type_string = parsed.netloc if parsed.scheme == "tg" else parsed.path.partition("/")[-1]
            params = {x: y.pop() for x, y in parse_qs(parsed.query).items()}

            server = params.pop("server")
            port = int(params.pop("port"))
            TYPE = TYPES[type_string]
            valid_keys = [field.name for field in fields(TYPE)]
            valid_params = {k: params[k] for k in valid_keys if k in params}
            type_class = TYPE(**valid_params)
        except BaseException as err:
            logging.debug("an error occurred during conversion: %s", err)
            return None
        return Proxy(server, port, type_class)

    @classmethod
    def to_uri(cls, obj: "Proxy") -> str:
        type_string = None
        for k, v in TYPES.items():
            if isinstance(obj.type, v):
                type_string = k
                break
        assert type_string
        params = {"server": obj.server, "port": str(obj.port)}
        valid_keys = [f.name for f in fields(obj.type)]
        for k in valid_keys:
            params[k] = getattr(obj.type, k)
        query = urlencode(params)
        path = f"/{type_string}"
        return urlunparse(("https", "t.me", path, "", query, ""))


def _resolve_name(obj):
    o_type = obj if isinstance(obj, str) else type(obj).__name__
    o_type = o_type[0].lower() + o_type[1:]
    return o_type


def _asdict(obj):
    if is_dataclass(obj):
        result = {}
        for f in fields(obj):
            result[_resolve_name(f.name)] = _asdict(getattr(obj, f.name))
        result["@type"] = _resolve_name(obj)
        return result
    return obj


class Mint:
    """Mini Telegram Representative Object for TDJson's API, tailored for this specific purpose"""

    @classmethod
    def mock_params(cls):
        return {
            "@type": "setTdlibParameters",
            "api_id": 1,  # type matters
            "files_directory": ".telegram",  # to keep the dir-tree clean
            "system_language_code": "en",
            "device_model": "mock",  # all the provided keys are required
            "application_version": "pock",
            "api_hash": "hock",
            "@extra": {"request_id": "params"},
        }

    def __init__(self, tdlib_path):
        self.tg = self.init_telegram(tdlib_path)
        self.results = []

    @classmethod
    def init_telegram(cls, tdlib_path):
        tg = TDJson(tdlib_path, 0)
        tg.send(cls.mock_params())
        # to keep receiving updates until the
        # expected initial communication ends
        while True:  # ...
            value = tg.receive() or {}
            if value.get("@type") == "updateConnectionState":
                break
        return tg

    def test(self, proxies: list[Proxy], batch_size=64):
        self._tests = proxies
        i = 0
        for batch in batched(proxies, batch_size):
            for proxy in batch:
                query = {
                    "@type": "pingProxy",
                    "proxy": _asdict(proxy),
                    "@extra": {"i": i},
                }
                self.tg.send(query)
                i += 1
            for proxy in batch:
                result = self.tg.receive()
                self.handle_result(result)

    def handle_result(self, result):
        if not (
            result  ##
            and (extra := result.get("@extra"))
            and (i := extra.get("i"))
        ): return  # fmt:off
        # fmt:on

        proxy: Proxy = self._tests[i]
        uri = proxy.uri
        mutual = f"{i:>3}:"

        if result["@type"] == "seconds":
            ms = int(result["seconds"] * 1000)
            logging.info(f"[green]{mutual} %-4d ms %s", ms, uri)
            self.results.append((ms, uri))
        else:
            code, message = map(result.get, ["code", "message"])
            logging.error(f"[red]{mutual} error %3d[/red] %s [dim]%s", code, message, uri)
