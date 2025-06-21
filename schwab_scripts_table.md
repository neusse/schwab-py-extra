## Available Commands

After installing `schwab-py-extra` with `pip install .`, the following command-line utilities become available:

| Command | Description | Example Usage |
|---------|-------------|---------------|
| `schwab-analysis` | Run token function analysis routines against your Schwab account | `schwab-analysis -u` |
| `schwab-refresh-token` | Automatically refresh your Schwab API token using stored credentials | `schwab-refresh-token` |
| `schwab-fetch-new-token` | Obtain a brand-new API token via the manual OAuth flow. Deletes any existing token file before acquiring a new one | `schwab-fetch-new-token` |
| `schwab-setup-env` | Interactively create and validate the persistent environment variables required for Schwab API access (`schwab_api_key`, `schwab_app_secret`, `schwab_callback_url`, `schwab_token_path`) | `schwab-setup-env` |
| `schwab-setup-env --show` | Display current environment variable values without prompting for changes | `schwab-setup-env --show` |
| `schwab-package-checker` | Verify that all required dependencies and package versions meet Schwab Py's requirements | `schwab-package-checker -u` |

### Quick Start Examples

```bash
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