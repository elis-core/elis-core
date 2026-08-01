"""
ELIS Advisor A2A server — entrypoint.

Usage (development / smoke-test only):

    /opt/elis/a2a/venv/bin/python -m elis.a2a.advisor

Binds to 127.0.0.1:9500.  Never binds to 0.0.0.0.
Not a production service — no service install performed here.
"""

from elis.a2a.advisor.server import run

if __name__ == "__main__":
    run(host="127.0.0.1", port=9500)
