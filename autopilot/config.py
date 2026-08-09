"""Autopilot settings, read from the "autopilot" block of config.json.

Read straight from the JSON rather than through core/config.py, whose
reload_config() raises on any key it does not find. Keeping these optional
means an existing config.json keeps working untouched, and merges from
upstream never collide over a config key.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field


DEFAULTS = {
  # Support cards to borrow, best first. Written as they appear in game;
  # matching normalises punctuation away, so "[Q!=0] Agnes Tachyon" and the
  # real "[Q<>0] Agnes Tachyon" both work.
  "borrow_card_targets": [],
  # Stop rather than borrow something unintended when no target is found.
  "borrow_required": True,
  # How many times to scroll the borrow list before giving up.
  "borrow_max_scrolls": 8,
  # Levenshtein ratio a row must reach to count as the wanted card.
  "borrow_match_threshold": 0.80,
  # Cap on Skills visits per career, so a career can never loop forever
  # between Complete Career and the Learn screen.
  "max_skill_visits": 5,
  # Wait and retry when TP is too low, instead of stopping.
  "wait_when_out_of_tp": True,
  # Seconds between polls while waiting for the training to finish.
  "idle_poll_seconds": 20.0,
}


@dataclass
class AutopilotConfig:
  borrow_card_targets: list[str] = field(default_factory=list)
  borrow_required: bool = True
  borrow_max_scrolls: int = 8
  borrow_match_threshold: float = 0.80
  max_skill_visits: int = 5
  wait_when_out_of_tp: bool = True
  idle_poll_seconds: float = 20.0


def load(path: str = "config.json") -> AutopilotConfig:
  try:
    with open(path, "r", encoding="utf-8") as f:
      block = json.load(f).get("autopilot", {})
  except (OSError, json.JSONDecodeError):
    block = {}

  values = {key: block.get(key, default) for key, default in DEFAULTS.items()}
  return AutopilotConfig(**values)
