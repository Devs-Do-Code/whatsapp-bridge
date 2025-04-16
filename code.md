whatsapp_pkg_project/
├── pyproject.toml # Build system, dependencies, package metadata
├── README.md # Documentation for users
├── LICENSE # Your chosen license (e.g., MIT)
└── src/
└── shubh_whatsapp/ # This is the actual package source directory
├── **init**.py # Main package entrypoint, exports WhatsappClient
├── client.py # Contains the main WhatsappClient class
├── bridge.py # Manages starting/stopping the Go bridge process
├── config.py # Handles configuration, paths, dependency checks
├── db_reader.py # Reads data from the messages.db
├── api_client.py # Communicates with the Go bridge's REST API
├── exceptions.py # Custom exception classes
└── resources/ # Directory placeholder (Go code will be cloned here)
└── .gitkeep # Empty file to ensure directory is tracked by git
if needed
