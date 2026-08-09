"""Matching logic for the Borrow Card list.

Pure functions only - no device access - so they can be tested against saved
capture frames. The driver that scrolls and clicks lives elsewhere.

The Borrow Card list is sorted by Last Login and its contents change every run,
so selection is content-based, never positional.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import Levenshtein

# easyocr box -> ((corners), text, confidence). Corners are [tl, tr, br, bl].
OcrItem = tuple[list, str, float]

# Vertical gap that separates one card row from the next. Measured on real
# frames: lines inside a row sit <=37px apart, rows are 53-62px apart.
ROW_GAP = 45
# Vertical gap that separates lines within a single row. Fragments of the same
# line ("Biko" / "Pegasus") land within a few px of each other.
LINE_GAP = 12


def normalize(text: str) -> str:
  """Fold OCR noise and unreadable glyphs away.

  The card title "[Q!=0]" renders with a character easyocr's English model
  cannot produce, and it comes back as "[Q*0]" or "[Q+0]" on different rows of
  the same screen. Dropping non-alphanumerics makes all those spellings - and
  the configured target - collapse onto the same string.
  """
  return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", text.lower())).strip()


@dataclass
class BorrowRow:
  """One entry in the Borrow Card list."""
  lines: list[str] = field(default_factory=list)
  top: int = 0
  bottom: int = 0

  @property
  def friend(self) -> str:
    return self.lines[0] if self.lines else ""

  @property
  def title(self) -> str:
    return self.lines[1] if len(self.lines) > 1 else ""

  @property
  def character(self) -> str:
    return self.lines[2] if len(self.lines) > 2 else ""

  @property
  def card(self) -> str:
    """Title plus character, i.e. what identifies the support card."""
    return f"{self.title} {self.character}".strip()

  @property
  def center_y(self) -> int:
    return (self.top + self.bottom) // 2


def _cluster(items: list[tuple[int, int, str]], gap: int) -> list[list[tuple[int, int, str]]]:
  """Split y-sorted (y, x, text) items wherever the y gap exceeds `gap`."""
  groups: list[list[tuple[int, int, str]]] = []
  for item in items:
    if groups and item[0] - groups[-1][-1][0] <= gap:
      groups[-1].append(item)
    else:
      groups.append([item])
  return groups


def parse_rows(ocr_result: list[OcrItem], y_offset: int = 0, x_offset: int = 0) -> list[BorrowRow]:
  """Turn raw easyocr output for the list region into card rows.

  Offsets convert crop-local coordinates back to full-frame coordinates so the
  caller can click a matched row directly.
  """
  items = sorted(
    ((int(box[0][1]) + y_offset, int(box[0][0]) + x_offset, text) for box, text, _ in ocr_result),
    key=lambda i: i[0],
  )

  rows: list[BorrowRow] = []
  for group in _cluster(items, ROW_GAP):
    lines = []
    for line in _cluster(group, LINE_GAP):
      # Fragments of one line arrive out of order; x-sort rebuilds "Biko Pegasus".
      lines.append(" ".join(text for _, _, text in sorted(line, key=lambda i: i[1])))
    rows.append(BorrowRow(lines=lines, top=group[0][0], bottom=group[-1][0]))
  return rows


def score_row(row: BorrowRow, target: str) -> float:
  """How well a row matches a configured target, 0..1.

  Scores against the full "title character" string and against the character
  name alone, taking the better of the two. That lets a target be written
  either way - "[Q!=0] Agnes Tachyon" or just "Agnes Tachyon".
  """
  wanted = normalize(target)
  if not wanted:
    return 0.0
  return max(
    Levenshtein.ratio(wanted, normalize(row.card)),
    Levenshtein.ratio(wanted, normalize(row.character)),
  )


def find_best(rows: list[BorrowRow], targets: list[str], threshold: float = 0.80
              ) -> tuple[BorrowRow | None, str, float]:
  """Best (row, target, score) across all rows, or (None, "", 0.0).

  `targets` is in priority order: an earlier target wins ties, so a preferred
  card is taken over an equally-good later one.
  """
  best: tuple[BorrowRow | None, str, float] = (None, "", 0.0)
  for target in targets:
    for row in rows:
      score = score_row(row, target)
      if score > best[2]:
        best = (row, target, score)
  return best if best[2] >= threshold else (None, "", 0.0)


def duplicate_row_indexes(rows: list[BorrowRow], badge_ys: list[int],
                          max_gap: int = 60) -> set[int]:
  """Rows carrying a "Duplicate Support" badge, by index.

  The badge cannot be read as text: it is drawn over the card thumbnail, left
  of the text column that gets OCR'd. It is matched as an image instead, and
  sits just above the row it belongs to - measured at y=468 for a row whose
  text starts at y=489 - so each badge is attributed to the next row down.
  """
  flagged: set[int] = set()
  for badge_y in badge_ys:
    below = [(row.top - badge_y, index) for index, row in enumerate(rows)
             if 0 <= row.top - badge_y <= max_gap]
    if below:
      flagged.add(min(below)[1])
  return flagged
