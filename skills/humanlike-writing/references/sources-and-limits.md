# Sources, provenance, and limits

## What this package captures

This skill captures the source conversation's research catalog, the user's strict writing preference, and corrections needed to preserve truth and task formats. The pattern catalog is a completeness ledger for that conversation, not a claim that all possible AI writing traits have been discovered.

The examples are original illustrations. They are not real accusations, measured detector results, or quotations from the source pages. Evidence labels distinguish empirical correlations, human/editor observations, tool-specific checks, contextual artifacts, and technical detector signals.

## Anthropic creator provenance

- Creator: https://github.com/anthropics/skills/tree/main/skills/skill-creator
- Guidance read: https://raw.githubusercontent.com/anthropics/skills/main/skills/skill-creator/SKILL.md
- Latest creator-path commit observed: `b0cbd3df1533b396d281a6886d5132f623393a9c`
- Retrieval date: 2026-10-04.
- Applied structure: YAML name/description, a concise entry point, progressive references, realistic paired smoke evaluations, grading evidence, official static viewer, official validator, and official packaging script.
- The skill does not require Anthropic services. Native Codex agents are used for local evaluations; those runs are not Claude runtime validation.

## Research and official detector documentation

- Wikipedia field guide: https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing
- Russell et al., expert-reader and humanization study: https://arxiv.org/html/2501.15654v2
- Desaire et al., science-writing stylometry: https://pmc.ncbi.nlm.nih.gov/articles/PMC10328544/
- Linguistic characteristics survey: https://arxiv.org/abs/2510.05136
- Georgiou, extracted linguistic features: https://arxiv.org/abs/2407.03646
- Kobak et al., biomedical vocabulary changes: https://arxiv.org/abs/2406.07016
- DetectGPT: https://arxiv.org/html/2301.11305v2
- Binoculars: https://arxiv.org/html/2401.12070v3
- GPTZero architecture clarification: https://support.gptzero.me/articles/9585228410-how-do-i-interpret-burstiness-or-perplexity
- Turnitin report limitations: https://guides.turnitin.com/hc/en-us/articles/22774058814093-Using-the-AI-Writing-Report
- TH-Bench humanization trade-offs: https://arxiv.org/abs/2503.08708
- RAID robustness benchmark: https://arxiv.org/abs/2405.07940

## Editorial and tool-specific catalogs

- Prowlo checker: https://prowlo.com/tools/ai-writing-checker
- Prowlo vocabulary: https://prowlo.com/blog/ai-words-to-avoid
- Prowlo reader guide: https://prowlo.com/blog/signs-of-ai-writing
- CounterWord: https://counterword.eu/style-checker
- Prose Coach rhythm guide: https://www.prose.coach/blog/sentence-rhythm-and-ai-detection
- Text Humanize methodology: https://text-humanize.com/how-it-works
- Text Humanize patterns: https://text-humanize.com/blog/common-ai-writing-patterns
- Humanizer rule catalog: https://github.com/conorbronsdon/avoid-ai-writing/blob/main/references/patterns.md
- Humanize research/rules: https://github.com/harshaneel/humanize
- Tropes directory: https://tropes.fyi/directory
- Simon Willison's cliché highlighter: https://tools.simonwillison.net/llm-cliche-highlighter

These URLs were used in the source conversation. Do not claim they have been reread in a later session unless you actually retrieve them. Live pages and products change.

## Corrections the agent must retain

- Style is not authorship proof. Models learn human writing; people use all these devices too.
- Current commercial classifiers are not universally a word blacklist or a perplexity/burstiness formula. GPTZero's cited support page says its detection architecture changed in autumn 2023. Verify current architecture before discussing a product.
- Em-dash frequency changes across models, genres, eras, and editing habits. The no-em-dash rule is this user's preference, not a validated universal discriminator.
- Both unjustified confidence and redundant hedging are editable defects. Removing all hedges damages accuracy; adding "probably" to settled facts also damages accuracy.
- Function words, noun density, syntax, lexical diversity, token rank, curvature, and cross-perplexity are aggregate measurements. A demonstration sentence is not a measurement, and there is no universal required score for good prose.
- Formal grammar, technical terminology, consistent paragraphs, or low vocabulary variety can occur in legitimate human writing. Do not deliberately introduce errors.
- Rewriting may alter detector behavior while changing meaning or quality. Do not promise undetectability, optimize a bypass score, or invent benchmarks.
- Tool tracking/markup can show chatbot involvement without showing that the whole document was generated. Links can die for ordinary reasons.
- Wikipedia templates, review status, editorial behavior, and heading conventions are context-specific. They are not universal human-writing criteria.
- "Read everything" cannot establish exhaustive coverage of the internet. Report the actual source set and inspected content, not an unbounded research claim.
- A custom-instruction block is not automatically a loaded skill. Installation and attachment capabilities depend on the host. Do not claim automatic activation everywhere.

## Verification claims

Distinguish structural validation, deterministic checker tests, native-agent examples, subjective human review, platform installation, and actual model triggering. Report only the checks performed. A small paired smoke evaluation is useful evidence of instruction following, not a statistical quality benchmark or a guarantee for future sessions.

## Catalog source keys

Row pointers identify the source catalog or research family supporting the observation. They do not imply that each rule or repair was empirically validated. Editorial labels remain editorial; strict bans and numeric review thresholds are user preferences. Read the linked source before making stronger claims. The source conversation grouped some evidence broadly, so context and limitations must accompany its use.

### Source desaire

Science-writing stylometry: https://pmc.ncbi.nlm.nih.gov/articles/PMC10328544/

### Source rhythm

Sentence rhythm editorial guide: https://www.prose.coach/blog/sentence-rhythm-and-ai-detection

### Source counter

CounterWord disclosed style checks: https://counterword.eu/style-checker

### Source th-method

Text Humanize disclosed checks: https://text-humanize.com/how-it-works

### Source kobak

Biomedical excess-vocabulary research: https://arxiv.org/abs/2406.07016

### Source russell

Expert-reader study: https://arxiv.org/html/2501.15654v2

### Source prowlo-vocab

Prowlo vocabulary guide: https://prowlo.com/blog/ai-words-to-avoid

### Source prowlo-check

Prowlo disclosed checker patterns: https://prowlo.com/tools/ai-writing-checker

### Source prowlo-guide

Prowlo reader observations: https://prowlo.com/blog/signs-of-ai-writing

### Source th-patterns

Text Humanize editorial pattern guide: https://text-humanize.com/blog/common-ai-writing-patterns

### Source tropes

Tropes editorial directory: https://tropes.fyi/directory

### Source humanizer

Humanizer editorial reference catalog: https://github.com/conorbronsdon/avoid-ai-writing/blob/main/references/patterns.md

### Source humanize

Humanize rules and research compilation: https://github.com/harshaneel/humanize

### Source wiki

Wikipedia context-specific field guide: https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing

### Source detectgpt

DetectGPT technical method: https://arxiv.org/html/2301.11305v2

### Source binoculars

Binoculars technical method: https://arxiv.org/html/2401.12070v3

### Source linguistic

Linguistic characteristics survey: https://arxiv.org/abs/2510.05136

### Source georgiou

Extracted linguistic features research: https://arxiv.org/abs/2407.03646

### Source gptzero

GPTZero architecture clarification: https://support.gptzero.me/articles/9585228410-how-do-i-interpret-burstiness-or-perplexity
