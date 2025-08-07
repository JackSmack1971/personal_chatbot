# User Scenarios — Personal Chatbot with Persistent Memory and File Upload

Version: 1.0  
Status: Approved for Pseudocode

These scenarios describe typical end-to-end flows for a single local user. Each scenario lists preconditions, steps, expected results, and acceptance references.

---

## Scenario 1: First Run and Configuration

### Preconditions
- Fresh repository clone
- Python 3.10+ installed
- No config.json yet

### Steps
1. User runs `pip install -r requirements.txt`.
2. User creates a Supabase project (free tier) and runs `setup/create_tables.sql`.
3. User launches `python main.py`.
4. App detects missing config.json and guides the user to create or auto-generate it with placeholders.
5. User pastes OpenRouter API key and Supabase URL/key into config.json via UI or manual edit.
6. User reloads app.

### Expected Results
- App starts within < 10 seconds.
- UI shows green status for config validation.
- Model selector defaults to `openrouter/horizon-beta`.

### Acceptance References
- Acceptance: 7 (Settings/Configuration), 10 (Installation), 1 (Chat readiness)

---

## Scenario 2: Basic Chat with Streaming

### Preconditions
- Valid OpenRouter API key in config.json
- App is running

### Steps
1. User types a prompt into the input box.
2. User clicks Send.
3. The assistant starts streaming tokens live.
4. The typing indicator shows until completion.

### Expected Results
- User and assistant messages appear in transcript with timestamps.
- Stream updates at sub-second cadence (provider-dependent).
- Conversation is created in Supabase, and messages are persisted.

### Acceptance References
- Acceptance: 1 (Chat & Streaming), 4 (Persistence)

---

## Scenario 3: Model Switching Mid-Session

### Preconditions
- Active conversation with at least one exchange
- App is running

### Steps
1. User opens model dropdown.
2. User selects `anthropic/claude-3.5-sonnet`.
3. User sends a new message.

### Expected Results
- New assistant generation uses the selected model.
- Streaming remains stable.
- The model choice is reflected in the export metadata.

### Acceptance References
- Acceptance: 2 (Model Selection), 6 (Export metadata)

---

## Scenario 4: Drag-and-Drop File Upload (Text/Code)

### Preconditions
- App running; conversation open

### Steps
1. User drags a `.md` and a `.py` file into the chat area.
2. UI validates type and size.
3. Files are stored under `./personal_chatbot/uploads/<conversation_id>/<yyyy-mm>/`.
4. Content is extracted and summarized into a preview snippet.
5. User sends a prompt referencing the files.

### Expected Results
- File badges with names appear attached to the message.
- Preview snippets show (first lines with basic highlighting).
- File records created in Supabase (files table) and linked via message.file_paths.

### Acceptance References
- Acceptance: 3 (Upload & Processing), 4 (Persistence)

---

## Scenario 5: Large File Rejection

### Preconditions
- `max_file_size` in config.json is 50 MB
- App running

### Steps
1. User drops a 120 MB PDF.
2. UI validates size.

### Expected Results
- Upload is rejected with a clear error message stating size limit.
- Chat remains responsive; user can continue.

### Acceptance References
- Acceptance: 3 (Validation), 8 (Resilience)

---

## Scenario 6: Unsupported File Type

### Preconditions
- App running

### Steps
1. User drops an `.exe` file.

### Expected Results
- UI rejects the file type with a clear, non-technical message.
- No disk write occurs for the rejected file.

### Acceptance References
- Acceptance: 3 (Validation), 11 (Data policy)

---

## Scenario 7: Conversation History and Search

### Preconditions
- Several conversations exist with varied topics and files

### Steps
1. User opens the sidebar (Recent Conversations).
2. User types a keyword in the search box (e.g., “budget”).
3. User selects a filtered conversation.

### Expected Results
- Sidebar filters by title/message/file-name match.
- Selected conversation loads instantly, showing full transcript and file links.

### Acceptance References
- Acceptance: 5 (Search), 4 (Load history)

---

## Scenario 8: Smart Conversation Titling

### Preconditions
- New conversation created after first user message

### Steps
1. User sends an initial prompt.
2. Assistant responds.
3. Title is auto-generated based on the first exchange.

### Expected Results
- The conversation title updates from “Untitled” to a short, meaningful title.
- Updated title appears in the sidebar list.

### Acceptance References
- Acceptance: 4 (Smart titling)

---

## Scenario 9: Export Conversation to Markdown

### Preconditions
- Active conversation with files and multiple messages

### Steps
1. User clicks “Export to Markdown”.
2. User checks the `./personal_chatbot/exports/` directory.

### Expected Results
- A markdown file exists with name `<title>-<timestamp>.md`.
- Contents:
  - Metadata header (title, created_at, updated_at, model)
  - Full transcript with roles and timestamps
  - Referenced files list with relative paths

### Acceptance References
- Acceptance: 6 (Export)

---

## Scenario 10: Supabase Temporary Outage

### Preconditions
- Configured Supabase; simulated downtime

### Steps
1. User attempts to send a message.
2. The app attempts to persist conversation/message.

### Expected Results
- Connection retries up to 3 times with backoff.
- If still failing, UI shows persistence warning; chat generation may continue for current session.
- Once Supabase recovers, saving resumes.

### Acceptance References
- Acceptance: 8 (Resilience), 4 (Persistence behavior)

---

## Scenario 11: OpenRouter Transient Failure

### Preconditions
- Valid API key
- Simulate 429/5xx responses

### Steps
1. User sends a message.
2. OpenRouter returns a transient error.

### Expected Results
- App automatically retries up to 2 times with backoff.
- If still failing, show retry button and a helpful message.
- No secret values exposed in UI or logs.

### Acceptance References
- Acceptance: 8 (Error Handling)

---

## Scenario 12: Theme Toggle and Key Visibility

### Preconditions
- App running with default dark theme

### Steps
1. User opens Settings.
2. User toggles to light theme.
3. User toggles API key visibility to unmask briefly, then masks again.

### Expected Results
- Theme switches immediately (or after soft reload).
- API key is masked by default and reveals only on user action.
- No API key is printed to logs.

### Acceptance References
- Acceptance: 7 (Settings/Configuration), 9 (UX)

---

## Scenario 13: Non-Blocking File Parsing

### Preconditions
- App running; conversation open

### Steps
1. User drags a 20MB PDF and 5MB DOCX simultaneously.
2. Parsing runs in the background.
3. User continues chatting while files process.

### Expected Results
- Chat remains responsive.
- Progress/status messages appear for parsing.
- Previews show when ready.

### Acceptance References
- Acceptance: 9 (Performance/UX), 3 (File Processing)

---

## Scenario 14: Clean Exit

### Preconditions
- App running with ongoing conversation and uploaded files

### Steps
1. User stops the app (Ctrl+C or UI stop).
2. App performs graceful shutdown.

### Expected Results
- No corrupted files; in-flight writes are finalized or canceled safely.
- Next start resumes normally.

### Acceptance References
- Acceptance: 11 (Data & Storage), NFR: Operability
