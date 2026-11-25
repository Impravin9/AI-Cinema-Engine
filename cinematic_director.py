"""Offline story-aware director: turns prose beats into filmable action and coverage.

The director is deterministic and dependency-free. Explicit storyboard decisions always
win; inferred metadata is conservative and intended to drive the procedural renderer.
"""
from __future__ import annotations

import re
from typing import Any

_WORD = re.compile(r"[a-z0-9']+")


def _has(text: str, *terms: str) -> bool:
    words = set(_WORD.findall(text))
    return any(term in words for term in terms)


def direct_scene(scene: dict[str, Any], index: int = 0) -> dict[str, Any]:
    """Infer a playable action, emotional beat, setting and camera plan."""
    result = dict(scene)
    narration = str(scene.get("text") or "")
    text = " ".join(_WORD.findall(narration.lower()))

    # Specific physical actions must be tested before generic movement/reaction verbs.
    if _has(text, "fights", "fight", "fighting", "punches", "punch", "strikes", "strike",
            "duels", "duel", "attacks", "attack", "battles", "battle", "blocks", "block"):
        action, camera, shot, pace = "fight", "tracking", "medium_wide", "fast"
    elif _has(text, "kneels", "kneel", "kneeling", "bows", "bow", "prays", "pray"):
        action, camera, shot, pace = "kneel", "push_in", "medium", "slow"
    elif _has(text, "sits", "sit", "sitting", "sat", "rests", "rest"):
        action, camera, shot, pace = "sit", "slow_pan", "medium", "slow"
    elif _has(text, "points", "point", "pointing", "signals", "signal", "gestures", "gesture"):
        action, camera, shot, pace = "point", "push_in", "medium", "steady"
    elif _has(text, "runs", "run", "running", "chases", "chase", "escapes", "escape",
              "rushes", "rush", "sprints", "sprint", "flees", "flee"):
        action, camera, shot, pace = "run", "tracking", "medium_wide", "fast"
    elif _has(text, "walks", "walk", "walking", "approaches", "approach", "travels", "travel",
              "marches", "march", "wanders", "wander", "enters", "enter"):
        action, camera, shot, pace = "walk", "tracking", "wide", "steady"
    elif _has(text, "falls", "fall", "collapses", "collapse", "topples", "topple"):
        action, camera, shot, pace = "fall", "pull_back", "wide", "slow"
    elif _has(text, "turns", "turn", "looks", "look", "notices", "notice", "sees", "see",
              "hears", "hear", "discovers", "discover", "realizes", "realise", "realises",
              "reacts", "react"):
        action, camera, shot, pace = "react", "push_in", "close_up", "slow"
    elif _has(text, "speaks", "speak", "says", "said", "asks", "ask", "shouts", "shout",
              "tells", "tell", "whispers", "whisper", "replies", "reply"):
        action, camera, shot, pace = "speak", "push_in", "medium_close", "steady"
    else:
        action, camera, shot, pace = "observe", "slow_pan", "medium", "slow"

    if _has(text, "afraid", "fear", "terrified", "danger", "threat", "enemy", "attacks",
            "attack", "panic", "horrified"):
        mood = "fear"
    elif _has(text, "happy", "smiles", "smile", "celebrates", "celebrate", "joy", "laughs",
              "laugh", "triumph"):
        mood = "joy"
    elif _has(text, "sad", "grief", "cries", "cry", "mourning", "loss", "weeps", "weep",
              "heartbroken"):
        mood = "sadness"
    elif _has(text, "angry", "anger", "furious", "rage", "enraged", "shouts", "shout"):
        mood = "anger"
    elif _has(text, "discovers", "discover", "notices", "notice", "mystery", "strange",
              "smoke", "wonders", "wonder"):
        mood = "curiosity"
    else:
        mood = "determined"

    if _has(text, "forest", "woods", "trees", "jungle"):
        environment = "forest"
    elif _has(text, "village", "hut", "houses", "market", "street", "town"):
        environment = "village"
    elif _has(text, "battle", "war", "soldier", "army", "weapon", "tank", "sword"):
        environment = "battlefield"
    elif _has(text, "room", "house", "inside", "hall", "door", "chamber", "palace",
              "temple", "interior", "bedroom"):
        environment = "interior"
    elif _has(text, "river", "sea", "ocean", "lake", "shore", "waterfall", "coast"):
        environment = "water"
    elif _has(text, "mountain", "hill", "cliff", "peak", "valley"):
        environment = "mountain"
    else:
        environment = "landscape"

    # Film grammar: give otherwise static beats a deliberate coverage plan.
    defaults = {
        "action": action, "camera_move": camera, "shot_type": shot, "pace": pace,
        "mood": mood, "environment": environment, "shot_index": index,
        "performance_intensity": {"fast": 0.95, "steady": 0.62, "slow": 0.38}[pace],
        "screen_direction": "left_to_right" if index % 2 == 0 else "right_to_left",
        "transition": "cut",
        "blocking": "center",
    }
    if action in ("run", "walk", "fight"):
        defaults["blocking"] = "moving_profile"
    elif action in ("kneel", "sit", "fall"):
        defaults["blocking"] = "lowered_center"
    elif action in ("point", "speak"):
        defaults["blocking"] = "three_quarter"
    elif action == "react":
        defaults["blocking"] = "close_subject"

    # Avoid a monotonous sequence of identical medium shots when the story has no
    # explicit camera instructions. A beat after an establishing wide gets coverage.
    if action == "observe" and index == 0:
        defaults["shot_type"] = "wide"
        defaults["camera_move"] = "slow_pan"
    elif action == "observe" and index % 3 == 2:
        defaults["shot_type"] = "medium_close"
        defaults["camera_move"] = "push_in"

    for key, value in defaults.items():
        result.setdefault(key, value)
    return result


def direct_plan(scenes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Direct a complete ordered sequence while preserving all explicit user choices."""
    directed = [direct_scene(scene, index) for index, scene in enumerate(scenes)]
    for index, scene in enumerate(directed):
        explicit_transition = "transition" in scenes[index]
        if (index and not explicit_transition
                and scene.get("environment") != directed[index - 1].get("environment")):
            scene["transition"] = "establishing_cut"
        if scene.get("action") in ("fight", "run"):
            scene.setdefault("pace", "fast")
        scene.setdefault("coverage_role", "establishing" if index == 0 else "story_beat")
    return directed
