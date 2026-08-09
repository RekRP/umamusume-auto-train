import { useState } from "react";
import { Bot, X } from "lucide-react";
import type { Config, UpdateConfigType } from "@/types";
import type { Autopilot } from "@/types/autopilot.type";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { Checkbox } from "../ui/checkbox";
import Tooltips from "@/components/_c/Tooltips";

type Props = {
  config: Config;
  updateConfig: UpdateConfigType;
};

// Used when config.json predates the autopilot block.
const FALLBACK: Autopilot = {
  borrow_card_targets: [],
  borrow_required: true,
  borrow_max_scrolls: 8,
  borrow_match_threshold: 0.8,
  max_skill_visits: 5,
  wait_when_out_of_tp: true,
  idle_poll_seconds: 20,
};

export default function AutopilotSection({ config, updateConfig }: Props) {
  const autopilot = config.autopilot ?? FALLBACK;
  const [draft, setDraft] = useState("");

  const set = (patch: Partial<Autopilot>) =>
    updateConfig("autopilot", { ...autopilot, ...patch });

  const addTarget = () => {
    const value = draft.trim();
    if (!value || autopilot.borrow_card_targets.includes(value)) return;
    set({ borrow_card_targets: [...autopilot.borrow_card_targets, value] });
    setDraft("");
  };

  const removeTarget = (value: string) =>
    set({
      borrow_card_targets: autopilot.borrow_card_targets.filter((t) => t !== value),
    });

  const move = (index: number, delta: number) => {
    const next = [...autopilot.borrow_card_targets];
    const target = index + delta;
    if (target < 0 || target >= next.length) return;
    [next[index], next[target]] = [next[target], next[index]];
    set({ borrow_card_targets: next });
  };

  return (
    <div className="section-card">
      <h2 className="text-3xl font-semibold mb-4 flex items-center gap-3">
        <Bot className="text-primary" />
        Autopilot
      </h2>

      <p className="text-sm text-muted-foreground mb-4">
        Runs Independent Training back to back: borrows a support card, starts the run,
        buys skills when it ends, then starts the next one. Run it with{" "}
        <code className="px-1 py-0.5 rounded bg-muted">py -3.12 autopilot_run.py</code>.
      </p>

      <p className="text-lg font-medium mb-1">Support cards to borrow</p>
      <p className="text-sm text-muted-foreground mb-3">
        Type the card as it appears in the Borrow Card list. The character name on its own
        is enough &mdash; punctuation and unreadable symbols are ignored when matching, so
        <span className="whitespace-nowrap"> &ldquo;[Q&ne;0] Agnes Tachyon&rdquo;</span> and
        &ldquo;Agnes Tachyon&rdquo; both work. Topmost entry wins when several are available.
      </p>

      <div className="flex gap-2 mb-3">
        <Input
          placeholder="e.g. Kitasan Black"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              addTarget();
            }
          }}
        />
        <Button type="button" onClick={addTarget} disabled={!draft.trim()}>
          Add
        </Button>
      </div>

      <div className="flex flex-col gap-2 mb-6">
        {autopilot.borrow_card_targets.length === 0 && (
          <p className="text-sm text-muted-foreground italic">
            No cards yet. With none set the bot stops at the borrow list rather than
            picking something unintended.
          </p>
        )}
        {autopilot.borrow_card_targets.map((target, index) => (
          <div
            key={target}
            className="px-3 py-2 border-2 border-border rounded-lg flex items-center gap-3"
          >
            <span className="text-sm text-muted-foreground w-6">{index + 1}.</span>
            <span className="flex-1">{target}</span>
            <button
              type="button"
              className="px-2 text-muted-foreground hover:text-foreground disabled:opacity-30 cursor-pointer"
              onClick={() => move(index, -1)}
              disabled={index === 0}
              aria-label="Move up"
            >
              &uarr;
            </button>
            <button
              type="button"
              className="px-2 text-muted-foreground hover:text-foreground disabled:opacity-30 cursor-pointer"
              onClick={() => move(index, 1)}
              disabled={index === autopilot.borrow_card_targets.length - 1}
              aria-label="Move down"
            >
              &darr;
            </button>
            <button
              type="button"
              className="px-2 text-muted-foreground hover:text-destructive cursor-pointer"
              onClick={() => removeTarget(target)}
              aria-label={`Remove ${target}`}
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-3 grid-cols-1 gap-2">
        <label className="uma-label col-span-3">
          <Checkbox
            id="borrow-required"
            checked={autopilot.borrow_required}
            onCheckedChange={() => set({ borrow_required: !autopilot.borrow_required })}
          />
          Stop If No Card Matches
          <Tooltips>
            On means the bot stops rather than borrowing a card you did not ask for. Off
            means it closes the list and runs without a borrowed card.
          </Tooltips>
        </label>

        <label className="uma-label">
          <span>Scroll Attempts</span>
          <Tooltips>How far down the borrow list to look before giving up.</Tooltips>
          <Input
            className="w-18"
            type="number"
            min={1}
            value={autopilot.borrow_max_scrolls}
            onChange={(e) => set({ borrow_max_scrolls: e.target.valueAsNumber })}
          />
        </label>

        <label className="uma-label">
          <span>Match Strictness</span>
          <Tooltips>
            How closely a row must match, 0 to 1. Lower tolerates worse text recognition
            but risks borrowing the wrong card. 0.8 is a good default.
          </Tooltips>
          <Input
            className="w-20"
            type="number"
            min={0}
            max={1}
            step={0.05}
            value={autopilot.borrow_match_threshold}
            onChange={(e) => set({ borrow_match_threshold: e.target.valueAsNumber })}
          />
        </label>

        <label className="uma-label">
          <span>Max Skill Visits</span>
          <Tooltips>
            How many times per career the bot may open the skill screen. Caps the loop
            between Complete Career and Learn.
          </Tooltips>
          <Input
            className="w-18"
            type="number"
            min={0}
            value={autopilot.max_skill_visits}
            onChange={(e) => set({ max_skill_visits: e.target.valueAsNumber })}
          />
        </label>

        <label className="uma-label">
          <span>Idle Poll (seconds)</span>
          <Tooltips>
            How often to check the screen while training is running. Training takes about
            50 minutes, so there is no point checking often.
          </Tooltips>
          <Input
            className="w-20"
            type="number"
            min={1}
            value={autopilot.idle_poll_seconds}
            onChange={(e) => set({ idle_poll_seconds: e.target.valueAsNumber })}
          />
        </label>

        <label className="uma-label col-span-3">
          <Checkbox
            id="wait-out-of-tp"
            checked={autopilot.wait_when_out_of_tp}
            onCheckedChange={() =>
              set({ wait_when_out_of_tp: !autopilot.wait_when_out_of_tp })
            }
          />
          Wait When Out Of TP
          <Tooltips>
            A run costs 15 TP and TP regenerates at 1 per 10 minutes, so sustained pace is
            about one run every 2.5 hours. On means wait for TP rather than stopping.
          </Tooltips>
        </label>
      </div>
    </div>
  );
}
