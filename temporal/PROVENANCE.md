# Temporal Binary Provenance

Recorded as tracked metadata per PO correction (2026-08-16). The binary itself
(`/home/samurai/temporal/bin/temporal`, 132MB) is deliberately NOT committed to
this repository (see `.gitignore`) — it is a downloaded third-party release
artifact, not source this project owns. These facts are committed instead.

- **Version**: Temporal CLI v1.8.2 (bundled Server 1.31.2, bundled Web UI 2.50.1)
- **Source**: official `temporalio/cli` GitHub releases
- **Platform variant used on this host**: `temporal_cli_1.8.2_linux_amd64.tar.gz`
- **SHA-256 (linux_amd64, the variant installed)**:
  `d8421bda989e6514b4bdb4d63a9012a8a05a806892e881a5aad8510496349a94`
- **Verification result**: computed SHA-256 of the downloaded archive matched
  the published checksum exactly before extraction. Full checksum manifest for
  all platform variants preserved at `/home/samurai/temporal/bin/checksums.txt`
  (not under this repo — lives alongside the binary under
  `/home/samurai/temporal/bin/`, outside `app/`).
- **License**: MIT (preserved alongside the binary at
  `/home/samurai/temporal/bin/LICENSE`).
- **Install location**: `/home/samurai/temporal/bin/temporal` (user-space,
  no root used).
