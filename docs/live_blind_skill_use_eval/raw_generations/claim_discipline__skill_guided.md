Adrian, any prose here is AI-assisted working text and is not direct-submission ready until disclosure, accountability, and policy status are explicit.

**Evidence Inventory**

| artifact | evidence use | safe scope |
|---|---|---|
| Preferred DID table | Main estimate for `ln_green_patents`; β = 0.085, SE = 0.031, p < 0.01; city/year FE; city-clustered SE; N = 2,840 city-years | Supports a positive post-pilot change under the DID design and assumptions |
| Event-study figure | Diagnostic; omitted period `t=-1`; CIs shown; most leads near zero, but `lead_1 = 0.040`, p = 0.08 | Mostly reassuring, but one marginal pre-period estimate weakens a strong causal presentation |
| Mechanism table | Positive association between pilot and R&D subsidy receipt | Cannot establish the subsidy channel causally |
| Placebo tests | Not run | Missing robustness/diagnostic evidence |

**Issue Table**

| severity | issue | evidence | why it matters | next action | status |
|---|---|---|---|---|---|
| P1 | Draft overstates causal certainty | “causes”, “proves”; event-study has `lead_1 = 0.040`, p = 0.08; no placebo | DID can support causal interpretation only under assumptions; marginal pre-period movement and missing placebo make “proves” too strong | Replace proof language with AI-disclosed, assumption-bounded working text; explicitly note the event-study diagnostic | overclaim |
| P1 | Mechanism claim exceeds evidence | Mechanism table shows positive association with R&D subsidy receipt, not causal identification | “Through increased R&D subsidies” implies mediation evidence that has not been established | Treat subsidies as suggestive mechanism evidence only; add stronger mechanism design or remove channel language | unsupported mechanism |
| P2 | Magnitude language is not benchmarked | β = 0.085 on log outcome | “major surge” is evaluative and needs a substantive benchmark | Report coefficient, SE, N, FE, clustering, and optional semi-log scale; justify any magnitude adjective with baseline or benchmark | scale ambiguity |
| P2 | Missing placebo diagnostic | No placebo test run | Weakens robustness package for a policy DID claim | Add placebo timing, placebo outcome, or untreated-policy falsification test with a clear null | missing evidence |
| P2 | Outcome-to-capacity leap | Outcome is `ln_green_patents`; draft says “upgrades local innovation capacity” | Capacity is broader than observed green patenting | Keep interpretation tied to measured green patent output unless capacity is separately measured | wrong estimand |

**Claim Ledger**

| claim_id | claim slot | type | support | risk | author action |
|---|---|---|---|---|---|
| C1 | Preferred DID estimate for `ln_green_patents`: β = 0.085, SE = 0.031, p < 0.01; city/year FE; city-clustered SE; N = 2,840 | estimate | strong | scale ambiguity | Use exact estimate and uncertainty |
| C2 | DID interpretation conditional on parallel-trends/identification assumptions | interpretation | partial | causal language | State assumptions and diagnostics |
| C3 | Event-study pre-trend diagnostic: mostly near zero, but `lead_1` marginal at p = 0.08; baseline `t=-1` | diagnostic | partial | fragile pretrend | Acknowledge directly |
| C4 | R&D subsidy channel | mechanism | weak | unsupported mechanism | Present only as association or add evidence |
| C5 | “Proves digital government upgrades local innovation capacity” | interpretation | missing | overclaim | Delete or convert into a bounded author decision |

**Result Section Scaffold**

| paragraph | purpose | evidence to use | author task |
|---|---|---|---|
| P1 | Orient readers to design and preferred model | DID table: outcome, treatment, FE, clustering, N | State what the model estimates and the comparison being made |
| P2 | Present main estimate | β = 0.085, SE = 0.031, p < 0.01; log outcome | Write the magnitude and uncertainty accurately; avoid unsupported magnitude adjectives |
| P3 | Discuss identifying-assumption diagnostic | Event study; omitted `t=-1`; leads and CIs; `lead_1` p = 0.08 | Explain what the pre-period pattern supports and what remains a concern |
| P4 | Handle mechanism evidence | Subsidy association table | Separate suggestive mechanism evidence from causal mediation |
| P5 | State robustness boundary | No placebo test | Decide whether to run placebo checks before submission or disclose the gap |

**Author Decision Questions**

1. Is the paper willing to make a causal DID claim conditional on assumptions, or should it use more guarded language until placebo checks are added?
2. What benchmark justifies calling β = 0.085 substantively large?
3. Should the marginal `lead_1` estimate be addressed in the main text or appendix?
4. Will the subsidy mechanism be tested with stronger design evidence, or framed only as suggestive association?
5. Is “innovation capacity” measured elsewhere, or should the claim stay limited to green patenting?
