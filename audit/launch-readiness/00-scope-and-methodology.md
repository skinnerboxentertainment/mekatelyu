# Scope and Methodology

## Audit identity

- Project: Paradisio / `skinnerboxentertainment/mekatelyu`
- Baseline branch: `master`
- Baseline commit: `6f40dd80`
- Audit start: 2026-07-20 (America/Costa_Rica)
- Audit mode: read-only baseline; documentation additions only
- Application/data remediation: requires separate authorization

## Objective

Determine whether the current repository is ready for a public launch, identify reproducible gaps, define initiatives to close them, and retain evidence connecting discovery, remediation, and verification.

## In scope

- Repository structure, maintainability, and build reproducibility
- GitHub Pages deployment artifacts and configuration
- Critical visitor, business-owner, premium, and administrative journeys exposed by the shipped site
- Desktop and mobile visual behavior
- Accessibility fundamentals
- Security, privacy, secrets, and user-input risks appropriate to a static site
- Dependency and supply-chain posture
- Dataset structure, completeness, consistency, and launch-sensitive content
- Performance, resilience, error handling, SEO, and operational controls
- Existing QA and launch documentation, treated as unverified historical input

## Out of scope unless access is supplied

- Formal penetration testing or destructive security testing
- Legal advice or definitive regulatory compliance certification
- Physical-device testing on real iOS/Android hardware
- Verification of every third-party business fact against the real world
- Account-gated third-party systems or payment settlement
- Paid APIs, commercial datasets, or actions that contact businesses

## Evidence rules

1. Findings must be reproducible from the baseline or clearly labeled as suspected risk.
2. Existing reports do not count as current verification until independently reproduced.
3. Passing checks are recorded alongside failures.
4. Every finding receives a stable ID, severity, evidence, impact, and recommended acceptance criterion.
5. `Fixed` and `verified` are separate states.
6. Failed and abandoned remediation attempts remain in the record.
7. Secrets and personal data are never copied into audit documentation; evidence is redacted where necessary.

## Severity model

| Severity | Meaning | Launch posture |
|---|---|---|
| Blocker | Prevents a critical journey, exposes sensitive data, or creates unacceptable legal/security risk | Must resolve before launch |
| High | Materially harms many users, trust, revenue, accessibility, or operations | Resolve before launch unless explicitly accepted |
| Medium | Meaningful defect with workaround or limited reach | Plan and resolve where feasible |
| Low | Minor defect, maintainability risk, or polish issue | May defer with rationale |
| Note | Observation or improvement without a confirmed defect | Optional |

## Planned assessment techniques

- Static repository and configuration inspection
- Clean build/rebuild comparison
- Python syntax and test discovery
- Dependency review and secret-pattern scan
- Dataset profiling and invariant checks
- Local HTTP serving of generated output
- Browser console, network, interaction, and responsive inspection
- Targeted accessibility and semantic checks
- Link, asset, and deep-link validation
- Regression verification for any later authorized remediation

## Completion criteria

The baseline audit is complete when critical journeys have recorded coverage, automated checks have evidence, findings are severity-ranked, readiness gaps have concrete initiatives and acceptance criteria, and the final report states an evidence-based go/no-go recommendation with residual risk.
