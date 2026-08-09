# PyTgProxy

A Python tool for testing and verifying Telegram proxy servers using TDLib's TDJson interface.

## Features
- **No API Credentials Required**: Uses TDJson with mocked parameters + handles native method call order - no Telegram API credentials needed 
   - *more info: `python-telegram`'s own `Telegram` class wouldn't work for this particular purpose at the time of releasing this project*
- Proxy testing with latency measurement
- Batch processing for improved performance
- Proxy list management from online repositories
- Supports SOCKS5, HTTP, and MTProto proxies
- Results export to CSV

## Getting Started
### Prerequisites
- [TDLib](https://core.telegram.org/tdlib) (Telegram Database Library)
  - Follow [the official instructions](https://tdlib.github.io/td/build.html) to compile for your OS
  - Place the compiled library (e.g., `libtdjson.so` on Linux, `libtdjson.dll` on Windows) somewhere you can easily point at, later
- Python 3.12+ (required for `itertools.batched`; the code may work on 3.7+ with a replacement implementation)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/amir-samiee/pytgproxy && cd pytgproxy
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your configuration:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` with your values (see Configuration section below)

## Configuration

Here's how `.env` file should look like (at the project's root):

```ini
LIB_PATH=path/to/libtdjson.so

PROXY_POOLS="https://example.com/some-proxies.txt
https://github.com/other-source/other-proxies.txt"
```

> **Important Note**: The following are example proxy sources that you may use at your own risk. The maintainer of this project takes no responsibility for the reliability, legality, or security of any third-party proxy sources. Always verify proxies before use and comply with all applicable laws in your jurisdiction.

For examples of proxy sources, take a look at:
- [freeproxydb.com](https://freeproxydb.com)
- [/Argh94/Proxy-List](https://github.com/Argh94/Proxy-List)
- [/SoliSpirit/mtproto](https://github.com/SoliSpirit/mtproto)
- [/LoneKingCode/free-proxy-db](https://github.com/LoneKingCode/free-proxy-db)
- [/Grim1313/mtproto-for-telegram](https://github.com/Grim1313/mtproto-for-telegram)
- [/kort0881/telegram-proxy-collector](https://github.com/kort0881/telegram-proxy-collector)

## Usage

### Update Proxy List

Fetch proxies from configured online sources and append them to your local list:

```bash
python main.py --update # or
python main.py -u
```

This will:
- Fetch proxies from all URLs specified in `PROXY_POOLS`
- Append them to `proxies.txt` (creates the file if it doesn't exist)
- Clean and validate the proxy list (removes invalid entries)

### Test Proxies

```bash
python main.py
```

**Examples:**
```bash
# Test with custom proxy file and batch size
python main.py -p my_proxies.txt -b 32

# Test and save results to a new file (overwrite mode)
python main.py -r new_results.csv -m w

# Update proxies and validate with verbose output
python main.py -u -v
```
*execute `python main.py -h` for a full guide on options*

### Proxy File Format

The `proxies.txt` file should contain one proxy URI per line (unrecognized lines would be skipped).
Supported formats:

```
# MTProto
tg://proxy?server=1.2.3.4&port=443&secret=abcdef123456...

# SOCKS5
tg://socks?server=1.2.3.4&port=1080

# SOCKS5 with auth
tg://socks?server=1.2.3.4&port=1080&username=user&password=pass

# HTTP
tg://http?server=1.2.3.4&port=8080

# HTTP with auth
tg://http?server=1.2.3.4&port=8080&username=user&password=pass&http_only=true
```
*NOTE: Ignore the lines starting with `#`s. You don't actually need to separate different protocols.*
## Key Files 
*(Configurable either via `.env` or commandline arguments)*
- `proxies.txt`: List of proxy URIs to test
- `results.csv`: Test results with response times in milliseconds and proxy URIs
  - Format: `response_time_ms,proxy_uri`
  - Only successful tests are saved by default
- `.log`: Application log file with detailed debug information

### Testing Process

1. Proxies are loaded from the specified file
2. They are tested in batches using TDJson's `pingProxy` method
3. Each proxy's response time is measured in milliseconds
4. Results are sorted by response time and saved to CSV
5. Failed proxies are logged with error codes and messages

## License

This project is licensed under the GNU General Public License (GPL) Version 3 (see [LICENSE](LICENSE)).

## Acknowledgments

- [Telegram TDLib](https://github.com/tdlib/td) - Telegram Database Library
- [python-telegram](https://github.com/alexander-akhmetov/python-telegram) - Python bindings for TDLib
- [rich](https://github.com/Textualize/rich) - For prettified console output which makes development unbelievably easier
- [Devin AI from DeepWiki](https://deepwiki.com) - For AI-powered development assistance that made this project possible
- [Devstral by Mistral AI](https://mistral.ai/news/devstral/) - For performing handy tasks such as drafting this very README (except the current line obvi)