# Repository Deprecation Design

**Date:** 2026-08-30  
**Status:** Approved

## Context

This repository preserves tested chat-template patches, regression fixtures,
and source provenance for Qwen3.5, Qwen3.6, and Gemma 4. Qwen3.8 has superseded
the Qwen generations that motivated the repository, so the project will stop
active maintenance while retaining its historical and operational value for
users of the older model families.

## Goal

Turn the repository into an unmistakably frozen historical archive. Readers
must be able to tell immediately that it is unmaintained, that its patches are
limited to the model families already documented, and that they should not
assume compatibility with Qwen3.8 or other newer models.

## Repository Changes

1. Add a prominent deprecation notice at the top of `README.md` stating that
   the repository has been unmaintained since 2026-08-30 because Qwen3.8
   supersedes its tracked Qwen3.5 and Qwen3.6 work.
2. Keep the quick-start and technical documentation available for historical
   users, but label the instructions as applying only to the archived model
   families and artifacts.
3. Replace the active contribution instructions with a frozen-project policy:
   no new patches, model families, or routine maintenance will be accepted.
4. Add a deprecation entry to the Unreleased section of `CHANGELOG.md` so the
   lifecycle change is represented in the repository history.
5. Leave templates, patches, tests, fixtures, provenance records, licenses,
   and source snapshots unchanged.

After the documentation change is committed and published, archive the GitHub
repository so its hosting state agrees with the README. The archive action is
the final step because an archived repository is read-only.

## Verification

- Confirm the deprecation notice is visible before the README introduction.
- Search the README for language that still invites new contributions or
  implies ongoing support, and remove or qualify it.
- Confirm the README still explains how historical users can inspect, test,
  and apply the preserved patches.
- Review the final diff to ensure no patch, template, test, fixture,
  provenance, or source-snapshot content changed.
- Confirm the GitHub repository reports archived status only after the
  documentation commit is available on the remote.

## Non-Goals

- Adding Qwen3.8 support or evaluating whether old patches apply to it.
- Retiring or deleting individual historical patches.
- Removing tests or maintenance scripts; they remain reproducibility tools.
- Redirecting users to a successor repository, because none has been
  identified.
