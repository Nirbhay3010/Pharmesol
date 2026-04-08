# Future Improvements

What I would build next given more time, in order of impact.

## Core Agent Intelligence

**RAG Knowledge Base** — Add a retrieval layer so the agent can pull real answers from product docs, pricing sheets, and competitive positioning instead of relying only on what's hardcoded in the prompt. This is the difference between an agent that deflects and one that actually sells. Would use OpenAI embeddings with ChromaDB, chunked product documentation, and a `search_knowledge_base` tool the agent calls when it needs to answer a product question.

**Two-Stage Intent Classification** — Run a lightweight intent classifier (`gpt-5.4-mini`) on every utterance, returning structured labels (SALES_INQUIRY, SUPPORT, PRICING, SCHEDULING, COMPETITIVE, REGULATORY) with confidence scores. This feeds into routing, analytics, and post-call summaries. Matches the two-stage classification from the system design — fast classifier for clear intents, frontier model for ambiguous ones.

**Multi-Contact Identification** — Identify who is calling from a known pharmacy, not just which pharmacy. The owner cares about pricing, the tech cares about workflow, and the front-desk person cares about ease of use — the conversation should adapt to the caller's role accordingly.

## Conversation Resilience

**Sentiment Monitoring + Auto-Escalation** — Track sentiment turn-by-turn and auto-escalate when frustration persists across two or more consecutive messages. Currently the agent has no awareness that a caller is getting increasingly annoyed. Would trigger a warm handoff with full context summary.

**Session Persistence + Resume** — If a call drops or the caller hangs up mid-conversation, persist the session state so we can resume where we left off on callback after a quick identity verification. Nobody wants to repeat themselves.

**Per-Pharmacy Memory** — Build persistent memory across calls so returning callers aren't treated like strangers. If HealthFirst called last week about pricing, the agent should open with "last time we spoke you were interested in our automation tier — did you get a chance to think about it?"

## Post-Call Intelligence

**Call Summary Card** — Auto-generate a structured summary when the conversation ends: who called, what they wanted, what was discussed, actions taken, objections raised, and a hot/warm/cold lead score. Display it in the UI and make it CRM-ready.

**Analytics Dashboard** — Aggregate call summaries into a lightweight dashboard showing call volume, intent distribution, conversion funnel, and common objections over time. This turns the agent from a single-call tool into a sales intelligence system.

## Production Hardening

**Evaluation Suite** — Automated test conversations that run against the agent and verify it doesn't hallucinate, handles edge cases, resists prompt injection, and follows the gather-confirm-execute pattern consistently. You can't ship an agent you can't regression-test.

**Session Storage** — Replace in-memory session dict with Redis or SQLite so sessions survive server restarts and can scale horizontally beyond a single process.

**Objection Handling Playbook** — Structured responses for "we already have a system", "too expensive", "not interested right now" loaded via RAG so the agent handles pushback with pre-approved, effective responses instead of improvising.

**Failed Handoff Fallback** — When an escalation target is unavailable, automatically offer callback booking or priority ticket creation. The agent should never leave a caller in silent hold.
