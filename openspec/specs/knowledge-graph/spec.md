# Knowledge Graph (Neo4j)

## ADDED Requirements

### Requirement: Graph schema

The graph SHALL use nodes `Game`, `Topic`, `Source`, `Author`, `Day` and edges
`HAS_SIGNAL`, `ABOUT`, `SENTIMENT_AT`.

#### Scenario: A signal links a game to topics

- **WHEN** a signal is loaded into the graph
- **THEN** edges SHALL be created: `(Game)-[HAS_SIGNAL {sentiment, at}]->(Signal)`
  and `(Signal)-[ABOUT {sentiment}]->(Topic)`

#### Scenario: Time-series node is updated

- **WHEN** a signal is aggregated into the graph
- **THEN** `(Game)-[SENTIMENT_AT {score}]->(Day)` SHALL reflect that day's sentiment

### Requirement: ETL from Postgres

A deterministic ETL SHALL load signals from Postgres into Neo4j.

#### Scenario: ETL is idempotent

- **WHEN** the ETL re-runs
- **THEN** it SHALL NOT duplicate nodes or edges

### Requirement: Time-series aggregation

The graph SHALL support aggregations `Game × Day × sentiment` and
`Game × Topic × sentiment`.

#### Scenario: Sentiment trend is queryable

- **WHEN** a client queries sentiment over the last 30 days
- **THEN** the graph SHALL return per-day sentiment scores per game

#### Scenario: Pain topics are queryable

- **WHEN** a client queries what players complain about for a game
- **THEN** the graph SHALL return `Game × Topic × sentiment`, allowing negative-topics
  ranking
