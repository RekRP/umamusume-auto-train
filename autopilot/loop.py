"""Continuous Independent Training loop.

Each tick: read the screen, identify it against the table in screens.py, run
that screen's action, repeat. Nothing tracks "what step are we on", so an
unexpected popup, a slow transition or being started mid-cycle all recover on
their own - and the bot can be launched from any screen.

The loop only ever clicks the location of a template it has already matched.
On a screen it does not recognise it does nothing at all, which is what keeps
a misread from turning into a stray tap.
"""

from __future__ import annotations

from PIL import Image

import core.bot as bot
import core.config as core_config
import utils.constants as constants
import utils.device_action_wrapper as device_action
from core.ocr import extract_number, get_reader
from core.skill import buy_skill, init_skill_py
from utils.adb_actions import init_adb
from utils.device_action_wrapper import BotStopException
from utils.log import debug, error, info, warning
from utils.notifications import StopReason
from utils.tools import sleep

from autopilot import config as auto_config
from autopilot.borrow_match import find_best, is_duplicate, parse_rows
from autopilot.screens import (
  BORROW_ALLOWLIST, BORROW_LIST_LTRB, BORROW_ROW_X, BORROW_SCROLL_FROM,
  BORROW_SCROLL_TO, FRIENDS_SLOT_EMPTY, MATCH_THRESHOLD, SCREENS,
  SKILL_POINTS_LTRB, SKILLS_BUTTON, START_CAREER_BUTTON,
)

CLOSE_BUTTON = "assets/buttons/close_btn.png"


class Autopilot:
  def __init__(self, cfg: auto_config.AutopilotConfig):
    self.cfg = cfg
    self.runs_completed = 0
    self.skill_visits = 0
    self.skills_done = False
    self.last_screen = None

  # --- screen reading -------------------------------------------------
  def identify(self):
    """First matching entry of the table, or (None, None)."""
    for screen in SCREENS:
      pos = device_action.locate(screen.identify, confidence=MATCH_THRESHOLD)
      if pos:
        return screen, pos
    return None, None

  def read_skill_points(self) -> int:
    """Skill point total on the Learn screen, or -1 if unreadable."""
    crop = device_action.screenshot(region_ltrb=SKILL_POINTS_LTRB)
    pil = Image.fromarray(crop)
    pil = pil.resize((pil.width * 3, pil.height * 3), Image.BICUBIC)
    return extract_number(pil)

  def read_borrow_rows(self):
    crop = device_action.screenshot(region_ltrb=BORROW_LIST_LTRB)
    result = get_reader().readtext(crop, allowlist=BORROW_ALLOWLIST)
    return parse_rows(result, y_offset=BORROW_LIST_LTRB[1], x_offset=BORROW_LIST_LTRB[0])

  # --- handlers -------------------------------------------------------
  def do_formation(self, screen):
    """Borrow first if the slot is still empty, otherwise start the career."""
    if device_action.locate(FRIENDS_SLOT_EMPTY, confidence=MATCH_THRESHOLD):
      info("Borrow slot empty, opening the borrow list.")
      device_action.locate_and_click(FRIENDS_SLOT_EMPTY, confidence=MATCH_THRESHOLD)
    else:
      info("Support formation ready, starting the career.")
      device_action.locate_and_click(START_CAREER_BUTTON, confidence=MATCH_THRESHOLD)

  def do_borrow(self, screen):
    targets = self.cfg.borrow_card_targets
    if not targets:
      error('No borrow_card_targets configured. Add them under "autopilot" in config.json.')
      device_action.stop_bot(StopReason.STUCK)
      return

    for attempt in range(self.cfg.borrow_max_scrolls + 1):
      rows = self.read_borrow_rows()
      debug(f"Borrow list page {attempt + 1}: {[r.card for r in rows]}")
      row, target, score = find_best(rows, targets, self.cfg.borrow_match_threshold)
      if row and not is_duplicate(row):
        info(f"Borrowing {target!r} - matched {row.card!r} ({score:.3f}) from {row.friend!r}.")
        device_action.click((BORROW_ROW_X, row.center_y))
        return
      if row:
        debug(f"Skipping {row.card!r}: flagged as a duplicate support.")
      device_action.flush_screenshot_cache()
      device_action.swipe(BORROW_SCROLL_FROM, BORROW_SCROLL_TO)
      sleep(0.6)

    if self.cfg.borrow_required:
      error(f"None of {targets} found after {self.cfg.borrow_max_scrolls} scrolls. Stopping "
            "rather than borrowing something unintended.")
      device_action.stop_bot(StopReason.STUCK)
    else:
      warning(f"None of {targets} found. Continuing without a borrowed card.")
      device_action.locate_and_click(CLOSE_BUTTON, confidence=MATCH_THRESHOLD)

  def do_complete_career(self, screen):
    """Spend skill points while any remain, then finish the career."""
    if not self.skills_done and self.skill_visits < self.cfg.max_skill_visits:
      if device_action.locate(SKILLS_BUTTON, confidence=MATCH_THRESHOLD):
        self.skill_visits += 1
        info(f"Opening the skill screen (visit {self.skill_visits}).")
        device_action.locate_and_click(SKILLS_BUTTON, confidence=MATCH_THRESHOLD)
        return
    info("Done buying skills, completing the career.")
    device_action.locate_and_click(screen.identify, confidence=MATCH_THRESHOLD)

  def do_buy_skills(self, screen):
    """Hand off to upstream's buy_skill(), which works on this screen as-is.

    It opens by looking for the career lobby's skills button, which is absent
    here (0.539), so that lookup harmlessly finds nothing before it starts
    scanning. init_skill_py() resets its turn gate, which paces buying during
    a career and is meaningless once the career is over.
    """
    sp = self.read_skill_points()
    if sp < 0:
      warning("Could not read the skill point total; leaving the skill screen.")
      self.skills_done = True
      device_action.locate_and_click("assets/buttons/back_btn.png",
                                     region_ltrb=constants.SCREEN_BOTTOM_BBOX)
      return

    info(f"Skill points available: {sp} (buying above {core_config.SKILL_PTS_CHECK}).")
    init_skill_py()
    if buy_skill({"current_stats": {"sp": sp}}, core_config.SKILL_CHECK_TURNS) is False:
      debug("buy_skill declined - below the configured threshold. Not returning here.")
      self.skills_done = True
      device_action.locate_and_click("assets/buttons/back_btn.png",
                                     region_ltrb=constants.SCREEN_BOTTOM_BBOX)

  # --- one tick -------------------------------------------------------
  def step(self) -> bool:
    """Act once. Returns False when nothing was recognised."""
    device_action.flush_screenshot_cache()
    screen, _ = self.identify()

    if screen is None:
      if self.last_screen is not None:
        info("Nothing actionable on screen - waiting (training, loading, or a cutscene).")
        self.last_screen = None
      return False

    if screen.name != self.last_screen:
      info(f"Screen: {screen.name} - {screen.action}")
      self.last_screen = screen.name

    # A career's skill budget resets when its results first appear.
    if screen.name == "training_log":
      self.skill_visits = 0
      self.skills_done = False

    if screen.handler:
      getattr(self, f"do_{screen.handler}")(screen)
    else:
      device_action.locate_and_click(screen.click, confidence=MATCH_THRESHOLD)

    if screen.name == "career_complete":
      self.runs_completed += 1
      info(f"Run finished. Completed this session: {self.runs_completed}.")

    return True


def run() -> None:
  cfg = auto_config.load()
  core_config.reload_config()

  bot.use_adb = core_config.USE_ADB
  if core_config.DEVICE_ID:
    bot.device_id = core_config.DEVICE_ID
  if not bot.use_adb:
    error("Autopilot supports ADB only. Set use_adb in config.json.")
    return

  # Same shift main.py applies for ADB, which puts GAME_WINDOW_BBOX at
  # (0,0,800,1080) and lines the constants up with the emulator frame.
  constants.adjust_constants_x_coords(offset=-155)
  if not init_adb():
    error("Could not reach the device over ADB.")
    return

  pilot = Autopilot(cfg)
  info(f"Autopilot started. Borrow targets: {cfg.borrow_card_targets or '(none configured)'}")

  try:
    while bot.is_bot_running:
      acted = pilot.step()
      sleep(1.0 if acted else cfg.idle_poll_seconds)
  except BotStopException as e:
    info(f"{e}")
  except KeyboardInterrupt:
    info("Interrupted.")
  finally:
    bot.is_bot_running = False
    info(f"Autopilot stopped after {pilot.runs_completed} completed run(s).")
