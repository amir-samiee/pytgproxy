from dataclasses import asdict as _asdict
from dataclasses import dataclass, fields, is_dataclass
from urllib.parse import parse_qs, urlparse

# asdict = _asdict


def type_rename(obj):
    o_type = obj if isinstance(obj, str) else type(obj).__name__
    o_type = o_type[0].lower() + o_type[1:]
    return o_type


def asdict(obj):
    if is_dataclass(obj):
        result = {}
        for f in fields(obj):
            result[type_rename(f.name)] = asdict(getattr(obj, f.name))
        result["@type"] = type_rename(obj)
        return result
    return obj


# def asdict(obj):
#     default = _asdict(obj) if is_dataclass(obj) else obj
#     o_type = type(obj).__name__
#     o_type = o_type[0].lower() + o_type[1:]
#     print(o_type)
#     default["@type"] = o_type
#     for key, value in default.items():
#         if is_dataclass(value):
#             default[key] = asdict(value)
#     return default


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
        type_class = TYPES[type_string](**params)

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


class AddProxy:
    proxy: Proxy
    enable: bool


class EditProxy:
    proxy_id: int
    proxy: Proxy
    enable: bool


class EnableProxy:
    proxy_id: int


class RemoveProxy:
    proxy_id: int


@dataclass
class PingProxy:
    proxy: Proxy
