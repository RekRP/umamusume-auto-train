"""The screen table for the Independent Training cycle.

Order matters: entries are tried top to bottom and the first match wins, so
specific screens come before the generic catch-alls. Several screens share a
button - close_btn appears on Borrow Card, Skills Learned and Umamusume
Details; next_btn on Trainee Select and all three result screens - so the
ambiguous ones are identified by a header crop first, and whatever is left
falls through to a generic rule whose action is the same anyway.

Never match against all of assets/: some templates there are tiny enough to
correlate with almost anything (assets/ui/energy_bar_right_end_part.png scores
0.87-0.98 on every screen tested). Only the templates named here are used.
"""

from __future__ import annotations

from dataclasses import dataclass

AUTO = "assets/autopilot"
BTN = "assets/buttons"


@dataclass(frozen=True)
class Screen:
  name: str
  # Template proving we are on this screen.
  identify: str
  # What the bot does here, for logs and the dry-run probe.
  action: str
  # Template to click. None means `handler` decides.
  click: str | None = None
  # Name of a special routine in the loop (borrowing, skill buying, branches).
  handler: str | None = None
  # Restricts where `identify` may match. Only needed where a shared button
  # would otherwise make two different screens look alike.
  identify_region: tuple[int, int, int, int] | None = None


# Result screens put Next at y~963, Trainee Select puts it at y~879. Without
# this band, the slow header slide on Trainee Select leaves a window where only
# the button is drawn and the generic result rule claims the screen.
RESULT_BUTTON_BAND = (0, 930, 800, 1080)


SCREENS: tuple[Screen, ...] = (
  # --- start of a run -------------------------------------------------
  Screen("borrow_card", f"{AUTO}/borrow_card_header.png",
         "find and tap the wanted support card", handler="borrow"),
  Screen("trainee_select", f"{AUTO}/trainee_select_header.png",
         "keep the selected trainee and continue", click=f"{BTN}/next_btn.png"),
  Screen("support_formation", f"{AUTO}/start_career_btn.png",
         "open the borrow list if the slot is empty, else start",
         handler="formation"),
  Screen("final_confirmation", f"{AUTO}/start_btn.png",
         "spend TP and begin training", click=f"{AUTO}/start_btn.png"),
  Screen("home", f"{AUTO}/career_btn.png",
         "open Career", click=f"{AUTO}/career_btn.png"),

  # --- end of a run ---------------------------------------------------
  Screen("training_log", f"{BTN}/ok_btn.png",
         "dismiss the training results", click=f"{BTN}/ok_btn.png"),
  Screen("complete_career_confirm", f"{AUTO}/finish_btn.png",
         "confirm finishing the playthrough", click=f"{AUTO}/finish_btn.png"),
  Screen("complete_career", f"{BTN}/complete_career_btn.png",
         "buy skills while points remain, else complete the career",
         handler="complete_career"),
  # Identified by the Skill Points bar, NOT by its Confirm button: the Sparks
  # screen and the Sparks confirmation carry the same Confirm, and treating
  # either as Learn would click beside "Reroll Sparks (Consumes 30 TP)".
  Screen("learn", f"{AUTO}/skill_points_label.png",
         "pick skills and confirm", handler="buy_skills"),
  Screen("learn_confirmation", f"{BTN}/learn_btn.png",
         "confirm learning the chosen skills", click=f"{BTN}/learn_btn.png"),
  Screen("sparks", f"{AUTO}/reroll_sparks_btn.png",
         "accept the inheritance sparks without rerolling",
         click=f"{BTN}/confirm_btn.png"),
  Screen("career_complete", f"{AUTO}/to_home_btn.png",
         "return to Home and close the loop", click=f"{AUTO}/to_home_btn.png"),

  # --- generic fallbacks, same action wherever they appear ------------
  # Reached only after the specific Confirm screens above have been ruled out.
  Screen("confirmation", f"{BTN}/confirm_btn.png",
         "accept a confirmation dialog", click=f"{BTN}/confirm_btn.png"),
  Screen("result", f"{BTN}/next_btn.png",
         "advance a result screen", click=f"{BTN}/next_btn.png",
         identify_region=RESULT_BUTTON_BAND),
  Screen("dialog", f"{BTN}/close_btn.png",
         "close a dialog", click=f"{BTN}/close_btn.png"),
)

# Template that tells the borrow slot is still empty. Checked by the
# "formation" handler; scores 1.000 empty vs 0.581 filled.
FRIENDS_SLOT_EMPTY = f"{AUTO}/friends_slot_empty.png"

# The Complete Career screen's Skills button, which differs from the career
# lobby's (upstream skills_btn.png scores 0.558 here).
SKILLS_BUTTON = f"{AUTO}/skills_btn_career_complete.png"

START_CAREER_BUTTON = f"{AUTO}/start_career_btn.png"

MATCH_THRESHOLD = 0.85

# --- geometry, in ADB frame coordinates (800x1080) --------------------
# main.py shifts GAME_WINDOW_BBOX by -155 for ADB, giving (0,0,800,1080),
# so these line up with utils/constants.py once that shift is applied.

# Text column of the Borrow Card rows, left of the "Following" badge.
BORROW_LIST_LTRB = (225, 175, 530, 935)
# Where to tap a chosen row, and the swipe that scrolls the list one page.
BORROW_ROW_X = 400
BORROW_SCROLL_FROM = (400, 820)
BORROW_SCROLL_TO = (400, 400)

# Skill point total on the Learn screen, right of the "Skill Points" bar.
# Verified reading 3258 off a real frame.
SKILL_POINTS_LTRB = (560, 342, 680, 375)

# easyocr allowlist for the Borrow Card rows. The repo default omits brackets,
# which measurably degrades card titles ([Teio-Oo-Oolll] 0.80 -> 1.00).
BORROW_ALLOWLIST = (
  "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-!.,'#? []()"
)
