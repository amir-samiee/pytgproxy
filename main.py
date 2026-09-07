"""more help about the library itself on: https://core.telegram.org/tdlib/docs"""

import logging
from pathlib import Path

from common import dump_rows, dump_uris_from_pools, init_with_args
from models import GenericManager, Mint, Proxy


def main():
    args = init_with_args()
    telemode = not args.use_requests
    if args.update or args.U:
        validator = Proxy.from_uri if telemode else None
        dump_uris_from_pools(args.pools, args.proxies, validator)
        if args.update:
            return

    def handle_call_save(func, post_run, *func_args, **func_kwargs):
        try:
            func(*func_args, **func_kwargs)
        except KeyboardInterrupt:
            logging.warning("exit request received")
        finally:
            logging.info(f"saving the results to {args.out}...")
            post_run()

    uris = Path(args.proxies).read_text().split()
    if telemode:
        proxies = [proxy for uri in uris if (proxy := Proxy.from_uri(uri))]
        mint = Mint(args.tdlib_path)

        def post():
            mint.tg.stop()
            dump_rows(mint.results, args.out, mode=args.method, pingkey=1)

        handle_call_save(mint.test, post, proxies, max_workers=args.max_workers)
    else:
        manager = GenericManager(args.target)
        results = []

        def post():
            rows = [x[:2] for x in results if x]
            dump_rows(rows, args.out, pingkey=1)

        handle_call_save(results.extend, post, manager.ping_proxies(uris))


if __name__ == "__main__":
    main()
