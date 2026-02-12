# Progressive development plan

## 1. Goal

Build a minimal, local-first CLI for text-to-image and image-to-image, then add a clean, modern PySide6 GUI with clear milestones.

## 2. Principles

- Minimal commands first: prompt + output path should work.
- Backward compatible changes in later phases.
- Observable behavior: verbose logs and clear errors.
- Local-first: no service or UI dependencies.
- GUI built on PySide6 with a clean, modern visual style.

## 3. PySide6 technical route

Architecture:

- `core/`: API client, polling, file IO, mode switching.
- `cli/`: argument parsing, command execution.
- `gui/`: PySide6 app, views, and state.

UI structure:

- Left panel: prompt input, image upload, model and format.
- Right panel: preview, output path, status and logs.
- Bottom bar: generate, cancel, open output folder.

GUI requirements:

- Clean, modern layout with clear spacing and typography.
- Responsive layout for small screens.
- Non-blocking generation using background threads.
- Status indicator for creating, polling, and saving.
- Error banner with actionable messages.
- Default values aligned with CLI defaults.

## 4. Phases and milestones

### Phase 0: Foundation

Scope:

- Confirm Python + Pipenv setup.
- Verify API key loading from `GPTSAPI_API_KEY`.
- Ensure `main.py` runs with basic text-to-image.

Deliverables:

- Documented setup steps and example command.
- Basic success and failure logging.

Acceptance checks:

- Command runs: `pipenv run python main.py "test" --out ./output/test.png`.
- Missing API key gives readable error.

### Phase 1: Minimal text-to-image (MVP)

Scope:

- CLI parameters: `prompt`, `--out`, `--format`, `--aspect`, `--model`, `--provider`.
- API request creation + polling until completion.
- Save output image to local file.

Deliverables:

- Stable output file handling.
- Basic verbose mode.

Acceptance checks:

- Output file exists and is non-empty.
- Invalid model or request shows readable error.

### Phase 2: Auto image-to-image switching

Scope:

- Add `--image` parameter for local file input.
- When `--image` is set, use image-to-image endpoint.
- Validate image path and readable file.

Deliverables:

- Documented image-to-image example.
- Clear error if model does not support image-to-image.

Acceptance checks:

- Passing `--image` uses image-to-image flow.
- Missing image path fails fast with message.

### Phase 3: Robustness and user experience

Scope:

- Default values for model, provider, aspect, format, timeout, poll interval.
- Create output directories when missing.
- Better error messages for timeouts and HTTP errors.

Deliverables:

- Consistent logging format.
- Retry on transient errors if safe.

Acceptance checks:

- Default run works with only prompt and output.
- Timeout error includes suggestion for `--timeout`.

### Phase 4: Configuration options

Scope:

- Optional config file support (e.g., `.env` or `config.json`).
- Environment variables override config file where appropriate.

Deliverables:

- Config format and precedence rules.
- Example config file in docs.

Acceptance checks:

- Configuration is loaded correctly and can be overridden by CLI args.

### Phase 5: GUI MVP (PySide6)

Scope:

- Build a PySide6 desktop app shell.
- Implement prompt input, output path, and generate button.
- Display status and log output.
- Use background worker for network requests.

Deliverables:

- PySide6 app launches and can generate a text-to-image result.
- Consistent styling (light theme, modern spacing).

Acceptance checks:

- UI does not freeze during generation.
- Success and error states are visible.

### Phase 6: GUI image-to-image

Scope:

- Add image upload control.
- Auto switch to image-to-image when file selected.
- Preview uploaded image.

Deliverables:

- GUI flow for image-to-image.

Acceptance checks:

- Image upload switches mode and generates output.

### Phase 7: GUI polish and configuration

Scope:

- Settings panel for model, aspect, format, and timeout.
- Persist last used settings locally.
- Open output folder action.

Deliverables:

- Settings panel and persistence.

Acceptance checks:

- Settings persist across runs.

### Phase 8: Developer experience and maintenance

Scope:

- Add minimal tests for argument parsing and mode switching.
- Add lint or formatting instructions.
- Add troubleshooting guide (common errors).

Deliverables:

- Test command in README.
- Basic error catalog.

Acceptance checks:

- Tests run in CI or locally without extra services.

## 5. Requirements traceability

- Minimal local usage: Phase 0-1.
- Configurable API key and model: Phase 1 and 4.
- Default text-to-image: Phase 1.
- Auto image-to-image when local file provided: Phase 2.

## 6. Risks and mitigations

- API instability: add timeouts and clear errors.
- Model capability mismatch: validate model and explain limits.
- File permission errors: check paths and surface details.

## 7. Open questions

- Which image-to-image endpoint is used for each model?
- Preferred config format: `.env` vs `config.json`?
- Do we need batch prompts (multiple outputs)?
- Do we need a dark theme option for the GUI?
