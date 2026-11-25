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

### Realistic film mode (primary live-action pipeline)

The realistic renderer now has its own story-grounded director layer:

- `realistic_director.py` derives scene-specific archive queries from the narration, selects shot sizes/camera direction, rejects unsupported named cast and writes photorealistic period-correct generation prompts.
- Old LEGO `plan.json` files are adapted, but their minifigure actors/props are not blindly treated as realistic scene direction.
- Historical prompts prohibit modern public figures, contemporary objects and anachronistic uniforms/equipment.
- Named people receive reusable Gemini identity-reference portraits when `GEMINI_API_KEY` is configured; generated scene images can use those references for better continuity.
- A scene can use a real moving clip from `media/videos/scene_001.mp4`, `scene_002.mp4`, etc. The renderer decodes clips, places them on the narration timeline, adds captions, transitions, sound effects, music and voiceover.
- If no suitable visual can be found or generated, rendering stops with a clear error instead of silently filling the film with text cards. Use `--allow-cards` only when you explicitly want that fallback.

Set a Gemini key in PowerShell (used for planning and photorealistic images):

```powershell
$env:GEMINI_API_KEY = "YOUR_KEY"
```

Render the existing story using its existing plan:

```powershell
python cinema.py myscript.txt output_realistic.mp4 --style realistic --plan plan.json --content-style history --source auto
```

Run a quick low-resolution test first:

```powershell
python cinema.py myscript.txt realistic_preview.mp4 --style realistic --plan plan.json --content-style history --source gen --preview --silent --nomusic
```

Use the 1080p final render (default) or force 720p:

```powershell
python cinema.py myscript.txt output_realistic_1080p.mp4 --style realistic --plan plan.json --content-style history --resolution 1080p
```

Intel graphics: `--encoder auto` tests whether FFmpeg can initialize Intel Quick Sync (H.264 QSV). It selects QSV only if the runtime test succeeds; otherwise it falls back to CPU `libx264`. To require QSV, use `--encoder h264_qsv`. To force CPU encoding, use `--encoder libx264`.

Optional generated/live-action scene clips can replace individual still images. Put clips in `media/videos` and name them `scene_001.mp4`, `scene_002.mp4`, etc. The clip's audio is ignored; narration, music and sound effects are mixed by the engine. A clip shorter than its narration scene holds its last frame; use clips at least as long as the spoken scene for best results.

Useful realistic options:

- `--source auto|photo|gen`
- `--content-style history|mythology|news|science|animals|story`
- `--resolution 720p|1080p` (1080p default)
- `--encoder auto|libx264|h264_qsv`
- `--video-dir media/videos`
- `--preview` for 640x360 at 12 fps
- `--silent` to disable narration
- `--allow-cards` to explicitly permit text-card fallback
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

## Realistic-renderer scope and limitations

The current renderer combines still-image cinematography (camera moves, grading, titles, captions, transitions, sound design and narration) with optional real moving scene clips supplied in `media/videos`. It does not yet synthesize a unique moving video clip for every scene by itself. The next development milestone is a video-generation provider layer with shot-level prompts, identity references and clip QA. The existing image-first path remains the reliable fallback when no video provider is configured.

Intel QSV is an optional H.264 encoding acceleration only. It does not accelerate AI image/video generation. Intel QSV is selected only after a real FFmpeg runtime probe; CPU encoding remains the fallback.

Existing LEGO renderer files remain separate and are not used by realistic mode.
