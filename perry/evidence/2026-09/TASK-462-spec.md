# TASK-462 — product versions and verified release updates

Date: 2026-09-16. Owner: Coding Agent. Rung: V3 plus independent architecture
review. Dispatch mode: auto. Executor: codex. Deployed: no.
Touches architecture: root NN-3/NN-4/NN-5; bin argument/update behavior.
Subjective verification: none. User approved the preceding proposal in chat:
"可以 按照这个方案做". This authorizes implementation, not live publication.

## Deliverable

1. Establish 0.1.0 at phase 004-guided as the current baseline; no historical
   release fabrication. User controls major increments (reset minor/patch),
   a newly started phase increments minor and resets patch, each integrated
   task delivery increments patch. A repeated task can have multiple distinct
   deliveries; duplicate delivery identifiers refuse. Task closure, PMO-only
   evidence/state commits and synchronization merges do not increment.
2. Agent-authored structured release records are authoritative; VERSION and
   CHANGELOG.md are deterministic projections. Text is opaque agent-authored
   prose, never interpreted by Python. Typed metadata includes version, date,
   phase, kind, task/delivery identity, change notes and upgrade/breaking notes.
   Keep this small and repository-local under release/, outside project-state
   schema/claims. No changes to generic clients' state namespace.
3. A stdlib release tool supports show/check, allocating patch/phase/major
   entries with explicit metadata, rendering and extracting release notes.
   Main integrator allocates versions, coding agents submit notes. Refuse
   malformed/out-of-order/duplicate versions, drift and missing notes. Major
   allocation requires an explicit human-decision reference (not inferred
   authorization); documentation requires the user's actual prior approval.
   Writes are recoverable: interruption cannot silently leave an accepted
   mixed version/changelog/record set; refuse or explicitly repair projections.
4. Merge/CI validation compares to an explicit base and rejects product changes
   without a new release entry; permit precisely documented PMO-only changes.
   Initial introduction is 0.1.0 and includes this task without bumping itself.
   A deterministic check cannot judge notes' quality: review remains agent-owned.
5. Release preparation is reproducible from an immutable version commit/tag,
   verifies VERSION/notes match tag, and runs tests before publishing. Provide
   a manually triggered GitHub release workflow (or equally concrete manual
   procedure) using the changelog notes. Never overwrite an existing tag/release;
   no live remote mutation during this task. Explain remote required checks are
   separate admin configuration, not enforced merely by adding workflow YAML.
6. Consumer update defaults to the latest non-draft/non-prerelease GitHub
   Release, verifies its tag and VERSION, shows current/available version and
   release changes, and updates only a clean safe checkout without discarding
   local commits. No fallback to unverified main when releases are absent or
   network/metadata validation fails. After first update, subsequent updates
   still work (including release-detached HEAD). Numeric version comparison
   prevents downgrades; refuse unrelated history or unexpected tag/version.
   Developer signals (symlink, dirty tree, feature branch/local work) retain
   main comparison/report-only behavior. Preserve force/quiet/strict and
   portable host lookup. Downloads/requests are bounded. No new dependency.
7. Document phase/start and task/integration responsibilities, compatibility
   warnings (this is not strict SemVer), developer vs consumer update behavior,
   publishing and recovery. Changes affect Perry's own product version only;
   Perry must not automatically version every project it manages.

## Files in scope

Authorization addendum (2026-09-16): after being told that the concrete
release component entry and final validation remained before merge, the user
said "好 把工作merge到main". This approves the exact entry in
TASK-462-architecture-proposal.md for ARCHITECTURE.md section 2 and local
main integration. No other architecture rules or remote publication are authorized.


VERSION, CHANGELOG.md, release/; .github/workflows/ci.yml and a release workflow;
bin/perry-update-check and its helper if necessary; README.md, AGENTS.md (keep
under roughly 60 lines), release documentation, narrowly relevant maintenance
references; targeted tests, tests/durations.json, tests/run only if needed for
mechanical release checking; this task's result evidence.

## Verification

- Temporary Git repositories exercise valid/invalid bump sequences, repeated
  phase/delivery, reset behavior, stale/mismatched projections, missing notes,
  product-change no-bump and PMO-only no-bump; test interrupted writes/recovery.
- Mock GitHub responses and local Git remotes exercise new release, no release,
  malformed metadata, mismatch, downgrade, local work protection, dirty and
  symlink developer behavior, first and second update, strict/offline behavior.
  Never contact the real remote or update the installed checkout during tests.
- Validate release tag/commit binding and release note extraction; refuse
  moving/reusing tags. Test workflow commands locally where possible; remote
  execution must remain explicitly unclaimed.
- Independent reviewer checks written criteria and architecture. Author runs
  targeted tests; parent runs full and slow suites on the final merged preview,
  with PYTHONPATH/PERRY_PROJECT/PERRY_HOME unset, and git diff --check.

## Out of scope

Live tags, pushes, GitHub Releases, branch-protection edits, host installation,
automatic major decisions, generic project-state schema/claim changes,
unapproved architecture changes, TASK-264 remaining scope, unrelated cleanup.

## Dispatch safety judgment

All targets are this repository's source/docs/tests. The hook names publication
and self-update: this round implements those paths and tests them only in
temporary repositories with mocked network; it does not perform those actions
against live installations or remotes. No hook/claim surface changes, no external
project writes. User approval covers this local implementation and its workflow
configuration; publishing remains a separate final action.
