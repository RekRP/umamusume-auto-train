"""Entry point for the Independent Training autopilot.

  py -3.12 autopilot_run.py

Press F10 at any time to stop. The stop is checked inside every click and
screenshot, so it takes effect immediately rather than at the end of a cycle.
"""

import threading

import core.bot as bot
from utils.log import info, init_logging

from autopilot.loop import run


def watch_for_stop() -> None:
  try:
    import keyboard
  except Exception as e:  # pragma: no cover - depends on the host
    info(f"Hotkey unavailable ({e}); use Ctrl+C to stop.")
    return
  keyboard.wait("f10")
  info("F10 pressed - stopping.")
  bot.is_bot_running = False


if __name__ == "__main__":
  init_logging()
  bot.is_bot_running = True
  threading.Thread(target=watch_for_stop, daemon=True).start()
  info("Press F10 to stop.")
  run()
