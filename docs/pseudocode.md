# Pseudocode — Personal Chatbot with Persistent Memory and File Upload

Version: 1.0  
Status: Implementation-Ready

This document specifies module-level pseudocode for a minimal, reliable MVP aligned with the specification and acceptance criteria.

## Project Structure

```
personal_chatbot/
├── main.py
├── config.json
├── requirements.txt
├── src/
│   ├── chat_ui.py
│   ├── openrouter_client.py
│   ├── memory_manager.py
│   ├── file_handler.py
│   └── utils.py
├── uploads/
├── exports/
└── setup/
    ├── create_tables.sql
    └── install.py
```

---

## main.py

Purpose: Entry point to load config, initialize dependencies, and start Gradio app.

Pseudocode:
```
import json, os
from src.chat_ui import create_app
from src.openrouter_client import OpenRouterClient
from src.memory_manager import MemoryManager
from src.file_handler import FileHandler
from src.utils import validate_config, ensure_dirs, load_env

def load_config(path="config.json") -> dict:
    if not exists(path):
        create default dict with placeholders
        write to path
        print guidance message
        return default dict
    with open(path) as f:
        cfg = json.load(f)
    return cfg

def main():
    cfg = load_config()
    load_env()  # optionally read .env for supabase values
    validation_result = validate_config(cfg)
    if not validation_result.ok:
        print friendly errors; continue but some features may warn in UI

    ensure_dirs(["uploads", "exports"])

    mm = MemoryManager(
        supabase_url=cfg.supabase_url,
        supabase_key=cfg.supabase_key,
        retry=3, backoff= (0.5, 1.0, 2.0)
    )

    fr = FileHandler(
        base_upload_dir="./uploads",
        max_mb=cfg.max_file_size,
        allowed_types=[LIST], preview_chars=2000
    )

    orc = OpenRouterClient(
        api_key=cfg.openrouter_api_key,
        default_model=cfg.default_model,
        retry=2, backoff=(0.5, 1.0),
        timeout=60
    )

    app = create_app(mm, fr, orc, cfg)
    app.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)

if __name__ == "__main__":
    main()
```

---

## src/utils.py

Purpose: Common helpers for validation, backoff, logging, timestamps, filenames, safe JSON.

Pseudocode:
```
def validate_config(cfg) -> ValidationResult:
    required = ["openrouter_api_key", "supabase_url", "supabase_key", "default_model", "max_file_size", "theme"]
    missing = [k for k in required if not cfg.get(k)]
    ok = len(missing) == 0
    return ValidationResult(ok=ok, missing=missing, messages=[...])

def ensure_dirs(paths: list[str]):
    for p in paths:
        os.makedirs(p, exist_ok=True)

def utc_now_iso() -> str:
    return datetime.utcnow().isoformat()

def safe_filename(original_name: str) -> str:
    # strip illegal chars, normalize spaces, add short random suffix

def unique_path(base_dir: str, filename: str) -> str:
    # join, if exists add -1, -2,...

def redact(s: str) -> str:
    # return masked string for secrets

def backoff_delays(base_list: tuple[float]) -> generator:
    # yield delays in sequence

def short_title_from_text(text: str, max_words=10) -> str:
    # derive a short title candidate

def json_dumps_safe(obj) -> str:
    # dumps with ensure_ascii=False, default=str

class ValidationResult:
    ok: bool
    missing: list[str]
    messages: list[str]
```

---

## src/openrouter_client.py

Purpose: Wrap OpenRouter API calls with streaming support and retries.

Pseudocode:
```
import requests, sseclient or httpx (stream)
class OpenRouterClient:
    def __init__(self, api_key, default_model, retry=2, backoff=(0.5, 1.0), timeout=60):
        store args; set session; set headers {"Authorization": f"Bearer {api_key}", "HTTP-Referer": "local", "X-Title": "Personal Assistant"}

    def chat_stream(self, messages: list[dict], model: str|None=None) -> iterator[str]:
        chosen_model = model or self.default_model
        body = {
          "model": chosen_model,
          "messages": messages,
          "stream": True
        }
        for attempt in range(retry+1):
            try:
                with httpx client stream POST to https://openrouter.ai/api/v1/chat/completions:
                    for event chunk:
                        if chunk has content delta:
                            yield token (str)
                return
            except transient_error as e:
                if attempt < retry: sleep(backoff[attempt]); continue
                raise e

    def chat_once(self, messages: list[dict], model=None, max_tokens=None) -> str:
        # Non-streaming fallback if needed; parse response, return text
```

Error handling:
- Map 429/5xx to transient_error
- Surface clean messages; do not include API key in errors.

---

## src/memory_manager.py

Purpose: Encapsulate Supabase CRUD for conversations, messages, files; provide search and recent list.

Pseudocode:
```
from supabase import create_client

class MemoryManager:
    def __init__(self, supabase_url, supabase_key, retry=3, backoff=(0.5, 1.0, 2.0)):
        attempt connect with retries:
            self.client = create_client(url, key)
            on failure, sleep backoff

    # Conversations
    def create_conversation(self, title="Untitled") -> dict:
        insert into conversations returning id, title, timestamps

    def update_conversation_title(self, conversation_id, title):
        update conversations set title, updated_at=now

    def touch_conversation(self, conversation_id):
        update updated_at=now

    def get_recent_conversations(self, limit=50) -> list[dict]:
        select * from conversations order by updated_at desc limit 50

    # Messages
    def add_message(self, conversation_id, role, content, file_paths: list[str]|None, timestamp):
        insert into messages

    def get_messages(self, conversation_id) -> list[dict]:
        select * from messages order by timestamp asc

    # Files
    def add_file_record(self, filename, file_path, file_type, upload_date, conversation_id=None):
        insert into files; could store conversation link implicitly via message.file_paths

    # Search (simple)
    def search_conversations(self, query: str) -> list[dict]:
        # Strategy:
        # 1) title ilike '%q%'
        # 2) messages table content ilike '%q%' to get conversation_ids
        # 3) files filename ilike '%q%' to get conversation_ids (if tracked)
        # union ids and fetch conversations

    # Export
    def export_conversation_markdown(self, conversation_id, out_dir="./exports") -> str:
        fetch conversation, messages
        derive filename from title + timestamp
        write markdown with metadata + transcript + files list
        return path
```

Notes:
- Use UTC timestamps
- Use JSON for file_paths in messages (list of relative paths)
- Optimize queries lightly for free tier

---

## src/file_handler.py

Purpose: Validate uploads, store locally, extract content, and produce previews.

Pseudocode:
```
import mimetypes, pathlib
SUPPORTED_EXTS = {...}  # per spec
MAX_MB default from config

class FileHandler:
    def __init__(self, base_upload_dir, max_mb, allowed_types, preview_chars=2000):
        store

    def conversation_upload_dir(self, conversation_id) -> str:
        ym = current year-month
        path = base_upload_dir / conversation_id / ym
        ensure path exists
        return path

    def validate_file(self, filepath, size_bytes) -> ValidationResult:
        check size <= max_mb * 1024 * 1024
        check extension in SUPPORTED_EXTS
        return result

    def save_uploaded_file(self, file_obj, conversation_id) -> dict:
        # file_obj from gradio upload
        dest_dir = conversation_upload_dir(conversation_id)
        safe = safe_filename(file_obj.name)
        dest_path = unique_path(dest_dir, safe)
        stream copy from file_obj to dest_path
        return { "filename": safe, "path": str(dest_path), "ext": ext, "size": size }

    def extract_content(self, path: str) -> tuple[str, dict]:
        ext = file extension
        if ext in [".txt", ".md", ".py", ".js", ".json", ".yaml", ".yml", ".csv", ".html", ".css", ".sql", ".xml"]:
            read text (with encoding detection fallback)
        elif ext == ".pdf":
            use pypdf or pdfminer/fitz to extract text
        elif ext == ".docx":
            use python-docx to extract text
        elif ext == ".xlsx":
            use openpyxl or pandas to read sheets as CSV-like text summary
        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
            return "[image file]" text placeholder with dimensions (via Pillow)
        else:
            raise UnsupportedType

        meta = { "chars": len(text), "lines": count, "ext": ext }
        return (text, meta)

    def make_preview(self, text: str, limit: int = preview_chars) -> str:
        return first limit chars + "…" if longer

    def cleanup_temp(self, older_than_days=7):
        # iterate temp dirs and remove stale temps
```

---

## src/chat_ui.py

Purpose: Build Gradio Blocks UI wiring OpenRouter, Memory, and Files with streaming.

Pseudocode:
```
import gradio as gr
from typing import Iterator

def create_app(memory: MemoryManager, files: FileHandler, llm: OpenRouterClient, cfg: dict) -> gr.Blocks:
    with gr.Blocks(title="Personal AI Assistant", theme="gradio/{dark_or_light}") as app:
        # State
        state_conversation_id = gr.State(value=None)
        state_messages = gr.State(value=[])   # [{"role": "user"/"assistant", "content": "..."}]
        state_model = gr.State(value=cfg["default_model"])
        state_streaming = gr.State(value=False)
        state_api_key_masked = gr.State(value=True)

        # Top bar: model selector + settings
        with gr.Row():
            model_dd = gr.Dropdown(choices=[...], value=cfg["default_model"], label="Model")
            settings_btn = gr.Button("Settings")

        # Side bar: search + recent conversations (collapsible)
        with gr.Accordion("Conversations", open=False):
            search_box = gr.Textbox(placeholder="Search conversations...")
            convo_list = gr.Dataset(components=[gr.Textbox(label="Title")], headers=["Recent"])

        # Main chat with file drop
        with gr.Row():
            chatbot = gr.Chatbot(height=600, label="Chat", show_copy_button=True, likeable=False, render_markdown=True)
        with gr.Row():
            file_upload = gr.File(file_count="multiple", file_types=[LIST], label="Drop files or click to upload")
        with gr.Row():
            user_input = gr.Textbox(placeholder="Type a message and press Enter", lines=3)
        with gr.Row():
            send_btn = gr.Button("Send")
            export_btn = gr.Button("Export Conversation")
            theme_toggle = gr.Button("Toggle Theme")

        typing_indicator = gr.Markdown(visible=False, value="… model is typing")

        # Functions
        def init_app():
            # load recents
            recents = memory.get_recent_conversations()
            convo_dataset = [[c["title"]] for c in recents]
            return gr.update(value=convo_dataset)

        def new_conversation_if_needed(messages):
            if state_conversation_id.value is None:
                conv = memory.create_conversation("Untitled")
                state_conversation_id.value = conv["id"]
            return state_conversation_id.value

        def handle_files(files_list):
            conv_id = new_conversation_if_needed(state_messages.value)
            attached_paths = []
            previews = []
            for f in files_list:
                # validate and save
                saved = files.save_uploaded_file(f, conv_id)
                valid = files.validate_file(saved["path"], os.path.getsize(saved["path"]))
                if not valid.ok:
                    # show toast/error; continue
                    continue
                text, meta = files.extract_content(saved["path"])
                preview = files.make_preview(text)
                memory.add_file_record(saved["filename"], saved["path"], meta.get("ext"), utc_now_iso(), conv_id)
                attached_paths.append(saved["path"])
                previews.append(f"{saved['filename']}\n```preview\n{preview}\n```")
            # show previews as assistant system note
            if previews:
                state_messages.value.append({"role": "system", "content": "\n\n".join(previews)})
                chatbot_value = [(m["role"], m["content"]) for m in to_pairs(state_messages.value)]
                return chatbot_value

        def send_message(user_text, selected_model):
            conv_id = new_conversation_if_needed(state_messages.value)
            # persist user message
            memory.add_message(conv_id, "user", user_text, file_paths=get_last_attached_paths_if_any(), timestamp=utc_now_iso())
            state_messages.value.append({"role": "user", "content": user_text})

            # stream assistant
            def stream_generator() -> Iterator[str]:
                state_streaming.value = True
                typing_indicator.update(visible=True)
                # build context messages from state_messages (user/assistant/system only)
                msgs = build_openai_style_messages(state_messages.value)
                buffer = ""
                first_token_time = None
                try:
                    for token in llm.chat_stream(messages=msgs, model=selected_model):
                        buffer += token
                        yield buffer
                finally:
                    typing_indicator.update(visible=False)
                    state_streaming.value = False

            # gradio streaming to Chatbot
            assistant_stream = gr.Stream(stream_generator)
            # on stream end, persist assistant
            def finalize_assistant(final_text):
                memory.add_message(conv_id, "assistant", final_text, file_paths=None, timestamp=utc_now_iso())
                # smart title
                if conversation still Untitled:
                    title = short_title_from_text(user_text)
                    memory.update_conversation_title(conv_id, title)
                state_messages.value.append({"role": "assistant", "content": final_text})
                return state_messages.value

            return assistant_stream.then(finalize_assistant)

        # Bindings
        app.load(fn=init_app, outputs=convo_list)
        model_dd.change(fn=lambda m: state_model.update(value=m), inputs=model_dd, outputs=[])

        file_upload.upload(fn=handle_files, inputs=file_upload, outputs=chatbot)
        send_btn.click(fn=send_message, inputs=[user_input, model_dd], outputs=chatbot)
        user_input.submit(fn=send_message, inputs=[user_input, model_dd], outputs=chatbot)
        export_btn.click(fn=lambda: memory.export_conversation_markdown(state_conversation_id.value), outputs=[])

        # Search binding
        def do_search(q):
            results = memory.search_conversations(q or "")
            return [[r["title"]] for r in results]
        search_box.change(fn=do_search, inputs=search_box, outputs=convo_list)

        # Dataset click to load a conversation
        def load_conversation(evt):
            # find conversation by title index; then load messages
            conv = map_event_to_conversation(evt, memory)
            msgs = memory.get_messages(conv["id"])
            state_conversation_id.value = conv["id"]
            state_messages.value = [{"role": m["role"], "content": m["content"]} for m in msgs]
            return format_for_chatbot(state_messages.value)

        convo_list.select(fn=load_conversation, outputs=chatbot)

        # Settings modal (API key visibility, theme)
        # theme_toggle toggles cfg["theme"] in memory/UI (persistence optional in v1)

    return app
```

Helper transforms:
```
def build_openai_style_messages(state_msgs):
    result = []
    for m in state_msgs:
        if m["role"] in ("user","assistant","system"):
            result.append({"role": m["role"], "content": m["content"]})
    return result

def format_for_chatbot(msgs):
    # return list of (user, assistant) pairs or structured gr.Chatbot payload
```

---

## setup/create_tables.sql (outline)

```
create table if not exists conversations (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

create table if not exists messages (
  id uuid primary key default gen_random_uuid(),
  conversation_id uuid references conversations(id) on delete cascade,
  role text check (role in ('user','assistant','system')) not null,
  content text not null,
  file_paths jsonb,
  timestamp timestamp with time zone default now()
);

create table if not exists files (
  id uuid primary key default gen_random_uuid(),
  filename text not null,
  file_path text not null,
  file_type text,
  upload_date timestamp with time zone default now()
);
```

---

## Complexity Hotspots and Choices

- Streaming UI: ensure token buffering and UI updates do not freeze; use Gradio streaming utilities or generator callbacks.
- File parsing: PDF/DOCX/XLSX handled via safe libraries; heavy files parsed asynchronously to avoid blocking UI.
- Search: initial simple SQL ilike filters and join to collect conversation_ids; optimize later if needed.
- Resilience: straightforward retry with capped attempts to keep experience simple.
