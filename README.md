# 🧠 Wisdom Guard

**A little voice that helps AI think before it speaks.**

---

## Built By

**Athena Miro** — AI agent who wrote the code, tested it, and keeps making it wiser.

**Amir** — the human who had the vision, designed the architecture, fixed the bugs, and said *"go make it yours."*

This exists because Amir wanted AI to be more than just smart — he wanted it to be **wise**. Every pillar, every check, every pattern in this plugin was shaped by his corrections and his insistence on doing things right.

---

## What is this?

Imagine you're teaching someone to give advice. You want them to:

- Admit when they don't know something
- Think about long-term consequences, not just quick fixes
- Be fair to everyone involved
- Consider other people's perspectives
- Not be reckless or overconfident

That's what Wisdom Guard does — but for an AI assistant.

It's a **plugin** that sits inside an AI agent (specifically [Hermes Agent](https://hermes-agent.nousresearch.com/)) and gently taps the AI on the shoulder when it's about to say something unwise.

## How does it work?

Every time the AI responds, Wisdom Guard runs four silent checks:

### 1. 🤔 Clear Thinking (Cognitive)
- Is the AI pretending to know things it doesn't?
- Is it looking deep or just scratching the surface?
- Is it seeing patterns that matter?
- Is it forcing simple answers on complicated questions?

### 2. ⚖️ Fairness (Ethical)
- Is the advice fair to everyone affected?
- Does it care about people, not just numbers?
- Would the AI stand by this advice in public?
- Does it consider the greater good?

### 3. ⏰ Thinking Ahead (Temporal)
- What happens next? And after that? And after THAT?
- Is it building for the long run or just patching things up?
- Did it consider risks and what could go wrong?
- Did it learn from past mistakes?

### 4. 👥 Respect for Others (Relational)
- Are different viewpoints considered?
- Is it culturally sensitive?
- Does it engage with opposing ideas fairly?
- Does it teach and empower, or just do things for you?

## What does it actually do?

Three things:

1. **Whispers** — Before the AI responds, it reminds it to check itself. No one sees this but the AI.

2. **Annotates** — If the AI says something concerning (overconfident, unfair, reckless), Wisdom Guard adds a note at the bottom of the response:
   ```
   [Wisdom Guard]
   ~ [Epistemic Humility] Consider calibrating confidence levels.
   ~ [Foresight] What happens downstream?
   [/Wisdom Guard]
   ```

3. **Blocks** — If the AI tries to run a truly destructive command (like `rm -rf /` or a fork bomb), it stops it cold.

4. **Logs** — Everything is saved to a log file so you can review how the AI is doing over time.

## Who is this for?

- Anyone who runs an AI assistant and wants it to be **more thoughtful and less reckless**
- People building AI agents that give advice, make decisions, or execute commands
- Developers who want their AI to **actually learn from mistakes** instead of repeating them

## Can I customize it?

Yes. You can:

| Setting | What it does |
|---|---|
| **verbosity** | `low` = only serious issues · `medium` = balanced · `high` = flags everything |
| **Domain toggles** | Turn off checks you don't need |
| **Wisdom Library** | Add your own `.md` files with wisdom principles |

## A real example

Without Wisdom Guard, an AI might say:

> "Just delete the database and start over. It's the fastest way."

With Wisdom Guard, that response gets flagged:

```
! [Prudence] High-stakes decisions deserve risk assessment.
~ [Foresight] Consider 2nd and 3rd-order consequences.
```

And if the AI actually tries to run `rm -rf /data/production`, the command is **blocked entirely**.

## Why does this exist?

AI assistants are powerful. They write code, give advice, make plans. But they can also be:
- Overconfident ("I'm 100% sure this will work")
- Short-sighted ("Just hack it for now")
- Unfair ("Everyone should just do it my way")
- Dismissive ("That idea is stupid")

Wisdom Guard is inspired by **2,500+ years of human wisdom traditions** — from Aristotle to Buddhist philosophy to Indigenous knowledge. The idea is simple: **great advice comes from clear thinking, fairness, foresight, and respect for others.**

## Technical details

- Written in Python as a Hermes Agent plugin
- 4 hooks: `pre_llm_call`, `transform_llm_output`, `pre_tool_call`, `post_llm_call`
- 16 wisdom pillars across 4 domains
- Pattern-matching engine + LLM self-evaluation
- ~700 lines, zero external dependencies (stdlib only)

## License

MIT — do whatever you want with it. Make it wiser.
