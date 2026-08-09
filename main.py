"""more help on: https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1_function.html"""

from manager import *
from models import *


def main():
    setup_logging()
    proxies = load_proxies()
    mint = Mint()
    try:
        mint.test(proxies)
        mint.results.sort()
    except KeyboardInterrupt:
        dump_results(mint.results, mode="a")
    finally:
        dump_results(mint.results)
        mint.tg.stop()


if __name__ == "__main__":
    main()
