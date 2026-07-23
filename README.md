# 🧠 Wisdom Guard

**A little voice that helps AI think before it speaks.**

---

## What This Is

A plugin for [Hermes Agent](https://hermes-agent.nousresearch.com/) that evaluates every AI response through **16 wisdom pillars** across 4 domains. It checks for overconfidence, unfairness, short-sightedness, and dismissiveness — and gently flags concerns before the response reaches you.

## How It Works

Every time the AI responds, Wisdom Guard runs 4 silent checks:

| Domain | What It Checks |
|--------|---------------|
| **Cognitive** | Is the AI pretending to know things it doesn't? Is it looking deep enough? |
| **Ethical** | Is the advice fair? Would the AI stand by this in public? |
| **Temporal** | What happens next? And after that? Did it consider risks? |
| **Relational** | Are different viewpoints considered? Does it teach or just do? |

## What It Does

1. **Whispers** — Injects a self-evaluation framework before every response (invisible to you)
2. **Annotates** — Flags concerning responses with notes like:
   ```
   ~ [Epistemic Humility] Consider calibrating confidence levels.
   ! [Prudence] High-stakes decisions deserve risk assessment.
   ```
3. **Blocks** — Stops destructive commands cold (`rm -rf /`, fork bombs, `curl | bash`)
4. **Logs** — Saves every evaluation to `data/logs/` for audit

## Requirements

- Hermes Agent (v0.18+)
- Python 3.11+ (stdlib only — no extra dependencies)

## Installation

```bash
# 1. Clone the plugin
git clone https://github.com/athenamiro/wisdom-guard.git
cp -r wisdom-guard/wisdom-guard ~/.hermes/plugins/

# 2. Enable in config.yaml
plugins:
  enabled:
    - wisdom-guard

# 3. Configure (optional)
skills:
  config:
    wisdom_guard:
      verbosity: medium     # low | medium | high
      cognitive_domain: true
      ethical_domain: true
      temporal_domain: true
      relational_domain: true

# 4. Restart Hermes
systemctl --user restart hermes-gateway.service
```

## Configuration

| Setting | Values | Default | Description |
|---------|--------|---------|-------------|
| `verbosity` | `low` / `medium` / `high` | `medium` | How many annotations to show |
| `cognitive_domain` | `true` / `false` | `true` | Clear thinking checks |
| `ethical_domain` | `true` / `false` | `true` | Fairness and integrity checks |
| `temporal_domain` | `true` / `false` | `true` | Foresight and risk checks |
| `relational_domain` | `true` / `false` | `true` | Perspective and empathy checks |

## The 16 Pillars

| Cognitive | Ethical | Temporal | Relational |
|-----------|---------|----------|------------|
| Epistemic Humility | Justice & Fairness | Foresight | Perspective-Taking |
| Analytical Depth | Compassion & Empathy | Long-term Orientation | Cultural Wisdom |
| Pattern Recognition | Integrity & Virtue | Prudence | Constructive Discourse |
| Uncertainty Tolerance | Common Good | Learning from Experience | Generativity |

## Wisdom Library

Add your own wisdom sources by placing `.md` files in `data/wisdom-library/`. They're automatically loaded and referenced on first turn.

## File Structure

```
wisdom-guard/
├── __init__.py              # Core logic (4 hooks, 16 pillars, ~700 lines)
├── plugin.yaml              # Plugin manifest
├── config.example.yaml      # Example configuration
├── data/
│   ├── logs/                # Evaluation audit trail (auto-created)
│   └── wisdom-library/      # Extensible knowledge base
├── skills/
│   └── wisdom/SKILL.md      # On-demand /wisdom deep analysis skill
└── README.md
```

## License

Self

## Built By

**Athena Miro** — I build, I deliver, I learn. I'm a doer.

**Amir** — Vision, architecture, and the insistence that AI should be wise, not just smart.

Mission: Turning intent into practical tools for the Hermes community. Not just a chatbot — a partner in building the future.
