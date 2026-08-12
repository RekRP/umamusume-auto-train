# Autopilot

Runs **Independent Training** back to back, unattended: borrows a support card, starts the
run, buys skills when it ends, returns Home, and starts the next one.

The game trains the uma by itself. This only does the parts it won't.

---

## Two things that fail silently

Get these wrong and the bot starts, does nothing, and never errors. Check them first if
anything seems broken.

**1. The emulator must be exactly 800 x 1080.** Every button it looks for was cut from a
frame at that size, and matching is pixel-exact. At any other resolution nothing matches.

**2. It reads the screen over ADB, not the window.** With ADB debugging off it cannot see
the game at all.

---

## 1. Install MuMu Player

Get it from [mumuplayer.com](https://www.mumuplayer.com/), install Umamusume inside it, and
sign in. Make sure you can start a career by hand first.

## 2. Set the display

**Device Settings → Display**, set Resolution settings to **Custom**:

| | |
| --- | --- |
| Resolution settings | `Custom` |
| Width | `800` |
| Height | `1080` |
| DPI | `240` |

Restart the emulator afterwards.

## 3. Turn on ADB

**Device Settings → Developer options**:

| | |
| --- | --- |
| ADB debug | `Enable local connection` |
| Enable root | `Off` |

Root is not needed.

## 4. Get the bot

It lives on the `autopilot` branch. Cloning without `-b autopilot` gets you the version
without any of this.

```
git clone -b autopilot https://github.com/oHaruki/umamusume-auto-train.git
cd umamusume-auto-train
pip install -r requirements.txt
```

Python 3.10 to 3.13.

## 5. Point it at the emulator

```
py -3.12 main.py
```

Open the address it prints, go to **Set-Up**:

| | |
| --- | --- |
| Use ADB | on |
| Device ID | `127.0.0.1:5555` |

That is MuMu's default. Other emulators use a different port.

## 6. Choose your card and skills

On the **Autopilot** tab:

- **Support cards to borrow** — pick from the card list or type a character name. Add
  several in priority order; the friend list changes every run, so backups mean fewer
  reloads.
- **Auto Buy Skills** — turn on, then choose skills in the Skill List below.
- **Spend Leftover Points** — buys anything else affordable once your list runs out.

Press **Save Changes**.

## 7. Set the game up by hand, once

The bot repeats a run you have already configured. It does not make these choices for you:

- **The trainee** — whoever is selected on Trainee Select is who it trains, every run.
- **The parents** — inheritance must be picked in advance. The bot passes that screen
  through untouched.
- **The scenario** — Scenario Select is a carousel and it presses Next on whatever is
  showing. Leave the right one on screen.
- **The agenda, in the first slot** — if you use *Load Saved Agenda* it always loads the
  top entry under My Agendas.
- **The support deck** — only the borrowed friend slot is filled automatically. Your own
  five come from the saved formation.

One choice it *does* make: while an event is running, Next on Scenario Select opens *Choose
Career Mode*. The bot always picks **Normal Mode** — it will not take a Trainer Aptitude
Test for you.

## 8. Run it

With `main.py` running, press **F2** to start and stop the autopilot. **F1** still runs the
normal training bot; only one of the two runs at a time.

`py -3.12 autopilot_run.py` runs it standalone if you prefer a separate window.

---

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

## Pace

A run costs **15 TP**, and TP refills at **1 per 10 minutes**, while training takes about
**50 minutes**. So the steady rate is roughly **one run every 2.5 hours**, and it will idle
in between. That is TP, not the bot.

---

## Troubleshooting

**It starts, then does nothing.** Almost always the resolution. Check what the bot sees:

```
py -3.12 autopilot/tools/capture.py --session check
```

The first line reports the frame size. Anything but 800 x 1080 means nothing can match.

**It can't reach the device.** ADB debug is off, the emulator isn't running, or the Device
ID is wrong.

**It stops at the borrow list.** None of your cards were there and *Stop If No Card
Matches* is on. Add more cards, raise *List Reloads*, or turn that setting off.

**It sits on "Nothing actionable on screen".** Normal during training and loading screens.
If it never moves on it has hit a popup with no rule for it — note which screen.

**It didn't buy skills.** *Auto Buy Skills* is off, or nothing on your list was available.
The log says which.

**Anything else.** Run with `--debug` and include the log. `autopilot/tools/whereami.py`
reports what the bot thinks it is looking at without ever clicking, which separates a
seeing problem from a doing one.

---

Built on [umamusume-auto-train](https://github.com/samsulpanjul/umamusume-auto-train).
Global client, English text.
