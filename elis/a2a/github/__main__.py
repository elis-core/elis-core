"""
ELIS GitHub A2A server — entrypoint.

Binds to 127.0.0.1:9503.  Never binds to 0.0.0.0.
"""

from elis.a2a.github.server import run

if __name__ == "__main__":
    run(host="127.0.0.1", port=9503)