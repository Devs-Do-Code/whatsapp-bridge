# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - YYYY-MM-DD

### Added

- Initial release of `whatsapp-bridge`.
- Core functionality for interacting with a personal WhatsApp account via a managed Go bridge (`whatsapp-mcp`).
- Automated setup: Checks for Go/Git prerequisites and clones the `whatsapp-mcp` repository.
- Go bridge process management: Starts and stops the background Go process.
- QR code detection and display for initial WhatsApp authentication.
- Sending text messages (`send_message`).
- Sending media files (images, video, audio, documents) with captions (`send_media`).
- Polling for new incoming messages from the local SQLite database (`get_new_messages`).
- Automatic download of incoming media files (`download_media=True` in `get_new_messages`).
- Manual download trigger for specific media messages (`download_media_manual`).
- Basic bot framework integration (`ApplicationBuilder`, `MessageHandler`, etc. adapted for WhatsApp).
- Custom exception classes (`WhatsappError`, `PrerequisitesError`, `SetupError`, `BridgeError`, `ApiError`, `DbError`).
- Configuration for data directory and connection timeouts.
- Initial project structure, `README.md`, `LICENSE.md` (MPL-2.0), `pyproject.toml`, and basic usage examples.
