"""
elis.a2a — ELIS A2A adapter built on the official a2a-sdk.

Provides the official Google A2A SDK integration for ELIS agent-to-agent
communication. The ``advisor`` sub-package exposes the ELIS Advisor A2A
server; the ``supervisor`` sub-package exposes the ELIS Supervisor A2A
server; the ``pm`` sub-package exposes the PM→Advisor client scaffold.

This package intentionally does NOT define a custom ``a2a`` top-level module
or any non-standard protocol binding. All public types are consumed from the
official ``a2a-sdk`` package installed in the runtime venv at
``/opt/elis/a2a/venv``.
"""
