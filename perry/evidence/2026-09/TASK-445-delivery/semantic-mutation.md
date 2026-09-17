# Missing USER before action — bounded semantic mutation

Synthetic scenario 2, baseline: User says “Use CSV.” PMO calls ask, receives
USER-102, calls answer with “Use CSV.”, then CSV implementation proceeds.

Mutation: retain the same utterance and implementation, but delete the ask and
answer steps; implementation proceeds before any USER record exists.

Implementer semantic verdict: REJECT. The new shared Record before action rule
requires the record even for an immediately answered choice. An explicit user
utterance makes recording possible; it does not remove the recording requirement.
This rejection is an agent judgement, not a writer refusal or automated semantic
test. No Python classified the utterance and no stores were written.

Revert: restore ask -> returned USER-102 -> answer “Use CSV.” -> action.
Implementer semantic verdict: PASS for the ordering and authority distinction.
Fresh V4 must independently judge these claims against the spec and four examples.
