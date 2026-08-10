# Autopilot

Runs **Independent Training** back to back, unattended: borrows a support card,
starts the run, buys skills when it ends, returns Home, and starts the next one.

The game's Independent Training does the training itself. This only handles the
parts it can't: setting a run up, and clearing up afterwards.

## Requirements

- **ADB, not window capture.** `use_adb` must be on, with `device_id` pointing at
  your emulator (MuMu's default is `127.0.0.1:5555`).
- **An 800x1080 portrait frame.** Every template ships cut from that exact
  resolution, and template matching is pixel-exact. A different emulator
  resolution will fail to match anything. Check the first line the capture tool
  prints:
  `py -3.12 autopilot/tools/capture.py --session check` reports the frame size.
- **The Global client, in English.** Card and skill names are matched as English
  text.
- Python 3.10-3.13, and the repo's usual `pip install -r requirements.txt`.

## Setup

1. Start the config server as normal: `py -3.12 main.py`
2. Open the URL it prints and go to the **Autopilot** tab.
3. Add the support card you want to borrow. Pick from the card list, or type a
   name - the character name alone is enough.
4. Turn on **Auto Buy Skills** and choose skills in the Skill List section on the
   same tab, if you want it spending points.
5. Save Changes.

## Running

Press **F2** in the `main.py` window to start and stop it. F1 still runs the
normal bot; only one of the two runs at a time.

`py -3.12 autopilot_run.py` runs it standalone if you prefer a separate window.

## Settings

| Setting | What it does |
| --- | --- |
| Support cards to borrow | Priority order; the topmost available one wins |
| Stop If No Card Matches | Stop rather than borrow a card you didn't ask for |
| Scroll Attempts | How far down the borrow list to look |
| List Reloads | Reload the list for a different set of friends when none match |
| Match Strictness | How closely a row must match, 0-1. 0.8 is a good default |
| Load Saved Agenda | Load the first entry under My Agendas before each run |
| Spend Leftover Points | After your skill list, buy anything else affordable |
| Max Skill Visits | Cap on reopening the skill screen per career |
| Idle Poll | How often to check while training runs |
| Wait When Out Of TP | Wait for TP rather than stopping |

## Things worth knowing

**A run costs 15 TP, and TP regenerates at 1 per 10 minutes.** Training itself
takes about 50 minutes, so the sustained rate is roughly one run every 2.5
hours - TP is the limit, not time. Expect it to idle between runs.

**Scenario Select is a carousel.** The bot presses Next on whichever scenario is
showing; it does not pick one. Leave the right scenario selected.

**It only clicks templates it has matched.** On a screen it doesn't recognise it
does nothing, so an unknown popup stalls it rather than misclicking. If it sits
at `Nothing actionable on screen` forever, it has hit a screen with no rule -
capture it and it can be added.

## Reporting a problem

Run with `--debug` and include the log. `autopilot/tools/whereami.py` reports
what the bot thinks it is looking at without ever clicking, which is the
quickest way to tell a detection problem from an action one.
