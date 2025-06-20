# schwab-py-extra

Extras for schwab-py

Download this repository and run (pip install .) from the repository root.
These commands will be accessable after it completes.


Command-Line Utilities
----------------------

Once Schwab-py is installed, the following commands become available on **Linux**, **macOS**, and **Windows**:

* **`schwab-analysis`**
  Run Token function analysis routines against your Schwab account.

* **`schwab-refresh-token`**  
  Automatically refresh your Schwab API token using stored credentials.

* **`schwab-fetch-new-token`**
  Obtain a brand-new API token via the manual OAuth flow. Deletes any existing token file before acquiring a new one.

* **`schwab-setup-env`**
  Interactively create and validate the persistant environment variables required for Schwab API access:

  * `schwab_api_key`
  * `schwab_app_secret`
  * `schwab_callback_url`
  * `schwab_token_path`
    Use `--show` to display current values without prompting.

* **`schwab-package-checker`**
  Verify that all required dependencies and package versions meet Schwab Py’s requirements.

### Usage Examples

* Show current env vars  ```schwab-setup-env --show```
* Set up env vars interactively: ```schwab-setup-env```
* Run analysis: ```schwab-analysis -u```
* Refresh an existing token: ```schwab-refresh-token```
* Fetch a brand-new token: ```schwab-fetch-new-token```
* Check package/dependency versions: ```schwab-package-checker -u```

> **Note**: After running `schwab-setup-env` on Linux/macOS, you may need to `source ~/.bashrc` or `source ~/.zshrc` for changes to take effect in your current shell.


``schwab-py-extra`` is released under the
`MIT license`__.
