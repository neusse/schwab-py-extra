schwab-py-extra
---------------

Join my Discord:  https://discord.gg/bgzXwqRH


# Extras for schwab-py

Quick start:

These utils support both windows, macos and linux.  so paths etc should comply with your os. Once schwab-py-extra is installed all commands should run as any other executible in your path.  

1. Get schwab-py installed (pip install -U schwan-py)
2. Download or clone this repository.
3. From the root of this repository (/schwab-py-extra) install this python package.  (pip install .)
4. Once installed run the environment setup, you need the bellow list. The setup command is (schwab-setup-env). follow the prompts and it will handle setting up your environment variables. (windows or linux)
   * api_key
   * app_secret
   * callback from your app as regisered on the schwab web site (ie. HTTPS://127.0.0.1:8182/)
   * path to your token to be created (ie. /home/neusse/token.json)
5. Create a token. This will run the manual flow. If it works we are all good to go. (schwab-fetch-new-token) follow directions.
6. Test the token by running the analysis. It will look at some token values and packges then get a quote for TSLA. (schwab-py-analysis -u)

If all is good.  you should see the quote in the output.  If not help is available on the schwab-py discord or my discord.

Good Luck!

I will be adding some example code for the new folks to get you going.  also take a look at all the code in this repository. 

-------

There will be support for 3 data sources.  the Schwab-py API, Alpaca API and yfinance API.
Comand-line utilities that interact with a particular API will begin with that API name. (ie. yf-gapper-screener)

## Available Commands

After installing `schwab-py-extra` with `pip install .`, the following command-line utilities become available:

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `schwab-dividends-calener` | Print a dividend calender for the last year of your current positions | `schwab-dividend-calendar` |
| `schwab-positions-monitor` | A continualy updating posistion display | `schwab-positions-monitor -w` |
| `schwab-portfolio-analyzer` | Back test your current posistions with charts and reports | `schwab-portfolio-analyzer` | 
| `schwab-py-analysis` | Run health analysis routines against your Schwab-py install and token | `schwab-py-analysis -u` |
| `schwab-refresh-token` | Manually force refresh of your Schwab API token using stored credentials | `schwab-refresh-token` |
| `schwab-fetch-new-token` | Obtain a brand-new API token via the manual OAuth flow. Deletes any existing token file before acquiring a new one | `schwab-fetch-new-token` |
| `schwab-setup-env` | Interactively create and validate the persistent environment variables required for Schwab API access (`schwab_api_key`, `schwab_app_secret`, `schwab_callback_url`, `schwab_token_path`) | `schwab-setup-env` |
| `schwab-setup-env --show` | Display current environment variable values without prompting for changes | `schwab-setup-env --show` |
| `schwab-package-checker` | Verify that all required dependencies and package versions meet Schwab Py's requirements | `schwab-package-checker -u` |
| `yf-gapper-screener` | Uses yahoo screen function for fast screening finding overnight price gaps. | `see program for options` |
| `yf-dividend-screener` | Filters for healthy stocks with high dividens.  All markets | `yf-dividend-screener` |



### Quick Start Examples

```bash
# display your portfolio
schwab-portfolio-analyzer

# Set up environment variables interactively
schwab-setup-env

# Show current environment variables
schwab-setup-env --show

# Run analysis with updates
schwab-analysis -u

# Refresh an existing token
schwab-refresh-token

# Fetch a brand-new token
schwab-fetch-new-token

# Check package and dependency versions
schwab-package-checker -u
```

> **Note:** After running `schwab-setup-env` on Linux/macOS, you may need to run `source ~/.bashrc` or `source ~/.zshrc` for changes to take effect in your current shell.
