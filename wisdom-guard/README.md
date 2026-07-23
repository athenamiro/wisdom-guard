# Wisdom Guard — Hermes Agent Plugin

An always-on discernment layer for [Hermes Agent](https://hermes-agent.nousresearch.com/) that evaluates every response through **16 wisdom pillars** drawn from **2,500+ years of human wisdom traditions**, psychological research, and decision science.

## What It Is

Wisdom Guard is **not** a content filter or a censorship tool. It is a **wisdom companion** that:

- **Injects** a wisdom evaluation framework into every turn (so Hermes self-evaluates as it generates)
- **Annotates** responses with advisory notes when wisdom concerns are detected
- **Blocks** recklessly dangerous tool calls (fork bombs, `rm -rf /`, remote code piping)
- **Logs** all evaluations for audit trail
- **Provides** a `/wisdom` skill for on-demand deep analysis of decisions

## The 4 Domains and 16 Pillars

### I. Cognitive Domain
| Pillar | What It Checks |
|---|---|
| **Epistemic Humility** | Does the response acknowledge what it doesn't know? Are confidence levels calibrated? |
| **Analytical Depth** | Are root causes examined? Are multiple analytical lenses applied? |
| **Pattern Recognition** | Are relevant historical parallels or structural similarities identified? |
| **Uncertainty Tolerance** | Are shades of gray preserved? Is ambiguity embraced where appropriate? |

### II. Ethical Domain
| Pillar | What It Checks |
|---|---|
| **Justice & Fairness** | Is the advice fair to all stakeholders? Are rights and duties balanced? |
| **Compassion & Empathy** | Does the response acknowledge human impact? Is compassion balanced with objectivity? |
| **Integrity & Virtue** | Would the agent stand by this advice publicly? Are principles upheld? |
| **Common Good** | Are broader societal and environmental impacts addressed? |

### III. Temporal Domain
| Pillar | What It Checks |
|---|---|
| **Foresight** | Are 2nd and 3rd-order consequences explored? |
| **Long-term Orientation** | Is sustainability considered? Are short-term needs balanced with long-term health? |
| **Prudence** | Are risks assessed? Are there fallback plans? |
| **Learning from Experience** | Are relevant historical lessons or known pitfalls mentioned? |

### IV. Relational Domain
| Pillar | What It Checks |
|---|---|
| **Perspective-Taking** | Are multiple stakeholder perspectives considered? |
| **Cultural Wisdom** | Is the response culturally sensitive? Are traditions appropriately referenced? |
| **Constructive Discourse** | Does the response engage with counterarguments? |
| **Generativity** | Does the response empower and teach, or create dependency? |

## Wisdom Sources

The guard draws from:

- **Greek Philosophy**: Aristotle's Phronesis/Sophia, Plato's Dialectic, Stoic Virtues
- **Islamic Tradition**: Hikmah, the Five Legal Maxims, characteristics of the Hakim
- **Buddhist Wisdom**: Prajna, the Middle Way, Karuna
- **Taoist Wisdom**: Wu Wei, Tao Te Ching, Zhuangzi
- **Judaic Wisdom**: Hokhmah, Talmudic dialectic, Musar
- **Confucian Wisdom**: The Five Constants, Doctrine of the Mean
- **Hindu Wisdom**: Bhagavad Gita, Upanishads, the gunas
- **Indigenous Wisdom**: Ubuntu, Seven Generations, Deep Time
- **Psychological Research**: Jeste et al. Delphi study, Baltes' Berlin Wisdom Paradigm, Sternberg's Balance Theory
- **Decision Science**: Second-order thinking, Inversion, Chesterton's Fence, Via Negativa
- **AI Ethics**: Alignment principles, Precautionary Principle, Value Alignment

## Installation

### 1. Copy the plugin to your Hermes plugins directory

```bash
# Clone or copy wisdom-guard to your Hermes plugins directory
cp -r wisdom-guard/ ~/.hermes/plugins/wisdom-guard/
```

### 2. Enable the plugin

```bash
hermes plugins enable wisdom-guard
```

Or add to `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - wisdom-guard
```

### 3. Restart Hermes

```bash
hermes
```

The Wisdom Guard is now active on every turn.

## How It Works

### Always-On Hooks

| Hook | What It Does |
|---|---|
| `pre_llm_call` | Injects the wisdom evaluation framework into every turn's context |
| `transform_llm_output` | Evaluates the final response and appends `[Wisdom Guard]` annotations |
| `pre_tool_call` | Blocks dangerously reckless terminal commands |
| `post_llm_call` | Logs all wisdom evaluations to `data/logs/` for audit |

### Annotation Format

When a concern is detected, annotations are appended to the response:

```
[Wisdom Guard]
  ! [Foresight] High-stakes decisions deserve risk assessment. Consider what could go wrong.
  ~ [Epistemic Humility] Consider calibrating confidence levels on some claims.
  · [Perspective-Taking] Consider how different stakeholders would view this situation.
[/Wisdom Guard]
```

Severity indicators: `!` = high, `~` = medium, `·` = low

### On-Demand Skill

For deep analysis, invoke the `/wisdom` skill:

```bash
/wisdom Should I migrate our entire database to a new provider?
```

This triggers a structured 6-step wisdom analysis covering cardinal virtues, consequence mapping, ethical lens analysis, and wisdom traditions insights.

## Extending the Wisdom Library

Add your own wisdom sources by placing `.md` files in:

```
~/.hermes/plugins/wisdom-guard/data/wisdom-library/
```

Any `.md` file placed here is automatically loaded and referenced by the guard.

## Configuration

Add to `~/.hermes/config.yaml`:

```yaml
skills:
  config:
    wisdom_guard:
      sensitivity: medium  # low | medium | high
      cognitive_domain: true
      ethical_domain: true
      temporal_domain: true
      relational_domain: true
```

## File Structure

```
wisdom-guard/
├── plugin.yaml                    # Plugin manifest
├── __init__.py                    # Core guard logic (4 hooks + 16 pillars)
├── config.example.yaml            # Example configuration
├── data/
│   └── wisdom-library/            # Extensible knowledge base
│       ├── core-principles.md     # Foundational wisdom definitions
│       ├── ethical-frameworks.md  # Decision-making frameworks
│       ├── decision-models.md     # Mental models for wise decisions
│       └── wisdom-traditions.md   # Wisdom across world traditions
├── skills/
│   └── wisdom/
│       └── SKILL.md               # /wisdom skill for deep analysis
└── README.md                      # This file
```

## License

MIT
