# AI-Cinema-Engine

A Python-based hybrid cinema pipeline with separate LEGO and realistic documentary renderers.

## Current architecture

- `cinema.py`: unified command-line entry point and renderer selection.
- `core/contracts.py`: shared validation/inspection for the existing LEGO and modern storyboard JSON formats.
- `core/runner.py`: launches the preserved renderer as a subprocess, isolates its working directory and reports failures.
- `lego_boost.py` / `lego_ai.py` / `lego_director.py` / `lego_engine_v2.py`: existing LEGO pipeline (preserved).
- `lego_modern.py`: existing realistic photo/AI-visual documentary renderer (preserved).

The orchestration layer deliberately delegates to the existing renderers instead of importing and patching their internal modules. This avoids the current legacy import chain leaking into the new entry point.

## Quick start (Windows PowerShell)

Install Python dependencies:

```powershell
python -m pip install -r requirements-cinema.txt
winget install Gyan.FFmpeg
```

Set one supported LLM key if you want automatic AI planning. For example:

```powershell
$env:GEMINI_API_KEY = "YOUR_KEY"
```

Alternatively, use Ollama where supported by the selected legacy director.

### Realistic documentary mode

```powershell
python cinema.py myscript.txt output.mp4 --style realistic
```

Use the existing LEGO-compatible `plan.json` (the modern renderer adapts its legacy fields):

```powershell
python cinema.py myscript.txt output.mp4 --style realistic --plan plan.json
```

Create a prompt to plan manually in an LLM:

```powershell
python cinema.py myscript.txt --style realistic --prompt-only
```

The generated prompt is `modern_prompt.txt`. Save the model's JSON response as `modern_plan.json`, then render:

```powershell
python cinema.py myscript.txt output.mp4 --style realistic --plan modern_plan.json
```

Useful realistic options:

- `--source auto|photo|gen`
- `--content-style history|mythology|news|science|animals|story`
- `--preview` for 640x360 at 12 fps
- `--silent` to disable narration
- `--media media` and `--music music` for local assets

### LEGO mode

```powershell
python cinema.py myscript.txt output.mp4 --style lego
```

The unified entry point delegates to `lego_boost.py`, which enables its improved narration fallback and scene/background upgrades while preserving the existing LEGO engine.

Use a saved LEGO plan:

```powershell
python cinema.py myscript.txt output.mp4 --style lego --plan plan.json
```

Use the faster LEGO rendering setting:

```powershell
python cinema.py myscript.txt output.mp4 --style lego --fast
```

## Plan validation and tests

The shared validator checks the common minimum contract (`title` and non-empty `scenes[].text`) without rewriting renderer-specific scene fields.

Run tests:

```powershell
python -m unittest discover -s tests -v
```

## Hardware notes

The current realistic renderer encodes H.264 through FFmpeg `libx264`. Intel GPU acceleration is not claimed by this first integration layer. We will add Intel QSV/OpenVINO paths only after checking the actual installed driver and FFmpeg capabilities; CPU fallback remains the reliable baseline.

## Important limitations

This phase unifies execution, not the underlying visual-generation models. The realistic renderer currently creates image-led documentary sequences with cinematic motion/effects; it is not yet a full temporal character-animation/video-generation pipeline. Character reference management and true video generation are later development phases.

Existing renderer files are intentionally not replaced in Phase 1.
