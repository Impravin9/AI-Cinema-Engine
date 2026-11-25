"""Deterministic casting and motion corrections for the legacy LEGO renderer.

This module is intentionally an adapter: it sanitizes the director's plan and
corrects actor paths before the existing renderer builds frames. It does not
replace the renderer or invent named historical figures.
"""
from __future__ import annotations

import re
from typing import Any

_SOURCE_SCRIPT = ""

_GROUP_TERMS = {
    "soldier", "soldiers", "troop", "troops", "army", "armies", "civilian",
    "civilians", "refugee", "refugees", "pilot", "pilots", "sailor", "sailors",
    "crew", "workers", "worker", "people", "crowd", "villagers", "villager",
    "police", "officer", "officers", "commander", "commanders", "general",
    "generals", "leader", "leaders", "king", "queen", "minister", "president",
    "doctor", "nurse", "scientist", "reporter", "journalist", "teacher",
    "family", "children", "child", "man", "woman", "men", "women"
}

def set_source_script(text: str) -> None:
    global _SOURCE_SCRIPT
    _SOURCE_SCRIPT = str(text or "")

def _words(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", str(value or "").lower())

def _is_group(name: str, role: str | None) -> bool:
    words = set(_words(name))
    return bool(words & _GROUP_TERMS) or (role or "").lower() in {
        "soldier", "civilian", "pilot", "sailor", "commander", "general",
        "king", "queen", "minister", "president", "doctor", "nurse",
        "scientist", "reporter", "journalist", "villager", "police"
    }

def _mentioned(name: str, source: str) -> bool:
    n = _words(name)
    s = set(_words(source))
    # Require at least one meaningful name token to occur in the user's script.
    # For multi-word historical names, matching the surname is sufficient.
    return any(len(token) > 2 and token in s for token in n)

def _scene_action(text: str, role: str = "") -> str:
    t = " " + " ".join(_words(text)) + " "
    r = (role or "").lower()
    if re.search(r"\b(run|ran|running|flee|fled|escape|escaped|charge|charged|rush|rushed)\b", t):
        return "run"
    if re.search(r"\b(march|marched|marching|advance|advanced|retreat|retreated|walk|walked|enter|entered|approach|approached)\b", t):
        return "walk"
    if re.search(r"\b(salute|saluted|saluting)\b", t):
        return "bow"
    if re.search(r"\b(order|ordered|command|commanded|point|pointed|signal|signalled|signaled)\b", t):
        return "point"
    if re.search(r"\b(speak|spoke|say|said|announce|announced|tell|told|ask|asked|declare|declared)\b", t):
        return "talk"
    if re.search(r"\b(pray|prayed|worship|worshipped|kneel|knelt)\b", t):
        return "namaste"
    if re.search(r"\b(hide|hid|hiding|crouch|crouched)\b", t):
        return "crouch"
    if re.search(r"\b(fall|fell|collapsed|collapse|hit the ground)\b", t):
        return "fall"
    if re.search(r"\b(celebrate|celebrated|victory|won|cheered|cheer)\b", t):
        return "cheer"
    if re.search(r"\b(attack|attacked|fight|fought|battle|battled|fire|fired|shoot|shot)\b", t):
        return "angry" if r not in {"soldier", "pilot", "sailor"} else "point"
    if re.search(r"\b(think|planned|plan|considered|studied|examined)\b", t):
        return "think"
    if re.search(r"\b(cry|cried|mourn|mourned|grieve|grieved)\b", t):
        return "sad"
    return "idle"

def sanitize_plan(plan: dict[str, Any], source_script: str | None = None) -> dict[str, Any]:
    """Remove named cast not supported by the input script; keep role groups."""
    source = _SOURCE_SCRIPT if source_script is None else str(source_script)
    characters = plan.get("characters") or []
    kept: list[dict[str, Any]] = []
    allowed: set[str] = set()
    for character in characters:
        if not isinstance(character, dict):
            continue
        name = str(character.get("name") or "").strip()
        role = character.get("role")
        if not name:
            continue
        if _is_group(name, role) or _mentioned(name, source):
            kept.append(character)
            allowed.add(name.casefold())

    # Keep the original character definitions, but remove unsupported scene cast.
    plan["characters"] = kept
    for scene in plan.get("scenes") or []:
        if not isinstance(scene, dict):
            continue
        text = str(scene.get("text") or "")
        actors = []
        for actor in scene.get("actors") or []:
            if not isinstance(actor, dict):
                continue
            name = str(actor.get("name") or "").strip()
            if not name:
                continue
            if name.casefold() in allowed or _mentioned(name, source) or _is_group(name, None):
                actor["action"] = _scene_action(text, str(actor.get("role") or ""))
                actors.append(actor)
        scene["actors"] = actors[:3]
    return plan

def install() -> None:
    """Wrap the existing director once, retaining all its drawing and audio code."""
    import lego_director as director

    if getattr(director.build_scenes, "_cinema_motion_fix", False):
        return
    original = director.build_scenes

    def build_scenes_fixed(plan, tts=None):
        clean = sanitize_plan(plan)
        # Normalize automatic/unknown actions into deliberate, story-derived actions.
        for scene in clean.get("scenes") or []:
            text = str(scene.get("text") or "")
            for actor in scene.get("actors") or []:
                role = str(actor.get("role") or "")
                action = str(actor.get("action") or "auto").lower()
                if action in {"", "auto"}:
                    actor["action"] = _scene_action(text, role)
                elif action not in director.E.ONE and action not in {
                    "run", "walk", "idle", "kick", "header", "jump", "celebrate",
                    "cheer", "sad", "shock", "angry", "talk", "point", "fall",
                    "getup", "dive", "shrug", "bow", "wave", "namaste", "dance",
                    "crouch", "think"
                }:
                    actor["action"] = _scene_action(text, role)

        rendered, genre, title = original(clean, tts)
        # Legacy build_scenes creates a horizontal drift path even for idle actors.
        # Pin all non-travelling characters to a fixed mark. Gesture/action cycles
        # still run from their explicit keyframes, but they no longer shuffle
        # across the frame like sleepwalkers.
        for index, scene in enumerate(rendered):
            source_scene = clean["scenes"][index] if index < len(clean["scenes"]) else {}
            source_actors = {
                str(a.get("name", "")).casefold(): a
                for a in (source_scene.get("actors") or [])
                if isinstance(a, dict)
            }
            for actor in scene.get("actors", []):
                ch = actor.get("ch")
                name = str(ch.get("name", "") if isinstance(ch, dict) else "").casefold()
                source_actor = source_actors.get(name, {})
                action = str(source_actor.get("action") or "idle").lower()
                if action not in {"walk", "run"}:
                    path = actor.get("path") or [(0, 640, 560)]
                    point = path[len(path) // 2]
                    x = float(point[1]); y = float(point[2])
                    actor["path"] = [(0.0, x, y)]
        return rendered, genre, title

    build_scenes_fixed._cinema_motion_fix = True
    director.build_scenes = build_scenes_fixed
