"""Run the Borrow Card matcher against a saved capture frame.

  py -3.12 autopilot/tools/try_borrow_match.py <frame.png> --target "[Q!=0] Agnes Tachyon"

Lets the matching logic be checked without the game running.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2
import easyocr

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from autopilot.borrow_match import find_best, parse_rows, score_row  # noqa: E402

# Text column of the Borrow Card rows, left of the "Following" badge.
LIST_REGION = (225, 175, 530, 935)  # l, t, r, b

# The repo's allowlist plus brackets, which measurably improves card titles.
ALLOWLIST = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-!.,'#? []()"


def main() -> int:
  p = argparse.ArgumentParser()
  p.add_argument("frame", help="PNG from autopilot/captures/")
  p.add_argument("--target", action="append", default=[],
                 help="Wanted card, repeatable, in priority order")
  p.add_argument("--threshold", type=float, default=0.80)
  args = p.parse_args()

  img = cv2.imread(args.frame, cv2.IMREAD_COLOR)
  if img is None:
    print(f"[ERROR] could not read {args.frame}")
    return 1

  l, t, r, b = LIST_REGION
  crop = cv2.cvtColor(img[t:b, l:r], cv2.COLOR_BGR2RGB)

  reader = easyocr.Reader(["en"], gpu=False, verbose=False)
  rows = parse_rows(reader.readtext(crop, allowlist=ALLOWLIST), y_offset=t, x_offset=l)

  print(f"parsed {len(rows)} rows from {Path(args.frame).name}\n")
  for i, row in enumerate(rows, 1):
    print(f"  row {i}  y={row.top}-{row.bottom}  click_y={row.center_y}")
    print(f"    friend    : {row.friend!r}")
    print(f"    title     : {row.title!r}")
    print(f"    character : {row.character!r}")
    for target in args.target:
      print(f"    score vs {target!r}: {score_row(row, target):.3f}")
    print()

  if args.target:
    row, target, score = find_best(rows, args.target, args.threshold)
    if row:
      print(f"MATCH: {target!r} -> {row.card!r} (score {score:.3f}), click at y={row.center_y}")
    else:
      print(f"NO MATCH above {args.threshold}")
  return 0


if __name__ == "__main__":
  sys.exit(main())
