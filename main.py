"""more help about the library itself on: https://core.telegram.org/tdlib/docs"""

import logging
from pathlib import Path

from common import dump_rows, dump_uris_from_pools, handle_clargs, is_generic
from models import GenericManager, Mint, Proxy


def main():
    args = handle_clargs()
    # import rich

    # rich.print(args)
    target = args.get("target")
    telemode = not target
    and_run = args.get("update_run")
    if args.get("update") or and_run:
        validator = Proxy.from_uri if telemode else is_generic
        dump_uris_from_pools(args["pools"], args["proxyfile"], validator)
        if not and_run:
            return

    def main_flow_wrapper(func, post_run, *func_args, **func_kwargs):
        try:
            func(*func_args, **func_kwargs)
        except KeyboardInterrupt:
            logging.warning("exit request received")
        finally:
            logging.info(f"saving the results to {args['out']}...")
            post_run()
            logging.info("saved successfully...")

    uris = Path(args["proxyfile"]).read_text().split()
    if telemode:
        proxies = [proxy for uri in uris if (proxy := Proxy.from_uri(uri))]
        mint = Mint(args["tdlib-path"])

        def post():
            dump_rows(mint.results, args["out"], mode=args["method"], pingkey=1)
            mint.tg.stop()

        main_flow_wrapper(mint.test, post, proxies, max_workers=args["max-workers"])
    else:
        manager = GenericManager(target)
        results = []

        def post():
            rows = [x[:2] for x in results if x]
            dump_rows(rows, args["out"], pingkey=1)

        main_flow_wrapper(results.extend, post, manager.ping_proxies(uris))
    # print("\n".join(Path(args["out"]).read_text().splitlines()))
    out = Path(args["out"]).read_text()
    for line in out.splitlines():
        print(line.split(maxsplit=1)[0])


if __name__ == "__main__":
    main()
