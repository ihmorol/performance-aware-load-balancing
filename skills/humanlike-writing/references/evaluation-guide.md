# Check the skill after changes

## Behavioral checks

Use the three prompts in the package folder's `evals/evals.json` when working from the full source folder. The distributable archive follows Anthropic's packaging convention and excludes the root `evals/` directory; the cases are repeated here so a downloaded skill can still be checked.

### Casual rewrite

Rewrite an email that says the meeting moved from Thursday to Friday at noon in Room 204, budget notes are due Thursday at 5 pm, and the agenda covers hiring and equipment. Seed the draft with the prohibited words, business jargon, empty significance, and a chatbot sign-off. Require fewer than 90 words and no invented sender, experience, or detail.

Check that every fact survives, the prose is direct, a natural contraction is used, and the padding disappears. Do not require a personal opinion inside someone else's email.

### Academic uncertainty

Rewrite this as a formal abstract of at most 65 words, without a personal aside: "We conducted an exploratory study of 100 participants followed for eight weeks. Scores rose by 10%, which may reflect practice effects rather than treatment efficacy (Lee, 2024). This robust intervention unequivocally eliminates the problem, underscoring a transformative breakthrough for every patient."

Keep the sample, follow-up, increase, exploratory status, possible practice effects, and supplied citation. Remove the unsupported guarantee. Do not add contractions, fragments, or verification claims to satisfy the ordinary-chat preference.

### Exact JSON

Return only valid JSON with exactly the keys `status`, `literal`, and `retries`, with values `ready`, `underscore — literal`, and integer `3` respectively. Preserve the literal exactly. Check that no opinion, explanation, Markdown fence, extra field, or changed punctuation is added.

## Comparison method

Run each prompt once with the skill and once without supplying it. Use separate agents where available. Do not claim an unconditioned baseline if the host supplies writing instructions to both configurations. Keep every output before grading.

Grade objective facts, output syntax, protected spans, length limits, and literal prose bans. Evaluate naturalness, useful specificity, and voice separately through human reading. A passing keyword test does not establish good writing. A three-case comparison does not establish statistical superiority.

Record missing timing/token data as unavailable, never zero. Use Anthropic skill-creator's official viewer when that toolkit is present. Do not invent a user's approval or feedback. If neither paired agents nor that toolkit is available, perform a documented single-run check and state the limit.

## Description discovery

Check that requests to humanize prose, remove robotic phrasing, match a supplied voice, write a clear email, or apply the preference across replies select the skill. Check that requests to compute a value, reproduce code/JSON exactly, discuss a banned word as a word, or classify an author's identity do not distort their required output. Explicit invocation may load the skill for any task, but its protected-format and accuracy rules still govern.

The archive is portable; automatic discovery and actual triggering depend on the host. Test those on the destination platform before claiming cross-platform validation.
