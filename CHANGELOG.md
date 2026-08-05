# Changelog

All notable changes to the Holodeck training simulator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Radio Communication task type** — new 6th task covering VHF protocol, distress calls
  (Mayday, Pan-Pan, Sécurité), Digital Selective Calling (DSC), and ITU phonetic alphabet.
  Four scenario categories across three difficulty levels.
- **Evaluator edge-case test suite** (35 new tests) — covers empty responses, unicode,
  very long inputs, boundary thresholds, case insensitivity, and helper functions.
- **Bug fix in Evaluator** — `pass_threshold=0.0` was treated as falsy and silently replaced
  with the default (0.45). Now correctly handled via `is None` check.

### Changed
- Task registry now includes 6 task types (was 5).
- Simulator tests updated to cover all 6 types.
- README task table to be updated.

## [0.1.0] - Initial Release

- 5 task types: Engine Diagnosis, Route Planning, Fish Identification, Material Selection, Emergency Response
- 4-dimensional evaluator (accuracy, specificity, reasoning, completeness)
- .nail reflex compilation for successful attempts
- Weakness map tracking for targeted distillation
- Session reporting with per-type and per-difficulty breakdowns
- Dry-run mode for testing without Ollama
- 69 tests, all passing
