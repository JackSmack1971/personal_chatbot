# Personal Chatbot — Project Skeleton

This is the initial project skeleton per the approved specifications. It contains:
- requirements.txt with pinned dependencies
- Planned folder structure (to be populated in implementation phase)

## Structure (planned)

```
personal_chatbot/
├── main.py                 # Entry point (to be implemented)
├── config.json             # Local configuration (to be created by setup/install.py or manually)
├── requirements.txt        # Pinned dependencies
├── src/
│   ├── chat_ui.py          # Gradio interface (to be implemented)
│   ├── openrouter_client.py# OpenRouter API client (to be implemented)
│   ├── memory_manager.py   # Supabase integration (to be implemented)
│   ├── file_handler.py     # File processing (to be implemented)
│   └── utils.py            # Helper functions (to be implemented)
├── uploads/                # Local file storage (created at runtime)
├── exports/                # Conversation exports (created at runtime)
└── setup/
    ├── create_tables.sql   # Supabase schema (to be added next)
    └── install.py          # Quick setup script (to be added next)
```

## Quick Start (after implementation)
1) Create and activate a virtual environment.
2) Install dependencies:
```
pip install -r requirements.txt
```
3) Create a Supabase project, run SQL from `setup/create_tables.sql`.
4) Create `config.json` with your keys (or run `setup/install.py` once it exists).
5) Run the app:
```
python main.py
```

Refer to docs/ in the repository root for specifications, architecture, and integration details.