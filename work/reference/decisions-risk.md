# Human questions and risks

Read `kernel.md`. Query pending `ask` items for `nudge`, and open `risk` items for
`risk`. Page through complete results when making a count or whole-queue claim.
Use the item's events for creation/update times; report unknown dates honestly.

A human question states the decision, consequences, blockers and recommendation
in at most 600 characters when the existing decision-card rule applies. Create
an `ask`, adding `blocks` relations to actual task IDs. Record the user's real
answer with transition `answer`; a recommendation or silence is not an answer.
An input is not a task merely because both are waiting for action.

If an unanswered input prevents work, move the affected task with transition
`block`, setting a reason that names the ask and a concrete next_action. Continue
independent work within the authorized scope. Re-read dependencies after answers;
an answered ask alone does not mean the task's acceptance criteria passed.

A risk is a `risk` item with a `concern`. Clear it only with evidence and a reason
using transition `clear`. Do not maintain another current risk/ask register in
markdown. Narrative reports cite these items. ADRs and design decisions belong
to the decide lane; propose a cross-lane handoff, never write its files here.
<!-- next-close: work risk --> <!-- next-close: work nudge -->
