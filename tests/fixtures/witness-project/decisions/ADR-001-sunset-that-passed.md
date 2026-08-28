# ADR-001: The sunset that already passed

> Type: Process
> Status: Active
> Date: 2026-06-01
> Sunset: 2026-06-30
> Deciders: Witness Project

## Context

`perry-decide list` reports an `active` decision whose sunset date is in the
past under `expired_sunsets`. Perry's own `decisions/` has no such row, so the
three keys of that entry have never been compared against a payload.

## Decision

This decision carries a sunset date of 2026-06-30 and stays `active`, on
purpose and permanently. It is the collection's only member.

## Consequences

- `perry-decide list --root tests/fixtures/witness-project` emits one
  `expired_sunsets` entry, for as long as today is after 2026-06-30.
- Nothing else in Perry reads this file.
