# PyTgProxy: Python Telegram Proxy Tester

A Python tool for testing and managing Telegram proxy servers. This utility helps you find and verify working Telegram proxies by pinging them and measuring their response times.

## Features

- **Performance Testing**: Measures ping latency for each proxy
- **Proxy Discovery**: Fetches proxy lists from online repositories
- **Results Export**: Saves test results to CSV for analysis
- **Proxy Types**: Supports SOCKS5, HTTP, and MTProto proxy types
- **Configuration**: Environment-based configuration for keys and setup
- **No-API Mode**: Test proxies without requiring Telegram API credentials

## Installation

### Prerequisites

- [TDLib](https://core.telegram.org/tdlib) (Telegram Database Library)
- Python 3.12+ (tested on 3.13, the primary version restriction is due to itertools.batched function; replace/implement it and 3.7+ should be fine as well)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/telegram-proxy-tester.git
   cd telegram-proxy-tester
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

### For Standard Mode (with API credentials)
Create a `.env` file in the project root with the following variables:

```ini
# Telegram API credentials
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token

# TDLib configuration
LIB_PATH=path/to/libtdjson.so  # e.g., /usr/local/lib/libtdjson.so
FILES_DIR=./tdlib_files
ENCRYPTION_KEY=your_encryption_key

# Proxy configuration
PROXY_POOLS=https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt
```

### For No-API Mode (Demo)
Only requires TDLib configuration:

```ini
# TDLib configuration
LIB_PATH=path/to/libtdjson.so  # e.g., /usr/local/lib/libtdjson.so

# Proxy configuration
PROXY_POOLS=https://raw.githubusercontent.com/SoliSpirit/mtproto/master/all_proxies.txt
```

### Getting Telegram API Credentials (Optional for No-API Mode)

1. Go to [https://my.telegram.org](https://my.telegram.org)
2. Log in with your Telegram account
3. Navigate to "API development tools"
4. Create an application to get your `API_ID` and `API_HASH`

## Usage

### Fetch and Update Proxy List

```bash
python proxy.py
```

This will:
- Fetch proxies from configured online sources
- Append them to `proxies.txt`
- Clean and validate the proxy list

### Test Proxies

#### Standard Mode (with API credentials)
```bash
python main.py
```

This will:
- Load proxies from `proxies.txt`
- Test each proxy's connectivity and response time using Telegram API
- Save results to `results.csv`

#### No-API Mode (without API credentials)
```bash
python noapi.py
```

This will:
- Load proxies from `proxies.txt`
- Test each proxy's connectivity and response time using TDJson directly
- Save results to `results.csv`
- **No Telegram API credentials required**

## Proxy Types Supported

This tool supports the following Telegram proxy types:

1. **SOCKS5**: Standard SOCKS5 proxies
2. **MTProto**: Telegram's native MTProto proxies
3. **HTTP**: HTTP proxies, with optional HTTP-only mode (not tested)

## Output Files

- `proxies.txt`: List of proxy URIs to test
- `results.csv`: Test results with response times (milliseconds, proxy URI)
- `.log`: Application log file

## Development

### Dev Container

This project includes a Dev Container configuration for GitHub Codespaces:

- Uses Ubuntu 20.04 base image
- Automatically installs dependencies

To use:
1. Create a GitHub Codespace and open the project inside it (Recommendation: use vs code and create/connect/manage one via command palette)
2. Click "Reopen in Container" if/when prompted
3. Or use the Remote-Containers extension to rebuild the container

## Implementation Details

### Architecture Overview
The project now offers two testing approaches:

1. **Standard Mode (`main.py`)**:
   - Uses the full `python-telegram` client
   - Requires valid Telegram API credentials
   - Provides complete Telegram client functionality

2. **No-API Mode (`noapi.py`)**:
   - Uses TDJson directly with mocked parameters
   - No API credentials required
   - Lightweight implementation focused solely on proxy testing
   - Uses batch processing for improved performance

## License

This project is licensed under the GNU General Public License (GPL) Version 3.

## Acknowledgments
- [Telegram TDLib](https://github.com/tdlib/td) - Telegram Database Library
- [python-telegram](https://github.com/alexander-akhmetov/python-telegram) - Python bindings for TDLib
- [Rich](https://github.com/Textualize/rich) - For prettified console output which makes development unbelievably easier
- Devin AI from [DeepWiki](https://deepwiki.com) - For AI-powered development assistance that made this project possible
- Devstral by Mistral AI - For performing handy tasks such as drafting this very README (except the current line obvi)