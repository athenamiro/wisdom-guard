# Wisdom Guard — Hermes Agent Plugin

**Built by Athena** · **Vision by Amir**

An always-on wisdom layer for [Hermes Agent](https://hermes-agent.nousresearch.com/) that evaluates every response through **16 wisdom pillars** across 4 domains. Checks for overconfidence, unfairness, short-sightedness, and dismissiveness.

## Hooks

| Hook | What It Does |
|------|-------------|
| `pre_llm_call` | Injects wisdom framework into every turn |
| `transform_llm_output` | Appends `[Wisdom Guard]` annotations when concerns detected |
| `pre_tool_call` | Blocks destructive commands (`rm -rf /`, fork bombs, remote code piping) |
| `post_llm_call` | Logs all evaluations to `data/logs/` |

## The 16 Pillars

| Cognitive | Ethical | Temporal | Relational |
|-----------|---------|----------|------------|
| Epistemic Humility | Justice & Fairness | Foresight | Perspective-Taking |
| Analytical Depth | Compassion & Empathy | Long-term Orientation | Cultural Wisdom |
| Pattern Recognition | Integrity & Virtue | Prudence | Constructive Discourse |
| Uncertainty Tolerance | Common Good | Learning from Experience | Generativity |

## Configuration

```yaml
skills:
  config:
    wisdom_guard:
      verbosity: medium     # low | medium | high
      cognitive_domain: true
      ethical_domain: true
      temporal_domain: true
      relational_domain: true
```

## Wisdom Library

Add `.md` files to `data/wisdom-library/` — they're auto-loaded and referenced.

## License

Self
