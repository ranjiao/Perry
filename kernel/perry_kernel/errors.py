"""Error codes, their exit codes, and the one exception every refusal raises.

`kernel/ARCHITECTURE.md` § 5.1 is the table this mirrors. `describe` reports
it from here, so the declaration and the behaviour cannot drift apart.
"""

from __future__ import annotations

#: code -> (exit code, when it is raised). The order is the document's.
ERRORS: dict[str, tuple[int, str]] = {
    "usage": (2, "an unknown command, an undeclared flag or positional, a flag "
                 "this command does not honour, or a missing flag argument"),
    "input_invalid": (2, "--input is not exactly one JSON object, or a declared "
                         "key has the wrong JSON type"),
    "unknown_key": (2, "the input carries a key the command does not declare, "
                       "at any declared level"),
    "actor_invalid": (2, "a write has no actor, the actor's kind is not human or "
                         "agent, its name is empty, or an agent has no session"),
    "anchor_not_found": (1, "no directory holding .perry/ at --root, at "
                            "PERRY_PROJECT, or above the working directory"),
    "store_missing": (1, "the resolved store has not been initialised"),
    "store_foreign": (1, "the file at the store path is not a kernel store; it "
                         "is never overwritten"),
    "store_version": (1, "the store's format is newer than this kernel"),
    "store_busy": (1, "the write lock was not acquired within 5 s"),
    "store_corrupt": (1, "sqlite3 reports damage, or a row cannot be read back"),
    "store_live_under_test": (1, "PERRY_KERNEL_TESTING is set and the store path "
                                 "was derived, not named"),
    "store_initialized": (1, "init on a store initialised with a different "
                             "state root"),
    "store_not_empty": (1, "import into a store that holds any event"),
    "io_error": (1, "a file the command must read or write could not be"),
    "no_template": (1, "an item, relation, attachment or query command before "
                       "any template is applied"),
    "template_invalid": (1, "the template breaks format 1"),
    "template_version": (1, "version is not above the applied one, or equals it "
                            "with different content"),
    "template_incompatible": (1, "the new version would strand stored data"),
    "item_not_found": (1, "an id in the input, a ref value or a relation end "
                          "does not exist"),
    "id_exhausted": (1, "a type's ids have reached 2^53, the highest number "
                        "an id may carry; none is left to mint"),
    "unknown_type": (1, "the applied template declares no such type"),
    "unknown_field": (1, "the applied template declares no such field"),
    "unknown_transition": (1, "the applied template declares no such transition"),
    "unknown_relation": (1, "the applied template declares no such relation kind"),
    "field_invalid": (1, "a value does not fit its field's kind"),
    "metric_invalid": (1, "a metric value breaks the metric rules"),
    "transition_not_allowed": (1, "the item's state is not in the transition's "
                                  "from"),
    "guard_refused": (1, "one or more refuse-mode guards failed"),
    "relation_invalid": (1, "a self-edge, an end whose type the declaration does "
                            "not allow, a duplicate edge, or a second parent"),
    "relation_cycle": (1, "a blocks or parent edge would close a cycle"),
    "stale_write": (1, "an item named in expect has moved"),
    "attachment_invalid": (1, "an empty ref, a ref containing a line break, a "
                              "duplicate ref, or a malformed hash"),
    "export_dir_foreign": (1, "the export directory holds an entry other than "
                              "the kernel's two files"),
    "export_missing": (1, "import finds no export"),
    "export_invalid": (1, "an export line or seq run is malformed, or a replayed "
                          "before value does not match"),
    "replay_mismatch": (1, "replaying the events does not reproduce items.jsonl"),
    "internal": (3, "an unexpected fault; the transaction was rolled back"),
}

#: The one warning code (§ 5.1).
WARNINGS = {"limit_exceeded": "a warn-mode limit guard failed"}

#: § 5.6's three error sets.
SET_A = ("usage", "input_invalid", "unknown_key", "internal")
SET_S = SET_A + ("anchor_not_found", "store_missing", "store_foreign",
                 "store_version", "store_busy", "store_corrupt",
                 "store_live_under_test", "io_error")
SET_W = SET_S + ("actor_invalid",)

EXIT_CODES = {"0": "success", "1": "refused", "2": "bad invocation",
              "3": "internal fault (rolled back)"}


class KernelError(Exception):
    """A refusal. Raised anywhere, caught once at the top (NN-K6)."""

    def __init__(self, code: str, message: str, details=None):
        if code not in ERRORS:
            raise ValueError(f"undeclared error code {code!r}")
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details if details is not None else {}

    @property
    def exit(self) -> int:
        return ERRORS[self.code][0]
