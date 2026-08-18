# Signal Processing (LLM)

## ADDED Requirements

### Requirement: Topic extraction

The processing step SHALL run each raw signal through an LLM (**DeepSeek-V3**) to
extract structured `topics[]` drawn from a fixed vocabulary (gameplay, bugs,
performance, monetization, story, ui, …).

#### Scenario: A signal is classified into topics

- **WHEN** a signal's `text_raw` is processed
- **THEN** the LLM SHALL return `topics[]` drawn from the fixed vocabulary
- **AND** SHALL return it as valid JSON

### Requirement: Sentiment scoring

The processing step SHALL score each signal's sentiment in the range −1…+1.

#### Scenario: Sentiment is bounded

- **WHEN** a signal is scored
- **THEN** `sentiment` SHALL be a real number in [−1, +1]

### Requirement: Text cleaning

The processing step SHALL produce `text_clean` from `text_raw` (strip markup,
emojis/noise, normalize whitespace).

#### Scenario: Cleaned text is stored

- **WHEN** a signal is processed
- **THEN** `text_clean` SHALL be populated alongside `topics` and `sentiment`

### Requirement: Structured output

The LLM extraction SHALL use structured/JSON-mode output so the schema
(`topics[]`, `sentiment`) is deterministic.

#### Scenario: Malformed output is handled, never silently corrupted

- **WHEN** the LLM returns malformed JSON
- **THEN** the signal SHALL be retried
- **AND** if it still fails, SHALL be flagged as failed — never written with
  half-parsed fields

### Requirement: Batching

The processing step SHALL process signals in batches to control cost.

#### Scenario: Signals are batched

- **WHEN** a batch of signals is queued
- **THEN** the LLM SHALL process them in groups (e.g. tens per request) rather than
  one request per signal
