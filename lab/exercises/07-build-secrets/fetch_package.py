"""Fetch the company's private billing SDK at build time.

This stands in for `pip install --index-url https://__token__:$PACKAGE_TOKEN@pypi.example.com/`:
it refuses to run without a token, and writes the package when it has one.
"""

import os
import sys
from pathlib import Path

token = os.environ.get("PACKAGE_TOKEN", "")
if not token.startswith("pkg_"):
    sys.exit("fetch_package: PACKAGE_TOKEN is missing or not a package token")

package = Path("vendor/billing_sdk")
package.mkdir(parents=True, exist_ok=True)
(package / "__init__.py").write_text('VERSION = "2.4.1"\n')
print("fetch_package: fetched billing-sdk 2.4.1")
