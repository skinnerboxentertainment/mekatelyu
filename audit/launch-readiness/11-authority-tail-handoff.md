# Authority-tail handoff

The autonomous local phase is complete. These steps were intentionally deferred because they change shared/external state or require owner judgment.

## Required owner decisions

1. **Catalog risk:** approve launch with the documented stale/unknown/duplicate population, authorize a deterministic exclusion policy, or assign manual record review. No ambiguous business record was autonomously deleted or rewritten.
2. **Correction ownership:** name the person who will monitor and resolve the public `data-correction` GitHub issues.
3. **Legacy repository material:** authorize deletion from the current branch of obsolete `docs/` output, tracked agent sessions/logs/checkpoints, and public invoice/admin material. Decide separately whether Git history rewriting is warranted; history rewriting is disruptive and is not assumed.
4. **Manual accessibility/device check:** identify available iOS/Android devices and, if possible, a screen-reader tester; record any accepted limitations.
5. **Release ownership:** name the person authorized to approve deployment and rollback on August 1.

## Source-control steps requiring approval

1. Review the complete local diff on `launch/aug1-directory-base`.
2. Decide whether legacy-file cleanup belongs in the same change or a preceding privacy cleanup.
3. Authorize a local commit with an agreed message.
4. Authorize pushing the launch branch and opening/reviewing a pull request.
5. Confirm the remote `Launch readiness` workflow passes and inspect the uploaded `paradisio-reduced-release` artifact.
6. Protect `master`: require pull requests, the launch-readiness check, and restricted direct pushes.

## Deployment steps requiring approval

1. Add/approve the deploy job only after the CI artifact has been reviewed. The prepared workflow currently **does not deploy**.
2. Change GitHub Pages from legacy `master:/docs` publication to the approved Actions artifact.
3. Deploy `release/` so the root redirect and existing `/paradisio_app/` profile/QR URLs remain stable.
4. Run production smoke checks: root redirect, home data load, search, grouped category, map, representative active/closed profiles, QR image/download, correction link, sitemap, robots, and 404.
5. Record the deployed commit and artifact tree hash.
6. Rehearse rollback to the previous known-good artifact/commit before announcing launch.

## Go/no-go rule

Go only when remote CI passes, the exact artifact is approved, legacy privacy exposure has an explicit disposition, the catalog risk is accepted or reduced, production smoke checks pass, and a rollback owner is present.

No commit, push, pull request, Pages-setting change, deployment, or history rewrite has been performed by the autonomous phase.
