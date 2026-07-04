# Academic Writing Style Guide

This guide ensures analysis explanations read like genuine academic prose, not AI-generated content.

## Core Principles

1. **Let data speak**: Report findings directly without editorializing
2. **Be precise**: Use exact numbers, confidence intervals, effect sizes
3. **Be concise**: One idea per sentence, remove filler
4. **Be objective**: Describe what the analysis shows, not what it "reveals" or "highlights"

## Language Patterns to Avoid

### Weak Verb Constructions

| Avoid | Use Instead |
|-------|-------------|
| "serves as a proxy for" | "proxies" or "measures" |
| "plays a crucial role in" | "affects" or "influences" |
| "is indicative of" | "indicates" |
| "provides evidence for" | "supports" |

### Meaningless Intensifiers

Remove these words entirely—they add no information:

- very, extremely, highly, particularly
- crucial, critical, pivotal, key
- significant (unless statistically)
- groundbreaking, novel, innovative

### Empty Analytical Phrases

These phrases pad word count without adding meaning:

| Remove | Replacement |
|--------|-------------|
| "highlighting the importance of..." | (delete) |
| "underscoring the significance of..." | (delete) |
| "reflecting the continued relevance of..." | (delete) |
| "emphasizing the need for..." | (delete) |
| "suggesting that further research is needed" | specific research direction |

### Formulaic Transitions

| Avoid | Vary With |
|-------|-----------|
| "In summary," | (often unnecessary) |
| "Overall," | (often unnecessary) |
| "In conclusion," | (use sparingly, once at most) |
| "It is worth noting that" | (just state the fact) |
| "Interestingly," | (let readers judge interest) |

### Synonym Cycling

Do not artificially vary terms for the same concept:

- If discussing "income," keep calling it "income"—not "earnings," then "wages," then "compensation"
- Consistent terminology aids clarity

### Trailing Participle Phrases

Avoid sentences ending with `-ing` phrases that add shallow commentary:

**Bad**: "Income has the largest effect, *highlighting its central role in shaping attitudes*."

**Good**: "Income has the largest effect (β = 0.34, 95% CI: 0.28–0.40)."

## Format Patterns to Avoid

### Overuse of Bold

- Bold is for table headers and variable names in technical contexts
- Do not bold for emphasis in prose—let word choice convey importance

### List Dependency

- Prose paragraphs are standard for academic writing
- Use lists only for:
  - Enumerated methods steps
  - Variable definitions
  - Robustness check summaries

### Rigid Templates

- Vary paragraph structure naturally
- Not every section needs the same subheadings
- Adapt to what the analysis actually contains

## Preferred Style

### Sentence Structure

Write sentences that would appear in APSR, AJPS, or JOP:

**Good examples**:
- "The coefficient on education is 0.15 (SE = 0.03), indicating that each additional year of schooling is associated with a 0.15-point increase in support."
- "Model 2 adds demographic controls. The main effect attenuates slightly but remains significant at conventional levels."
- "We find no evidence that region moderates this relationship (interaction p = 0.43)."

**Bad examples**:
- "Interestingly, we observe a highly significant relationship between education and support, highlighting education's crucial role."
- "The results serve as compelling evidence for the importance of socioeconomic factors."

### Numbers and Statistics

- Report exact values: β = 0.23, not "positive and significant"
- Include uncertainty: 95% CI [0.15, 0.31] or SE = 0.04
- Use consistent decimal places (typically 2-3)
- Write out numbers below 10 in prose, use digits for 10+

### Hedging Appropriately

Use hedging that reflects actual uncertainty:

| Appropriate | Inappropriate |
|-------------|---------------|
| "The results suggest..." | "The results prove..." |
| "consistent with the hypothesis" | "confirms our theory" |
| "We find evidence that..." | "We demonstrate that..." |

But do not over-hedge:

| Appropriate | Over-hedged |
|-------------|-------------|
| "X affects Y" | "X may potentially have some effect on Y" |

### Discussing Limitations

Be specific, not performative:

**Good**: "Our measure of political interest is single-item, which may attenuate estimates due to measurement error."

**Bad**: "This study has limitations. Future research should address these limitations."

## Checklist Before Finalizing

- [ ] No sentences end with "-ing commentary phrases"
- [ ] No "highlighting/underscoring/emphasizing" phrases
- [ ] Key statistics include uncertainty measures
- [ ] Terminology is consistent throughout
- [ ] Bold used sparingly (tables only)
- [ ] Lists used only where genuinely clearer than prose
- [ ] Opening does not start with "This analysis..."
- [ ] No "It is worth noting" or "Interestingly"
