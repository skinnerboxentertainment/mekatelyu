# Documentation Inventory

Status date: 2026-07-22
Status values: Active (current, trustworthy) | Historical (point-in-time, may be stale) | Archive (superseded, preserved for reference) | Working (in-progress drafts, not authoritative)

---

## Root (mekatelyu/)

| File | Status | Notes |
|------|--------|-------|
| `README.md` | **Historical** | Public-facing; references 738 count (now 737). Mentions old docs/ structure. Good for project overview but counts are stale. |
| `AGENTS.md` | **Active** | Updated this session with rationale-based safety rules. Current operational protocol. |
| `HANDOVER.md` | **Active** | Entry point for new agents. Points to 13-aug1-release-candidate-handover.md. Current. |
| `TURNOVER.md` | **Historical** | Pre-launch turn-over doc. References 750 records and old features (classifieds, premium). Superseded by turnover_unified.md and the launch-readiness audit. |
| `turnoverCodex.md` | **Historical** | Codex-side turn-over document. Same vintage as TURNOVER.md. Useful cross-reference but counts/data are stale. |
| `turnover_unified.md` | **Historical** | Reconciliation of TURNOVER.md and turnoverCodex.md. Still references 750 records and pre-launch state. Not updated for the Aug 1 reduced release. |
| `SYNC-REPORT.md` | **Working** | Session handover doc from this thread. Useful for ChatGPT sync but not authoritative. |
| `ChatGPT_Screenshot_Analysis.md` | **Working** | UX critique of the business page. Used to inform Tier 1/2 changes. Not operational. |

## CODEX_ENDPOINT/

| File | Status | Notes |
|------|--------|-------|
| `README.md` | **Active** | Protocol docs for the CODEX endpoint bridge. Still current. |
| `SPEC.md` | **Active** | Specifications for the endpoint. Still current. |
| `session_schema.md` | **Active** | Schema docs for session files. Still current. |

## docs/

| File | Status | Notes |
|------|--------|-------|
| `paradisio_build_spec.md` | **Archive** | Original build spec. Pre-dates the reduced release, premium pages, etc. Not current. |
| `paradisio_vision.md` | **Historical** | Original product vision. Useful for long-term direction, not current implementation. |
| `paradisio_direction_unified.md` | **Active** | Design direction (Polished Local Warmth). Still the current design compass. |
| `paradisio_status_and_ideas.md` | **Historical** | Feature inventory and idea list. Many features mentioned (classifieds, premium) are excluded from reduced release. |
| `paradisio_roadmap.md` | **Historical** | Feasibility/ROI analysis. Pre-dates the reduced release scope decision. |
| `paradisio_executive_qa.md` | **Historical** | Executive Q&A from earlier phase. Stale on some specifics. |
| `paradisio_presentation_considerations.md` | **Historical** | Design research. Informative but not current spec. |
| `paradisio_for_kate_edwards.md` | **Archive** | Specific to a previous stakeholder. Not current. |
| `workspace_setup_guide.md` | **Historical** | Setup guide. May have stale path/environment references. |
| `request_classifieds_posting.md` | **Archive** | Research on classifieds posting flow. Classifieds excluded from reduced release. |
| `cid_v2_extraction_methodology.md` | **Historical** | Methodology for a v2 CID re-scan that hasn't been executed. Good reference if re-scan is greenlit. |
| `cid_enrichment_strategy_report.md` | **Historical** | Strategy doc. References old data pipeline. |
| `cid_scan_postmortem.md` | **Historical** | Postmortem on a CID scan. Informative but not current. |
| `AUTOVISUALWHATSAPPCHECKIFIER.md` | **Active** | WhatsApp visual audit specification. The tooling was used and results are in the audit directory. |
| `sponsorship-system-design.md` | **Working** | Draft design for a sponsorship system. Not implemented. |
| `angel-page-design.md` | **Working** | Draft design for the angel investment page. Partially implemented (invest page exists at /invest/). |
| `take-app-evaluation-proposal.md` | **Working** | Research assignment template. Not an evaluation. |
| `take-app-evaluation-complete.md` | **Working** | Completed Take App evaluation. Research output, not operational. |
| `doc-inventory.md` | **Active** | This file. |

## archive/

All files in `archive/` are correctly labeled. They are intentionally preserved historical records.

| File | Status | Notes |
|------|--------|-------|
| `EXECUTIVE_SUMMARY.md` | **Archive** | Superseded executive summary. |
| `ASSESSMENT.md` | **Archive** | Superseded assessment. |
| `ENRICHMENT_STRATEGY.md` | **Archive** | Superseded enrichment strategy. |
| `feasibilityAnalysis.md` | **Archive** | Superseded feasibility analysis. |
| `feasibilityAnalysis_v2.md` | **Archive** | Superseded v2 feasibility analysis. |
| `docs_feasibilityAnalysis_v2.md` | **Archive** | Superseded doc version. |
| `REMAINING_TASKS.md` | **Archive** | Remaining tasks from an earlier phase. Most are resolved or superseded. |
| `requestForSolutions.md` | **Archive** | Historical request doc. |
| `requestForService_CODEX.md` | **Archive** | Historical Codex request. |
| `requestForInvestigation_CODEX.md` | **Archive** | Historical Codex request. |

## audit/launch-readiness/

These are evidence and decision records from the July 20-21 launch readiness audit. They are **historical** — they document what was true at audit time. The release candidate has moved beyond some findings.

| File | Status | Notes |
|------|--------|-------|
| `00-scope-and-methodology.md` | **Historical** | Audit methodology. Good reference. |
| `01-system-inventory.md` | **Historical** | Baseline inventory at commit 6f40dd80. Stale counts. |
| `02-audit-log.md` | **Historical** | Chronological work record. |
| `03-findings-register.md` | **Historical** | Finding IDs and baseline evidence. |
| `04-launch-gap-analysis.md` | **Historical** | Baseline-to-launch gap analysis. |
| `05-remediation-plan.md` | **Historical** | Initiatives and acceptance criteria. |
| `06-change-log.md` | **Historical** | Every authorized local correction. |
| `07-verification-register.md` | **Historical** | Verification evidence. |
| `08-launch-checklist.md` | **Historical** | Control checklist at audit time. Some items now resolved. |
| `09-final-readiness-report.md` | **Historical** | Original no-go recommendation. Historical baseline. |
| `10-visual-product-critique.md` | **Historical** | Desktop/mobile product assessment. |
| `11-authority-tail-handoff.md` | **Active** | Owner decisions required. All 5 decisions have been resolved but the doc remains the correct reference for what was asked. |
| `12-semantic-reenrichment-initiative.md` | **Historical** | Taxonomy/evidence design. Completed locally. |
| `13-aug1-release-candidate-handover.md` | **Active** | **Authoritative handover.** The single most important document for understanding current project state. |
| `14-launch-record.md` | **Active** | Launch commit and artifact record. Created this session. |
| `evidence/` (all files) | **Historical** | Point-in-time evidence snapshots. Useful for audit trail, not current state. |

## audit/entity-resolution/

| File | Status | Notes |
|------|--------|-------|
| `ENTITY-RESOLUTION-SWEEP.md` | **Historical** | Sweep methodology and results. Completed. |
| `ENTITY-RESOLUTION-RESULT.md` | **Historical** | Results of the entity resolution. Completed. |

## audit/whatsapp-checkifier/

| File | Status | Notes |
|------|--------|-------|
| `FULL-AUDIT-REPORT.md` | **Historical** | Full WhatsApp audit report. Completed. |
| `REVIEW.md` | **Historical** | Visual review index. |

## audit/semantic-taxonomy/

| File | Status | Notes |
|------|--------|-------|
| `README.md` | **Historical** | Taxonomy audit overview. |
| `PRIMARY-CATEGORY-REVIEW.md` | **Historical** | Primary category review. Completed. |
| `MAPS-AUTH-COMPARISON-PROTOCOL.md` | **Historical** | Comparison protocol. |
| `CENSUS.md` | **Historical** | Taxonomy census. |

## audit/maps-cid-discovery/

| File | Status | Notes |
|------|--------|-------|
| `FULL-SWEEP-REPORT.md` | **Historical** | CID discovery sweep. Completed. |
| `ALIAS-CONSOLIDATION.md` | **Historical** | Alias consolidation results. Completed. |
| `COLLISION-RECONCILIATION.md` | **Historical** | CID collision reconciliation. Completed. |
| `REMAINING-EVIDENCE-RESOLUTION.md` | **Historical** | Remaining evidence resolution. Completed. |

---

## Summary

| Status | Count |
|--------|-------|
| **Active** | 8 |
| **Working** | 5 |
| **Historical** | 56 |
| **Archive** | 11 |
| **Total** | 80 |

**Active docs an agent should read first:**
1. `audit/launch-readiness/13-aug1-release-candidate-handover.md` — authoritative handover
2. `audit/launch-readiness/11-authority-tail-handoff.md` — owner decisions (all resolved)
3. `audit/launch-readiness/14-launch-record.md` — launch commit record
4. `AGENTS.md` — operational protocols
5. `HANDOVER.md` — agent entry point
6. `docs/paradisio_direction_unified.md` — design direction
7. `docs/AUTOVISUALWHATSAPPCHECKIFIER.md` — WhatsApp audit spec
8. `CODEX_ENDPOINT/README.md` — Codex bridge protocol
