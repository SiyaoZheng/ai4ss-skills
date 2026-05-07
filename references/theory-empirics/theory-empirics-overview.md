# Theory-Empirics Isomorphism

> Based on: Spirling & Stewart (2024) "What Good is a Regression?", Ashworth, Berry & Bueno de Mesquita (2021) "Theory and Credibility", Granato, Lo & Wong (2021) "EITM"
> Created: 2026-05-07

## Summary

A good research design requires **isomorphism** between theory and empirics — they share the same conceptual structure, connected by two types of relations. The bridge between them is **commensurability**: whether the theory's implications and the empirical estimates describe the same all-else-equal relationship in the same target.

Judged through the lens of **Inference to the Best Explanation (IBE)**, every credible contribution has three components: explanations (theory), facts (evidence), and a bridge (updating beliefs). A study can focus on any one without being invalid — but must be explicit about which part it contributes to.

## Two Relation Types

All social science concepts are connected by exactly two relations.

### Constitutive (θ)

How a concept is **defined** by its constituent attributes or sub-concepts.

- Direction: attribute → concept
- Question: "What does this concept consist of?"
- Encoded as a truth table (θ): for each combination of parent values, is the concept present?

### Causal (→)

How one concept **causally affects** another, all else equal.

- Direction: cause → effect
- Question: "What happens to Y if I change X?"
- Attributes: direction (positive/negative/null), condition, mechanism

## Commensurability: The Bridge

| | Theory side | Empirics side |
|---|---|---|
| Entity | Model with primitives and endogenous outcomes | Research design with measures and estimands |
| Output | Pertinent implications (all-else-equal) | Estimates (all-else-equal, when credible) |
| Quality criterion | Implications depend on representational features, not auxiliary assumptions | Measures are valid; identification assumptions plausible for target |
| Connected by | ⟸ Commensurability ⟹ | |

Commensurability is **strong** when theory and empirics describe the same all-else-equal relationship in the same target. It is **weak** when theory predicts an all-else-equal relationship but empirics estimate a raw correlation, or when they target different populations.

## IBE: Three Components

### Explanations (Theory)

What mechanisms might explain the phenomenon? Good explanations are general, elaborated, transportable, and falsifiable.

### Facts (Evidence)

What do we observe? Good facts are credibly estimated, commensurable with theoretical implications, and robust.

### Bridge (Updating)

How do the facts change beliefs about the explanations? Good bridging states which explanation is tested, how evidence discriminates, and reports null results.

## Signs of Weak Design

- **Causal two-step**: adding controls "as if" causal while disclaiming causal interpretation
- **HARKing**: Hypothesizing After Results are Known
- **PEACHing**: Presenting Explorations As Confirmable Hypotheses
- **Incommensurability**: theory and empirics describe different relationships or targets
- **Single-test fragility**: one implication, one test, one estimate
- **Null hypothesis testing only**: no competing explanation in view

## Principles

1. **Isomorphism.** Theory and empirics share the same concepts and relation types. If the theory posits X → Y but the empirics measure Z correlated with W, the design is incoherent.

2. **Commensurability is necessary.** A causally identified estimate with no theoretical connection is a fact without explanation. An elaborate theory with no credible test is explanation without evidence.

3. **All three IBE components matter.** A study can focus on generating explanations, producing facts, or bridging them. Evaluate a contribution on its own terms.

4. **Ruling out is progress.** A null result that eliminates a plausible explanation advances knowledge. The file drawer problem is anti-scientific.

5. **Elaboration over single tests.** Multiple implications tested with multiple methods.
