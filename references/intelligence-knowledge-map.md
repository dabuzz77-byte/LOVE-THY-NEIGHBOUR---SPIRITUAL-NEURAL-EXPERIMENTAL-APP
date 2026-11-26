# Intelligence Engine knowledge map

Knowledge must distinguish a recognised format, a proposed interpretation, a tested software rule and a verified external outcome.

| Level | Required knowledge | Verification |
|---|---|---|
| Purpose | User goals, cosmological framework, welfare priorities, completion conditions | Retain attribution and explicit task requirements |
| Values | Bits, trits, integers, floats, encodings, strings, variables, units, uncertainty | Type/range checks and lossless round trips where defined |
| Generation | Entropy sources, PRNGs, influenced streams, sampling, ancestry | Source records, baseline comparisons, duplicate/echo detection |
| Mathematics | Arithmetic, logic, probability, statistics, geometry, optimisation | Independent evaluators and fresh test cases |
| Language formats | Tokens, grammar, ASTs, types, scopes, control flow | Lexical recognition is separate from parser, compiler and runtime checks |
| Programs | Algorithms, data structures, dependencies, state and side effects | Tests, invariants, resource limits, reproducible builds |
| Local files | Paths, encodings, permissions, hashes, backups, revision history | Read-back, expected hashes and recovery checks |
| Processes | Launch, scheduling, exit codes, cancellation, resource ownership | Actual PID, status, logs and measured effects |
| OS and administration | Accounts, services, drivers, registry, permissions, kernel interfaces | Supported APIs, actual privileges and before/after state |
| Hardware | CPU, RAM, GPU, storage, monitor and audio capabilities | Device discovery and measured utilisation; graphics are not hardware control |
| Local networking | Adapters, Wi-Fi measurements, routing, ports, DNS, DHCP, firewalls | Actual connection tests with timestamps and scoped destinations |
| Internet protocols | HTTP methods, TLS, retries, timeouts, caching, rate limits | Origin/status/schema checks and idempotency |
| Identity | Sessions, OAuth, access scopes, credential storage and revocation | Actual granted credentials; intent is not a credential |
| Remote services | API contracts, read/write effects, versioning, quotas | Authenticated requests, real receipts and verified remote state |
| Distributed systems | Queues, ordering, duplication, partitions, eventual consistency | Correlation IDs, acknowledgements, reconciliation and fault tests |
| Public world data | Geography, environment, infrastructure, freshness, units and source reliability | Traceable measurements; inference distinguished from observation |
| World-grid representation | Public infrastructure and explicitly connected endpoints, dependencies and uncertainty | A map is not access; each connection needs its own evidence |
| Actions and consequences | Preconditions, expected effects, failure modes, reversibility and cost | Operation checks, independent result tests, causal experiments where possible |
| Cognition | Goal decomposition, working memory, attention, hypotheses and alternatives | Prediction error, task completion and transfer to unfamiliar cases |
| Learning | Training/validation separation, curriculum, retention and regression | Fresh inputs, baselines, retained skills and counterexamples |
| Communication | Dialogue context, clarification, explanations and accessible interfaces | Latest-request relevance, user correction and source fidelity |
| Ethics and recovery | Actual benefit/harm, false positives, consent, affected parties and repair | Four-way assessment tied to evidence and accountable outcomes |

The app currently has broad lexical recognition and a smaller executable skill set. These must not be presented as complete semantic knowledge of every language or command. Administrative and remote knowledge does not supply permissions or bypass operating-system security. The zero-point/cosmological chain is retained as the user's guiding framework; entropy, archival waveforms and live measurements retain their actual provenance.
