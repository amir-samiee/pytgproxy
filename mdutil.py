from pathlib import Path

import clipboard
from dotenv import dotenv_values
from rich import get_console
from rich.markdown import Markdown

from common import parse_args

if __name__ == "__main__":
    args = parse_args(**dotenv_values())
    path = Path(args.results)
    content = path.read_text()
    lines = content.splitlines()
    sep = "\t"
    md = []
    for k, (uri, ping) in enumerate(map(str.split, lines), 1):
        text = f"{ping}ms".center(9, "═")
        md.append(f"[{text}]({uri})")
    result = sep.join(md)

    console = get_console()
    try:
        clipboard.copy(result)
    except BaseException as err:
        console.print("\n\nunable to save to clipboard; cause:", err)
        console.print("printing instead so you can copy it yourself:...\n\n")
        console.print(Markdown(f"`{result}`"), soft_wrap=True)
        console.print("copy the above text and", end=" ")
    else:
        console.print("saved to clipboard.")
    console.print(
        "paste + send the copied content to any telegram markdown-rendering bot (e.g. "
        "@mdeditorbot) to get a more compact, accessible, and shareable list of proxies"
    )
