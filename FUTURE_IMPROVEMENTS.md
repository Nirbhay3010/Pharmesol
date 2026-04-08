# What I'd Build Next

## Agent Intelligence
- **RAG knowledge base** — so the agent answers product questions from real docs instead of guessing or deflecting.
- **Intent classifier** — lightweight model on every utterance for structured routing, analytics, and post-call summaries.
- **Multi-contact ID** — identify *who* is calling from a known pharmacy and adapt the conversation to their role.

## Conversation Resilience
- **Sentiment monitoring** — detect frustration over consecutive turns and auto-trigger escalation.
- **Session resume** — persist state so dropped calls can pick up where they left off after quick verification.
- **Per-pharmacy memory** — returning callers get continuity, not a cold start.

## Post-Call Intelligence
- **Call summary card** — auto-generated structured output (who called, what they need, lead score, next steps) ready for CRM which helps look for areas of improvement.
- **Analytics dashboard** — call volume, intent distribution, conversion funnel, common objections over time.

## Framework & Prompt Engineering
- **LangChain/LangGraph migration** — replace the hand-rolled agent loop with LangGraph for structured state machines, built-in tool orchestration, and easier chaining of multi-step workflows (RAG retrieval → classification → response).
- **Prompt optimization** — A/B test system prompts, measure conversion rate per prompt variant, compress token usage with few-shot examples, and tune temperature/top-p per conversation stage (lower for tool calls, higher for rapport building).
- **Model benchmarking** — evaluate different models on quality, latency, tool-calling reliability, and cost per conversation to find the best fit per task.

## Production Hardening
- **Eval suite** — automated test conversations to catch hallucination, prompt injection, and guardrail failures.
- **Persistent sessions** — Redis/SQLite instead of in-memory so sessions survive restarts.
- **Objection playbook** — pre-approved responses for "too expensive", "we already have a system", etc. via RAG.

