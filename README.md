# Holodeck

*Wesley practices in the sim.*

The holodeck is a lightweight Python-based simulation training environment where Wesley (Granite 3.1 2B via Ollama) practices real maritime tasks in a safe sandbox. No Roblox Studio required.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    THE SIMULATOR                          │
│                                                          │
│  ┌─────────┐   ┌──────────────┐   ┌─────────────┐       │
│  │ Scenario │──▶│ Wesley (LLM) │──▶│  Evaluator  │       │
│  │ Generator│   │ via Ollama   │   │  (scoring)  │       │
│  └─────────┘   └──────────────┘   └──────┬──────┘       │
│                                             │             │
│                          ┌──────────────────┼─────────┐  │
│                          │                  │         │  │
│                          ▼                  ▼         ▼  │
│                    ┌──────────┐  ┌──────────────┐ ┌────┐ │
│                    │ .nail    │  │ Failure Log  │ │Repo│ │
│                    │ reflex   │  │ (for loop)   │ │rt  │ │
│                    └──────────┘  └──────────────┘ └────┘ │
└──────────────────────────────────────────────────────────┘
```

## Task Types

| Task | Description | Skills Practiced |
|------|-------------|-----------------|
| **Engine Diagnosis** | Given symptoms, identify the engine problem | Troubleshooting, systems knowledge |
| **Route Planning** | Given current/wind/obstacles, plot a course | Navigation, spatial reasoning |
| **Fish Identification** | Given characteristics, identify the species | Marine biology, classification |
| **Material Selection** | Given build requirements, choose materials | Engineering, tradeoff analysis |
| **Emergency Response** | Given situation, choose correct protocol | Safety, decision-making under pressure |
| **Radio Communication** | Given scenario, describe VHF procedure | Communications, distress protocols, DSC |

Each task type has:
- **Scenario generator** — produces varied instances with randomized parameters
- **Evaluator** — scores responses on 4 dimensions (accuracy, specificity, reasoning, completeness)
- **Difficulty curve** — easy → medium → hard, with escalating complexity

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run 10 tasks across all 5 types
python -m holodeck.simulator --tasks 10

# Run a specific task type
python -m holodeck.simulator --type engine_diagnosis --tasks 5

# Run with a specific difficulty
python -m holodeck.simulator --difficulty hard --tasks 5

# Dry run (no Ollama, for testing)
python -m holodeck.simulator --dry-run --tasks 10
```

## How It Works

1. **Scenario Generation** — The holodeck creates a randomized scenario for the task type
2. **Wesley Attempt** — The scenario is sent to Granite via `ollama run`
3. **Evaluation** — The response is scored on 4 dimensions:
   - **Accuracy** — Does the answer match the expected solution?
   - **Specificity** — Concrete details, numbers, technical terms
   - **Reasoning** — Logical chain from symptoms to conclusion
   - **Completeness** — All parts of the problem addressed
4. **Compilation** — If successful (composite score ≥ threshold), compile into a `.nail` reflex
5. **Logging** — Both successes and failures are logged for the distillation loop

## Integration with the Exocortex

The holodeck feeds back into the distillation loop:

- **Successful attempts** → `.nail` reflexes (compiled wisdom for future use)
- **Failed attempts** → logged to `failures.jsonl` (the distillation loop targets these gaps)
- **Session reports** → `reports/` (human-readable summary of training)
- **Weakness map** → `weakness_map.json` (which task types Wesley handles well vs poorly)

## Ollama Configuration

The simulator expects Ollama running locally with `granite3.1-dense:2b`:

```bash
# Verify Ollama is running
ollama list

# The model should appear as:
# granite3.1-dense:2b
```

Environment variables:
- `OLLAMA_URL` — Ollama API endpoint (default: `http://localhost:11434/api/chat`)
- `OLLAMA_MODEL` — Model name (default: `granite3.1-dense:2b`)
- `OLLAMA_BIN` — Path to ollama binary for CLI fallback (default: `/home/eileen/.local/bin/ollama`)

## Testing

```bash
pytest tests/ -v
```

## The Point

The holodeck teaches what nobody knows — knowledge that comes from interaction with a world that pushes back. Distillation teaches what the teacher knows. The holodeck teaches what the teacher *doesn't* know.

The bump is the lesson. Wesley docks 50 times while the captain sleeps.

## License

MIT — see [LICENSE](LICENSE).
