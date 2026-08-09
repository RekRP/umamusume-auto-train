"""Detect-only probe: what does the bot think it is looking at?

Reads the screen over ADB and reports which entry of the screen table matches
and what the loop would do there. It never clicks, taps or swipes, so it is
safe to leave running while you play through a cycle by hand.

Run from the repo root:

  py -3.12 autopilot/tools/whereami.py

Every rule that matches is listed, not just the winner, so ambiguity between
screens is visible rather than hidden.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from adbutils import adb

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from autopilot.screens import (  # noqa: E402
  FRIENDS_SLOT_EMPTY, MATCH_THRESHOLD, SCREENS, SKILLS_BUTTON,
)

_cache: dict[str, np.ndarray] = {}


def template(rel_path: str) -> np.ndarray | None:
  if rel_path not in _cache:
    img = cv2.imread(str(REPO_ROOT / rel_path), cv2.IMREAD_COLOR)
    if img is None:
      print(f"[WARN] missing template: {rel_path}")
      return None
    _cache[rel_path] = img
  return _cache[rel_path]


def best_score(frame: np.ndarray, rel_path: str,
               region: tuple[int, int, int, int] | None = None) -> tuple[float, tuple[int, int]]:
  tpl = template(rel_path)
  if tpl is None:
    return 0.0, (0, 0)

  offset_x, offset_y = 0, 0
  if region:
    left, top, right, bottom = region
    frame = frame[top:bottom, left:right]
    offset_x, offset_y = left, top

  if tpl.shape[0] > frame.shape[0] or tpl.shape[1] > frame.shape[1]:
    return 0.0, (0, 0)
  res = cv2.matchTemplate(frame, tpl, cv2.TM_CCOEFF_NORMED)
  _, score, _, loc = cv2.minMaxLoc(res)
  return float(score), (loc[0] + offset_x, loc[1] + offset_y)


def grab(device) -> np.ndarray:
  try:
    img = device.screenshot(error_ok=False)
  except Exception:
    img = device.screenshot()
  # adbutils gives RGB; templates are read as BGR, so match in BGR throughout.
  return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def describe(frame: np.ndarray) -> tuple[str, str, list[str]]:
  """Return (dedup key, display line, every matching rule).

  The key deliberately excludes match scores, which drift by a few thousandths
  as screens animate; keying on them would reprint the same screen endlessly.
  """
  matches = []
  winner = None
  for screen in SCREENS:
    score, loc = best_score(frame, screen.identify, screen.identify_region)
    if score >= MATCH_THRESHOLD:
      matches.append(f"{score:.3f}  {screen.name:20s} at {loc}")
      if winner is None:
        winner = (screen, score, loc)

  if winner is None:
    return "none", "unrecognised screen - nothing would be clicked", matches

  screen, score, loc = winner
  detail, state = "", ""
  if screen.handler == "formation":
    empty, _ = best_score(frame, FRIENDS_SLOT_EMPTY)
    state = "empty" if empty >= MATCH_THRESHOLD else "filled"
    detail = (f" -> borrow slot EMPTY ({empty:.3f}), would open the borrow list"
              if state == "empty"
              else f" -> borrow slot filled ({empty:.3f}), would press Start Career!")
  elif screen.handler == "complete_career":
    skills, sloc = best_score(frame, SKILLS_BUTTON)
    state = "skills" if skills >= MATCH_THRESHOLD else "no_skills"
    detail = (f" -> Skills button found ({skills:.3f}) at {sloc}"
              if state == "skills" else " -> no Skills button visible")

  return (f"{screen.name}|{state}",
          f"{screen.name}  ({score:.3f})  would: {screen.action}{detail}",
          matches)


def main() -> int:
  p = argparse.ArgumentParser(description="Report the detected screen. Never clicks.")
  p.add_argument("--device", default="127.0.0.1:5555")
  p.add_argument("--poll", type=float, default=1.0)
  p.add_argument("--all", action="store_true", help="List every matching rule, not just the winner")
  args = p.parse_args()

  try:
    adb.connect(args.device)
    device = adb.device(args.device)
    probe = grab(device)
  except Exception as e:
    print(f"[ERROR] could not connect to {args.device}: {e}")
    return 1

  print(f"[OK] {args.device}, frame {probe.shape[1]}x{probe.shape[0]}")
  print("[OK] Detect only - this never clicks. Ctrl+C to stop.\n")

  last = None
  try:
    while True:
      key, line, matches = describe(grab(device))
      if key != last:
        print(f"{time.strftime('%H:%M:%S')}  {line}")
        if args.all and len(matches) > 1:
          for m in matches[1:]:
            print(f"          also matched: {m}")
        last = key
      time.sleep(args.poll)
  except KeyboardInterrupt:
    print("\n[OK] stopped")
  return 0


if __name__ == "__main__":
  sys.exit(main())
