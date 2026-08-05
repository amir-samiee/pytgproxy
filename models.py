from dataclasses import dataclass, fields, is_dataclass
from typing import Any
from urllib.parse import parse_qs, urlparse


def resolve_name(obj):
    o_type = obj if isinstance(obj, str) else type(obj).__name__
    o_type = o_type[0].lower() + o_type[1:]
    return o_type


def asdict(obj) -> dict[Any, Any]:
    if is_dataclass(obj):
        result = {}
        for f in fields(obj):
            result[resolve_name(f.name)] = asdict(getattr(obj, f.name))
        result["@type"] = resolve_name(obj)
        return result
    return obj


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
    "http": ProxyTypeHttp,
    "proxy": ProxyTypeMtproto,
    "socks": ProxyTypeSocks5,
}


@dataclass
class Proxy:
    server: str
    port: int
    type: ProxyType

    @classmethod
    def from_uri(cls, uri: str):
        parsed = urlparse(uri)

        type_string = parsed.path.partition("/")[-1]
        params = {x: y.pop() for x, y in parse_qs(parsed.query).items()}

        server = params.pop("server")
        port = int(params.pop("port"))
        TYPE = TYPES[type_string]
        valid_keys = [field.name for field in fields(TYPE)]
        valid_params = {k: params[k] for k in valid_keys if k in params}
        type_class = TYPE(**valid_params)

        return Proxy(server, port, type_class)


# ─────────────────────────────────── #


@dataclass
class AddedProxy:
    id: int
    last_used_date: int
    is_enabled: bool
    proxy: Proxy


@dataclass
class AddedProxies:
    proxies: list[AddedProxy]


# ─────────────────────────────────── #


@dataclass
class Seconds:
    seconds: float


# ─────────────────────────────────── #


@dataclass
class AddProxy:
    proxy: Proxy
    enable: bool


@dataclass
class EditProxy:
    proxy_id: int
    proxy: Proxy
    enable: bool


@dataclass
class EnableProxy:
    proxy_id: int


@dataclass
class RemoveProxy:
    proxy_id: int


@dataclass
class PingProxy:
    proxy: Proxy
