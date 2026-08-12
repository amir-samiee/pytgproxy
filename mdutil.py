from pathlib import Path

import clipboard
from dotenv import dotenv_values
from rich import print

from main import parse_args

if __name__ == "__main__":
    args = parse_args(**dotenv_values())
    path = Path(args.results)
    content = path.read_text()
    lines = content.splitlines()
    sep = "\t"
    md = []
    for k, (ping, uri) in enumerate(map(str.split, lines), 1):
        text = f"{ping}ms".center(9, "═")
        md.append(f"[{text}]({uri})")
    result = sep.join(md)
    try:
        clipboard.copy(result)
    except BaseException as err:
        print("\n\nunable to save to clipboard; cause:", err)
        print("printing instead so you can copy it yourself:...\n\n")
        print(result)
        print("copy the above text and", end=" ")
    else:
        print("saved to clipboard.")
    print(
        "paste + send the copied content to telegram's @markdownbot chat to "  ##
        "get a more compact, accessible, and shareable list of proxies"
    )
