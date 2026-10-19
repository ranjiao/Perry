# Startup routing

`SKILL.md` owns the ordering. Resolve intent before reading project state.

| Route | Read | Continue |
|---|---|---|
| Explain or help | shipped skill pages and host rendering guidance only | answer; mark optional pack commands conditional |
| Query | config/languages, `reference/recovery.md`, requested native query | answer only the requested fact |
| Change | config/languages, project hook, recovery procedure, affected native projections | load the owning lane and carry out the authorized action |
| Overview | Change safety, `reference/snapshot.md`, `reference/next.md` | compact dashboard and evidence for the suggested next step |

A narrow Query never initializes a store, writes config, scans the whole board
or appends a closing question. Explain never reads project config or selects
packs based on project state. Mixed explanation plus action uses Change.
A user-named action remains the action; recommendations do not override it.

Project state includes config, dossiers, native store/items/events, project
code and narrative attachments. Shipped `$PERRY_HOME` instructions and host
environment detection are not project state. Before state queries the only
permitted project reads are config and the safety paths explicitly enumerated
in `reference/recovery.md`. That procedure stops on blocking recovery and
waits for a user's choice on interrupted work, including before setup.

Run safety once per operation, then refresh after evidence of an external
change. After every write or refusal, re-query the affected native projection.
A paginated capture is valid only at one `store_seq`; never combine pages
from different writes. A failed native read is an error or migration condition,
not permission to use frozen registers or infer state from markdown.

Host detection is once per session. The bounded update check runs only for
Change, at most once per session and subject to its own throttle. Perry has
no session token limit; the agent environment and user own session rollover.
