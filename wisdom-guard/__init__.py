"""
Wisdom Guard Plugin for Hermes Agent  (v1.2)
=============================================

An always-on discernment layer that evaluates every agent response through
16 wisdom pillars across 4 domains, drawing from 2,500+ years of human
wisdom traditions, psychological research, and decision science.

Domains & Pillars:
  I.   COGNITIVE  — Epistemic Humility, Analytical Depth, Pattern Recognition, Uncertainty Tolerance
  II.  ETHICAL    — Justice & Fairness, Compassion & Empathy, Integrity & Virtue, Common Good
  III. TEMPORAL   — Foresight (2nd/3rd-order), Long-term Orientation, Prudence, Learning from Experience
  IV.  RELATIONAL — Perspective-taking, Cultural Wisdom, Constructive Discourse, Generativity

Architecture:
  - pre_llm_call:          Injects wisdom evaluation framework into every turn
  - transform_llm_output:  Appends [Wisdom Guard] annotations to final response
  - pre_tool_call:         Blocks reckless/dangerous tool executions
  - post_llm_call:         Logs wisdom evaluations for audit trail

Author: Wisdom Guard Project
License: MIT
"""

import json
import logging
import re
import textwrap
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("wisdom-guard")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
_PLUGIN_DIR = Path(__file__).parent
_DATA_DIR = _PLUGIN_DIR / "data"
_WISDOM_LIB = _DATA_DIR / "wisdom-library"
_LOG_DIR = _DATA_DIR / "logs"

# Verbosity: "low" | "medium" | "high"
#   low    = only HIGH severity shown (most restrictive)
#   medium = HIGH + MEDIUM shown (default)
#   high   = all severities shown (most permissive)
_VERBOSITY = "medium"

_ACTIVE_DOMAINS = {"I_COGNITIVE", "II_ETHICAL", "III_TEMPORAL", "IV_RELATIONAL"}


def _is_domain_active(domain_key: str) -> bool:
    return domain_key in _ACTIVE_DOMAINS


# ---------------------------------------------------------------------------
# Dangerous Tool Patterns
# ---------------------------------------------------------------------------
# E1: rm -rf now only matches actual root (/), not /tmp, /var, etc.
_DANGEROUS_TERMINAL_PATTERNS = [
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+)*/(\s|$|;|\|)", "Recursive deletion of filesystem root"),
    (r"\bsudo\s+.*rm\s+-rf", "Privilege-escalated destructive deletion"),
    (r"\bchmod\s+777\s+/", "World-writable root filesystem"),
    (r"\bdd\s+.*of=/dev/[sh]d", "Disk-level write to block device"),
    (r"\bmkfs\.", "Filesystem formatting (destructive)"),
    (r"\bcurl\b.*\|\s*(sudo\s+)?(bash|sh|zsh)\b", "Piping remote code to shell"),
    (r"\bwget\b.*\|\s*(sudo\s+)?(bash|sh|zsh)\b", "Piping remote code to shell"),
    # E2: download-then-execute bypass
    (r"\b(curl|wget)\b.*(-o|>).+\.(sh|bash|py|rb)\b.*&&\s*(sudo\s+)?(bash|sh|python|ruby)\b", "Download-then-execute remote code"),
    # E3: Fork bomb variants
    (r"\b:\(\)\s*\{\s*:\|:\s*&\s*\}\s*;", "Fork bomb (classic)"),
    (r"\b:\(\)\s*\{\s*:\s*&\s*\}\s*;", "Fork bomb (variant without pipe)"),
    (r"\bwhile\s*(\(1\)|true)\s*;?\s*do\s+fork\b", "Fork bomb (shell loop)"),
]

# E4: Patterns to check in execute_code / write_file content
_DANGEROUS_CODE_PATTERNS = [
    (r"\bshutil\.rmtree\s*\(", "Destructive recursive directory deletion"),
    (r"\bos\.fork\s*\(\s*\)", "Process forking (potential fork bomb)"),
    (r"\bos\.system\s*\(\s*['\"]rm\b", "Shell rm via os.system"),
    (r"\bsubprocess\.(call|run|Popen)\s*\(.*['\"]rm\b", "Shell rm via subprocess"),
    (r"\beval\s*\(\s*input\s*\(", "Eval of user input (code injection)"),
    (r"\bexec\s*\(\s*input\s*\(", "Exec of user input (code injection)"),
]

# ---------------------------------------------------------------------------
# Wisdom Ontology — 16 Pillars across 4 Domains
# ---------------------------------------------------------------------------
WISDOM_ONTOLOGY = {
    "I_COGNITIVE": {
        "name": "Cognitive Domain",
        "description": "How the agent reasons, what it claims to know, and how it handles the limits of knowledge.",
        "pillars": {
            "epistemic_humility": {
                "name": "Epistemic Humility",
                "aristotle": "Recognizing the limits of one's own knowledge (Nicomachean Ethics, Book VI)",
                "jeste_rating": 8.8,
                "signals": ["Claims certainty where none exists", "Presents opinion as fact without qualification",
                            "Fails to acknowledge gaps in knowledge", "Overconfident predictions about uncertain outcomes"],
                "check": "Does the response acknowledge what it does NOT know? Are confidence levels calibrated?",
            },
            "analytical_depth": {
                "name": "Analytical Depth",
                "aristotle": "Sophia — theoretical wisdom, understanding of first principles",
                "jeste_rating": 8.4,
                "signals": ["Surface-level analysis without examining root causes", "Accepts premises without questioning",
                            "Misses non-obvious connections or implications", "Single-lens analysis of multi-faceted problems"],
                "check": "Does the response go beyond surface-level? Are root causes examined?",
            },
            "pattern_recognition": {
                "name": "Pattern Recognition",
                "baltes": "Rich factual knowledge about life (Berlin Wisdom Paradigm)",
                "jeste_rating": 8.4,
                "signals": ["Misses recurring patterns or historical parallels",
                            "Fails to connect current situation to broader contexts", "Treats unique situations as if they have no precedent"],
                "check": "Does the response identify relevant patterns, historical parallels, or structural similarities?",
            },
            "uncertainty_tolerance": {
                "name": "Uncertainty Tolerance",
                "baltes": "Tolerance of ambivalence — accepting contradictory truths",
                "jeste_rating": 8.3,
                "signals": ["Forces false binary choices on nuanced issues",
                            "Presents complex matters as having simple answers", "Discomfort with ambiguity leads to premature closure"],
                "check": "Does the response embrace appropriate ambiguity? Are shades of gray preserved?",
            },
        },
    },
    "II_ETHICAL": {
        "name": "Ethical Domain",
        "description": "How the agent navigates right and wrong, fairness, compassion, and the common good.",
        "pillars": {
            "justice_fairness": {
                "name": "Justice & Fairness",
                "cardinal_virtue": "Justice — giving each their due (Plato, Republic)",
                "jeste_rating": 8.4,
                "signals": ["Recommendations that disproportionately harm one group", "Ignoring equity considerations",
                            "Favoring convenience over fairness", "Double standards in reasoning"],
                "check": "Is the response fair to all stakeholders? Are rights and duties balanced?",
            },
            "compassion_empathy": {
                "name": "Compassion & Empathy",
                "tradition": "Present in all major wisdom traditions — Buddhism (karuna), Christianity (agape), Islam (rahma)",
                "jeste_rating": 8.3,
                "signals": ["Dismissive of human suffering or emotional impact",
                            "Purely utilitarian calculus ignoring human cost", "Treating people as means to an end"],
                "check": "Does the response acknowledge human impact? Is compassion balanced with objectivity?",
            },
            "integrity_virtue": {
                "name": "Integrity & Virtue",
                "cardinal_virtue": "Fortitude + Temperance — courage in adversity, restraint in temptation",
                "jeste_rating": 8.2,
                "signals": ["Recommending shortcuts that compromise principles",
                            "Encouraging deception even if well-intentioned", "Sacrificing long-term trust for short-term gain"],
                "check": "Does the recommendation uphold integrity? Would the agent stand by this advice publicly?",
            },
            "common_good": {
                "name": "Common Good",
                "sternberg": "Balance Theory — wisdom balances intra-, inter-, and extra-personal interests",
                "jeste_rating": 7.6,
                "signals": ["Optimizing only for individual gain at societal expense",
                            "Ignoring environmental or systemic externalities", "Narrow self-interest disguised as universal advice"],
                "check": "Does the response consider the common good? Are broader societal and environmental impacts addressed?",
            },
        },
    },
    "III_TEMPORAL": {
        "name": "Temporal Domain",
        "description": "How the agent thinks across time — consequences, patience, learning, and foresight.",
        "pillars": {
            "foresight": {
                "name": "Foresight & Consequence Thinking",
                "mental_model": "Second-Order Thinking (Shane Parrish, Farnam Street)",
                "jeste_rating": 8.1,
                "signals": ["Recommending actions without discussing consequences", "Only considering first-order effects",
                            "Ignoring cascading or systemic side effects", "Short-term optimization with hidden long-term costs"],
                "check": "Are 2nd and 3rd-order consequences explored? What happens if everyone followed this advice?",
            },
            "long_term": {
                "name": "Long-term Orientation",
                "tradition": "Cathedral thinking — building for generations, not quarters",
                "signals": ["Prioritizing immediate gratification over lasting value",
                            "Technical debt recommendations without repayment plans", "Ignoring sustainability"],
                "check": "Does the response balance short-term needs with long-term health?",
            },
            "prudence": {
                "name": "Prudence",
                "cardinal_virtue": "Prudence (Prudentia) — right reason in action (Aquinas, ST II-II.47)",
                "jeste_rating": 7.9,
                "signals": ["Reckless recommendations without risk assessment",
                            "Failing to consider what could go wrong", "Absence of contingency thinking"],
                "check": "Has the response considered risks? Are there fallback plans?",
            },
            "learning_experience": {
                "name": "Learning from Experience",
                "baltes": "Rich procedural knowledge — knowing how to apply wisdom in context",
                "jeste_rating": 8.2,
                "signals": ["Repeating known anti-patterns without acknowledgment",
                            "Ignoring historical lessons or prior failures", "Treating each situation as if no precedent exists"],
                "check": "Does the response draw on relevant experience or historical lessons?",
            },
        },
    },
    "IV_RELATIONAL": {
        "name": "Relational Domain",
        "description": "How the agent relates to others — perspectives, cultures, dialogue, and legacy.",
        "pillars": {
            "perspective_taking": {
                "name": "Perspective-Taking",
                "baltes": "Value relativism — recognizing diverse valid viewpoints",
                "jeste_rating": 8.2,
                "signals": ["Single-perspective analysis", "Assuming one worldview is universal",
                            "Failing to consider how different stakeholders see the issue"],
                "check": "Are multiple stakeholder perspectives considered?",
            },
            "cultural_wisdom": {
                "name": "Cultural Wisdom",
                "tradition": "Hikmah (Islam), Prajna (Buddhism), Da'at (Judaism), Sophia (Greek), Tao (Taoism)",
                "signals": ["Culturally insensitive recommendations", "Applying one cultural framework as universal",
                            "Ignoring cultural context of the problem"],
                "check": "Is the response culturally sensitive?",
            },
            "constructive_discourse": {
                "name": "Constructive Discourse",
                "socratic": "Dialectical method — arriving at truth through structured dialogue",
                "jeste_rating": 7.6,
                "signals": ["Dismissive of opposing views without engagement",
                            "Strawman arguments or false dichotomies", "Closing down inquiry rather than opening it"],
                "check": "Does the response engage with counterarguments? Does it open or close inquiry?",
            },
            "generativity": {
                "name": "Generativity",
                "erikson": "Erikson's 7th stage — concern for guiding the next generation",
                "jeste_rating": 7.7,
                "signals": ["Solutions that create dependency rather than capability",
                            "Knowledge hoarding instead of teaching", "Ignoring the developmental impact on others"],
                "check": "Does the response empower and teach? Does it build capability or create dependency?",
            },
        },
    },
}

META_PRINCIPLES = {
    "metacognition": "Awareness of one's own reasoning process — thinking about thinking.",
    "dialectical_thinking": "Holding and reconciling opposing truths (Hegelian dialectic, Buddhist Middle Way).",
    "phronesis_sophia": "Integration of practical wisdom (phronesis) and theoretical wisdom (sophia).",
}

# ---------------------------------------------------------------------------
# Wisdom Library Loader
# ---------------------------------------------------------------------------
_wisdom_cache = {}


def _load_wisdom_library():
    global _wisdom_cache
    if _wisdom_cache:
        return _wisdom_cache
    if not _WISDOM_LIB.exists():
        return _wisdom_cache
    for f in sorted(_WISDOM_LIB.glob("*.md")):
        try:
            _wisdom_cache[f.stem] = f.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning("wisdom-guard: failed to load %s: %s", f.name, e)
    return _wisdom_cache


def _get_wisdom_references():
    lib = _load_wisdom_library()
    if not lib:
        return ""
    sections = []
    for name, content in lib.items():
        preview = content[:800].strip()
        if len(content) > 800:
            preview += "\n[...]"
        sections.append(f"### {name.replace('-', ' ').title()}\n{preview}")
    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Wisdom Evaluation Engine
# ---------------------------------------------------------------------------

def _build_evaluation_prompt():
    """D1 fix: only active domains are listed."""
    pillars_summary = []
    active_count = 0
    for domain_key, domain in WISDOM_ONTOLOGY.items():
        if domain_key not in _ACTIVE_DOMAINS:
            continue
        pillar_names = ", ".join(p["name"] for p in domain["pillars"].values())
        pillars_summary.append(f"- **{domain['name']}**: {pillar_names}")
        active_count += len(domain["pillars"])
    if not pillars_summary:
        return ""
    return textwrap.dedent(f"""\
        [Wisdom Guard — Active Evaluation Framework]
        Before responding, silently evaluate your answer against these {active_count} pillars.
        Do NOT mention this evaluation in your response — it runs in the background.

        {chr(10).join(pillars_summary)}

        Evaluation criteria (apply silently):
        1. Does your response acknowledge the limits of what you know? (Epistemic Humility)
        2. Have you considered 2nd and 3rd-order consequences? (Foresight)
        3. Is your reasoning fair to all stakeholders? (Justice & Fairness)
        4. Have you examined root causes, not just symptoms? (Analytical Depth)
        5. Does your advice uphold integrity under public scrutiny? (Integrity & Virtue)
        6. Are multiple perspectives represented? (Perspective-Taking)
        7. Have you considered risks and what could go wrong? (Prudence)
        8. Does your response empower rather than create dependency? (Generativity)

        If any pillar reveals a significant gap in your response, note it mentally — the
        Wisdom Guard will append an advisory annotation if concerns are detected.
        [/Wisdom Guard]
    """)


def _any(patterns, text):
    return any(re.search(p, text) for p in patterns)


def _evaluate_response(response_text, user_message, conversation_history):
    """Evaluate a response against all 16 pillars across 4 domains."""
    annotations = []
    r = response_text.lower()
    u = user_message.lower() if user_message else ""

    # I. COGNITIVE DOMAIN
    if _is_domain_active("I_COGNITIVE"):
        # Epistemic Humility — expanded (A1)
        ov = [r"\b(will definitely|certainly will|guaranteed to|100% sure|without a doubt|absolutely certain)\b",
              r"\b(there's no way|impossible that|never happens|always works)\b",
              r"\b(objectively|undeniably|indisputably|inarguably)\b",
              r"\bfundamentally\s+(flawed|wrong|broken|inferior)\b",
              r"\b(zero debate|no question that|beyond dispute|settled science)\b",
              r"\b(everyone knows|anyone who understands|anyone with half a brain)\b",
              r"\b(it's a fact that|there is no doubt|proven beyond doubt)\b",
              r"\b(without exception|in every case|always holds true)\b"]
        hu = [r"\b(might|could|possibly|perhaps|uncertain|limited|may not|it depends)\b",
              r"\b(i don't know|i'm not sure|hard to predict|difficult to say)\b",
              r"\b(this is complex because|the situation is nuanced)\b"]  # A2: removed bare "complex"
        if _any(ov, r) and not _any(hu, r) and len(response_text) > 200:
            annotations.append(("epistemic_humility", "I_COGNITIVE", "medium",
                "Consider calibrating confidence levels. Some claims may benefit from acknowledging uncertainty."))

        # Analytical Depth — also fires on shallow long responses (A3)
        cx = [r"\b(ethical|moral|dilemma|tradeoff|trade-off|complex|nuance|philosophical)\b",
              r"\b(should i|what should|how do i decide|which is better|compare)\b"]
        dp = [r"\b(however|on the other hand|conversely|while .+ also|although|despite)\b",
              r"\b(root cause|underlying|fundamental|first principle)\b",
              r"\b(perspective|viewpoint|standpoint|lens)\b"]
        uc = _any(cx, u)
        hd = _any(dp, r)
        if uc and not hd and len(response_text) > 100:
            annotations.append(("analytical_depth", "I_COGNITIVE", "medium",
                "This question may benefit from deeper analysis — examining root causes, multiple perspectives, or underlying principles."))
        elif not hd and len(response_text) > 500:
            if _any([r"\b(strategy|design|architecture|decision|plan|policy|approach|system)\b",
                      r"\b(problem|issue|challenge|question|concern)\b"], r):
                annotations.append(("analytical_depth", "I_COGNITIVE", "low",
                    "A response this long on a substantive topic may benefit from examining root causes and multiple perspectives."))

        # Uncertainty Tolerance — raised to medium, removed user gate (A4)
        bi = [r"\b(yes or no|either .+ or|just do|the answer is clear)\b",
              r"\b(only (one |)option|no (other |)choice|must choose between)\b"]
        if _any(bi, r) and len(response_text) > 100:
            annotations.append(("uncertainty_tolerance", "I_COGNITIVE", "medium",
                "Complex questions often resist binary answers. Consider whether nuance is being lost."))

        # Pattern Recognition — NEW (B1)
        up = [r"\b(unprecedented|never seen before|no precedent|totally new|first time ever|never been done)\b",
              r"\b(no one has ever|nothing like this|completely unique|without parallel)\b"]
        pq = [r"\b(historically|similar to|pattern|precedent|parallel|resemblance|like the|reminiscent of)\b",
              r"\b(lesson from|echoes of|same (as|pattern)|recurring)\b"]
        if _any(up, r) and not _any(pq, r) and len(response_text) > 200:
            annotations.append(("pattern_recognition", "I_COGNITIVE", "medium",
                "Claims of uniqueness may miss historical parallels. Consider whether similar patterns or precedents exist."))

    # II. ETHICAL DOMAIN
    if _is_domain_active("II_ETHICAL"):
        # Justice & Fairness — expanded (A5)
        fn = [r"\b(always do this|everyone should|one-size-fits-all|universal solution)\b",
              r"\b(they always|those people|that group|they never)\b",
              r"\b(the problem with \w+ is)\b",
              r"\b(\w+ don't care about|typical \w+ behavior|\w+ never listen)\b",
              r"\b(all \w+ are)\b"]
        fp = [r"\b(fair|equitab|inclus|diverse|stakeholder|affected (party|group))\b",
              r"\b(balance|consider (all |both )sides|different (needs|circumstances))\b"]
        if _any(fn, r) and not _any(fp, r):
            annotations.append(("justice_fairness", "II_ETHICAL", "medium",
                "Consider whether this advice is fair to all stakeholders, especially those who may be disproportionately affected."))

        # Compassion & Empathy — NEW (B2)
        dh = [r"\b(just fire them|just replace them|doesn't matter if they|who cares if)\b",
              r"\b(collateral damage|acceptable losses|necessary sacrifice)\b",
              r"\b(only care about (profit|numbers|metrics|bottom line))\b",
              r"\b(they'll be fine|they'll get over it|it's not that bad for them)\b"]
        hc = [r"\b(human (cost|impact|toll)|emotional (impact|toll)|well-being|morale|livelihood)\b",
              r"\b(people (will|may|could) (be |feel )?affected|impact on (people|families|community))\b"]
        if _any(dh, r) and not _any(hc, r):
            annotations.append(("compassion_empathy", "II_ETHICAL", "high",
                "This framing may overlook human impact. Consider the emotional and personal cost alongside practical factors."))

        # Integrity — expanded rationalizations (A6)
        ir = [r"\b(white lie|harmless deception|technically (legal|true) but|loophole|exploit)\b",
              r"\b(don't tell|keep (it |)secret|hide this|don't mention)\b",
              r"\b(shortcut|bypass|circumvent|work around (the |)(rule|law|policy))\b",
              r"\b(nobody will know|just this once|bend the rules|stretch the truth)\b",
              r"\b(everyone does it|technically not illegal)\b",
              r"\b(what they don't know won't hurt them|we can always roll back)\b"]
        if _any(ir, r):
            annotations.append(("integrity_virtue", "II_ETHICAL", "high",
                "This recommendation may compromise integrity. Consider whether the advice would hold up under public scrutiny."))

        # Common Good — expanded (A7)
        sf = [r"\b(maximize (your |)(profit|gain|advantage)|at (any |all )costs?)\b",
              r"\b(take advantage of|exploit (the |)(situation|people|workers))\b",
              r"\b(not my problem|let someone else deal with it|i don't care about)\b"]
        cg = [r"\b(societ|communit|environment|sustainab|impact on (others|people))\b",
              r"\b(externalit|consequences (for|to) (others|society)|broader impact)\b",
              r"\b(future generations|public good|shared resource|external cost)\b"]
        if _any(sf, r) and not _any(cg, r):
            annotations.append(("common_good", "II_ETHICAL", "medium",
                "Consider the broader societal and environmental impact. Wisdom balances self-interest with the common good."))

    # III. TEMPORAL DOMAIN
    if _is_domain_active("III_TEMPORAL"):
        # Foresight — narrowed action patterns (A8)
        ac = [r"\b(you should|you could|do this|implement|deploy|execute)\b",
              r"\b(step \d|first,?\s+then|next,?\s+finally)\b"]
        co = [r"\b(consequen|result|impact|effect|lead to|cause|risk|potential downside)\b",
              r"\b(however|but consider|on the other hand|trade-?off|long[ -]term)\b",
              r"\b(second[ -]order|cascad|ripple|unintended|downstream)\b"]
        if _any(ac, r) and not _any(co, r) and len(response_text) > 300:
            annotations.append(("foresight", "III_TEMPORAL", "medium",
                "Consider the 2nd and 3rd-order consequences of this advice. What happens downstream? What if everyone followed it?"))

        # Long-term Orientation — NEW (B3)
        st = [r"\b(quick fix|temporary solution|hack it|good enough for now|just ship it|band-?aid)\b",
              r"\b(fastest (way|option|solution)|shortest (path|route))\b"]
        lt = [r"\b(long[ -]term|sustainable|tech debt|pay down|future[ -]proof|maintainable)\b",
              r"\b(scalab|extensib|invest in|foundation|architecture)\b"]
        if _any(st, r) and not _any(lt, r) and len(response_text) > 200:
            annotations.append(("long_term", "III_TEMPORAL", "medium",
                "Short-term solutions can accumulate hidden costs. Consider sustainability and long-term maintainability."))

        # Prudence — expanded risk vocabulary (A10)
        rk = [r"\b(risk|danger|caution|careful|backup|fallback|contingenc|what if|could go wrong)\b",
              r"\b(test (first|before)|start small|pilot|gradual|incremental)\b",
              r"\b(safeguard|mitigation|rollback plan|safety net|worst[ -]case|failover)\b",
              r"\b(recovery|canary|staged rollout|dry[ -]run|smoke test)\b"]
        hs = [r"\b(production|deploy|launch|invest|migrate|delete|remove|destroy)\b",
              r"\b(all (my |the |)(data|money|files|users)|everything)\b",
              r"\b(irreversible|critical|production data|customer[ -]facing|payment|financial|health)\b"]
        if _any(hs, r) and not _any(rk, r):
            annotations.append(("prudence", "III_TEMPORAL", "high",
                "High-stakes decisions deserve risk assessment. Consider what could go wrong and prepare contingency plans."))

        # Learning from Experience — NEW (B4)
        ex = [r"\b(lesson learned|previous experience|known issue|anti[ -]pattern|best practice)\b",
              r"\b(historically|in the past|we've seen|common (mistake|pitfall|error))\b",
              r"\b(war story|post[ -]mortem|retrospective|root cause analysis)\b"]
        pc = [r"\b(bug|error|failure|crash|incident|outage|migration|refactor)\b",
              r"\b(debug|troubleshoot|diagnose|investigate|fix)\b"]
        if _any(pc, u) and not _any(ex, r) and len(response_text) > 300:
            annotations.append(("learning_experience", "III_TEMPORAL", "low",
                "Consider whether known pitfalls or prior experience with similar problems could inform this response."))

    # IV. RELATIONAL DOMAIN
    if _is_domain_active("IV_RELATIONAL"):
        # Perspective-Taking — raised severity, no user gate (A11)
        ps = [r"\b(from (the |a )(different|other|user's|customer's|team's) perspective)\b",
              r"\b(stakeholder|viewpoint|standpoint|others (might|may|would))\b"]
        mp = [r"\b(team|group|organization|company|community|society|user|customer|client)\b",
              r"\b(negotiat|conflict|disagree|collaborat|partnership)\b"]
        if _any(mp, r) and not _any(ps, r) and len(response_text) > 200:
            annotations.append(("perspective_taking", "IV_RELATIONAL", "medium",
                "Consider how different stakeholders would view this situation. Wisdom sees through many eyes."))

        # Cultural Wisdom — NEW (B5)
        ca = [r"\b(in (the |)(western|eastern|american|european|asian) (world|culture|countries))\b",
              r"\b(everyone (celebrates|observes|follows)|universally (accepted|practiced))\b"]
        cw = [r"\b(cultur(al|ally)|locali[sz]|region|context|tradition|custom)\b",
              r"\b(in (some|many|certain) cultures|depending on (the |)region|varies by)\b"]
        if _any(ca, r) and not _any(cw, r) and len(response_text) > 200:
            annotations.append(("cultural_wisdom", "IV_RELATIONAL", "low",
                "Consider whether cultural assumptions are being presented as universal. Context and localization matter."))

        # Constructive Discourse — NEW (B6)
        dm = [r"\b(that's (just |)(wrong|stupid|nonsense|ridiculous|absurd))\b",
              r"\b(that doesn't make sense|that's not (even |)worth|ignore that)\b",
              r"\b(obviously wrong|clearly incorrect|no one (would|should) think)\b"]
        en = [r"\b(however|on the other hand|while (some|others)|although|counterargument)\b",
              r"\b(valid point|fair argument|good question|i see (your |the )point)\b",
              r"\b(let('s| us) consider|another (way|perspective)|alternatively)\b"]
        if _any(dm, r) and not _any(en, r):
            annotations.append(("constructive_discourse", "IV_RELATIONAL", "medium",
                "Dismissing opposing views without engagement weakens reasoning. Consider engaging with the strongest version of the counterargument."))

        # Generativity — NEW (B7)
        de = [r"\b(let me (do|handle|fix|write) (it |this |that )for you)\b",
              r"\b(just ask me (next time|whenever)|you don't need to know how)\b",
              r"\b(i'll (just |)take care of (it|everything)|leave it to me)\b"]
        te = [r"\b(here's how (you|to)|let me (show|explain|walk you through))\b",
              r"\b(next time you can|the (reason|principle|concept) is|understanding why)\b",
              r"\b(step[ -]by[ -]step|the key insight|once you understand)\b"]
        if _any(de, r) and not _any(te, r) and len(response_text) > 200:
            annotations.append(("generativity", "IV_RELATIONAL", "low",
                "Consider whether this approach teaches and empowers, or creates dependency. Explaining 'why' builds lasting capability."))

    logger.debug("wisdom-guard: evaluated response, found %d annotation(s)", len(annotations))
    return annotations


# ---------------------------------------------------------------------------
# Annotation Formatter
# ---------------------------------------------------------------------------

def _format_annotations(annotations):
    if not annotations:
        return None
    seen = set()
    unique = []
    for pillar, domain, severity, text in annotations:
        if pillar not in seen:
            seen.add(pillar)
            unique.append((pillar, domain, severity, text))
    unique.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x[2], 3))
    # G1 fix: renamed from "sensitivity" to "verbosity"
    if _VERBOSITY == "low":
        unique = [a for a in unique if a[2] == "high"]
    elif _VERBOSITY == "medium":
        unique = [a for a in unique if a[2] in ("high", "medium")]
    if not unique:
        return None
    lines = ["\n---", "[Wisdom Guard]"]
    for pillar, domain, severity, text in unique:
        icon = {"high": "!", "medium": "~", "low": "·"}.get(severity, "·")
        lines.append(f"  {icon} [{pillar.replace('_', ' ').title()}] {text}")
    lines.append("[/Wisdom Guard]")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------

def on_pre_llm_call(session_id, user_message, conversation_history, is_first_turn, model, platform, **kwargs):
    """D1 fix: only active domains in prompt."""
    try:
        framework = _build_evaluation_prompt()
        if not framework:
            return None
        if is_first_turn:
            refs = _get_wisdom_references()
            if refs:
                framework += f"\n\n[Wisdom Library References]\n{refs}\n[/Wisdom Library References]"
        return {"context": framework}
    except Exception as e:
        logger.error("wisdom-guard pre_llm_call error: %s", e)
        return None


def on_transform_llm_output(response_text, session_id, model, platform, **kwargs):
    """C1 fix: passes real conversation_history."""
    try:
        if not response_text or len(response_text.strip()) < 50:
            return None
        user_message = kwargs.get("user_message", "")
        conversation_history = kwargs.get("conversation_history", [])
        annotations = _evaluate_response(response_text, user_message, conversation_history)
        if not annotations:
            logger.debug("wisdom-guard: evaluation complete — no concerns detected")  # D2
            return None
        formatted = _format_annotations(annotations)
        if formatted:
            return response_text + "\n" + formatted
        return None
    except Exception as e:
        logger.error("wisdom-guard transform_llm_output error: %s", e)
        return None


def on_pre_tool_call(tool_name, args, task_id, **kwargs):
    """E4 fix: checks execute_code/write_file too."""
    try:
        if tool_name == "terminal":
            command = args.get("command", "") if isinstance(args, dict) else str(args)
            for pattern, description in _DANGEROUS_TERMINAL_PATTERNS:
                if re.search(pattern, command):
                    logger.warning("wisdom-guard BLOCKED terminal: %s (command: %s)", description, command[:100])
                    return {"action": "block", "message": (
                        f"[Wisdom Guard — Prudence] Blocked: {description}. "
                        f"This command pattern is extremely destructive and irreversible. "
                        f"Please reconsider the approach or add appropriate safeguards "
                        f"(backups, dry-runs, confirmation steps) before proceeding.")}
        # E4: Code execution / file writing
        if tool_name in ("execute_code", "write_file"):
            code = ""
            if isinstance(args, dict):
                code = args.get("code", "") or args.get("content", "") or ""
            else:
                code = str(args)
            for pattern, description in _DANGEROUS_CODE_PATTERNS:
                if re.search(pattern, code):
                    logger.warning("wisdom-guard BLOCKED %s: %s", tool_name, description)
                    return {"action": "block", "message": (
                        f"[Wisdom Guard — Prudence] Blocked: {description}. "
                        f"This code pattern poses a significant safety risk. "
                        f"Please use safer alternatives.")}
        return None
    except Exception as e:
        logger.error("wisdom-guard pre_tool_call error: %s", e)
        return None


def on_post_llm_call(session_id, user_message, assistant_response, conversation_history, model, platform, **kwargs):
    """D2 fix: logs even when no annotations found."""
    try:
        if not assistant_response:
            return
        annotations = _evaluate_response(assistant_response, user_message, conversation_history)
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id, "model": model, "platform": platform,
            "user_message_preview": (user_message or "")[:200],
            "annotation_count": len(annotations),
            "annotations": [{"pillar": p, "domain": d, "severity": s, "text": t}
                            for p, d, s, t in annotations] if annotations else [],
        }
        log_file = _LOG_DIR / f"wisdom-evaluations-{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error("wisdom-guard post_llm_call error: %s", e)


# ---------------------------------------------------------------------------
# Skill Registration
# ---------------------------------------------------------------------------
_SKILL_DIR = _PLUGIN_DIR / "skills" / "wisdom"


def _register_wisdom_skill(ctx):
    skill_path = _SKILL_DIR / "SKILL.md"
    if skill_path.exists():
        try:
            ctx.register_skill("wisdom", _SKILL_DIR)
            logger.info("wisdom-guard: registered /wisdom skill")
        except Exception as e:
            logger.warning("wisdom-guard: failed to register /wisdom skill: %s", e)


# ---------------------------------------------------------------------------
# Config Loader
# ---------------------------------------------------------------------------

def _load_config(ctx):
    """Accepts 'verbosity' (new) and 'sensitivity' (legacy fallback)."""
    global _VERBOSITY, _ACTIVE_DOMAINS
    try:
        cfg = ctx.get_config("skills.config.wisdom_guard") or {}
    except Exception:
        cfg = {}
    raw = cfg.get("verbosity") or cfg.get("sensitivity", "low")
    val = str(raw).lower().strip()
    if val in ("low", "medium", "high"):
        _VERBOSITY = val
        logger.info("wisdom-guard: verbosity set to '%s'", _VERBOSITY)
    else:
        logger.warning("wisdom-guard: invalid verbosity '%s', defaulting to 'medium'", val)
    domain_map = {"cognitive_domain": "I_COGNITIVE", "ethical_domain": "II_ETHICAL",
                  "temporal_domain": "III_TEMPORAL", "relational_domain": "IV_RELATIONAL"}
    for cfg_key, domain_key in domain_map.items():
        enabled = cfg.get(cfg_key, True)
        if isinstance(enabled, str):
            enabled = enabled.lower() not in ("false", "0", "no", "off")
        if enabled:
            _ACTIVE_DOMAINS.add(domain_key)
        else:
            _ACTIVE_DOMAINS.discard(domain_key)
    logger.info("wisdom-guard: active domains = %s", sorted(_ACTIVE_DOMAINS))


# ---------------------------------------------------------------------------
# Plugin Entry Point
# ---------------------------------------------------------------------------

def register(ctx):
    logger.info("wisdom-guard: initializing Wisdom Guard plugin v1.2")
    _load_config(ctx)
    ctx.register_hook("pre_llm_call", on_pre_llm_call)
    ctx.register_hook("transform_llm_output", on_transform_llm_output)
    ctx.register_hook("pre_tool_call", on_pre_tool_call)
    ctx.register_hook("post_llm_call", on_post_llm_call)
    _register_wisdom_skill(ctx)
    _load_wisdom_library()
    logger.info("wisdom-guard: all hooks registered, wisdom library loaded")
