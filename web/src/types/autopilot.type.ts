import { z } from "zod";

export const AutopilotSchema = z.object({
  // Support cards to borrow, best first. Written as they appear in game;
  // matching normalises punctuation, so "[Q!=0] Agnes Tachyon" and the real
  // "[Q<>0] Agnes Tachyon" both resolve to the same card.
  borrow_card_targets: z.array(z.string()).default([]),
  // Stop rather than borrow something unintended when no target is found.
  borrow_required: z.boolean().default(true),
  borrow_max_scrolls: z.number().default(8),
  borrow_match_threshold: z.number().default(0.8),
  // Load a saved race agenda before each run, always the first one listed.
  use_agenda: z.boolean().default(false),
  // Cap on Skills visits per career, so a career cannot loop forever between
  // Complete Career and the Learn screen.
  max_skill_visits: z.number().default(5),
  wait_when_out_of_tp: z.boolean().default(true),
  idle_poll_seconds: z.number().default(20),
});

export type Autopilot = z.infer<typeof AutopilotSchema>;
