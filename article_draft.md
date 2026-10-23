# InboxSloth AI: Let Local AI Read the Noise

> **Status:** Editable draft. Replace bracketed notes with observations and genuine screenshots before publishing.

Group chats are useful and exhausting. For a college project, the important details can be scattered across jokes, context, reminders, and half-finished decisions. InboxSloth AI is a small local-first Flask application that turns a plain-text export into a daily briefing.

## What it does

The user drops in a `.txt` export. Flask validates it in memory, sends a carefully constrained prompt to Gemma 3 1B through Ollama, validates the structured JSON response, and renders the result into separate cards for summaries, key points, announcements, tasks, deadlines, and pending decisions.

## Why local open-weight AI?

The application does not need a paid API key and does not upload the transcript to a hosted AI provider. Running inference locally gives the user more control over where sensitive messages go. It is not a perfect privacy guarantee: the operating system, model runtime, backups, and other local processes still matter.

## What I learned

- Structured output still needs server-side validation.
- Prompt injection defenses should treat imported text as untrusted data.
- Empty arrays are more honest than guessed tasks or dates.
- A local model can be useful without pretending to be perfectly accurate.

## Demonstration

> **Add genuine screenshot(s) here after running the app:** `[screenshot path or link]`

For a transparent time-saving measurement, I will compare the time to identify the same set of action items manually and with the digest across `[number]` synthetic conversations, recording the method and actual observations.

## Limitations and next steps

The MVP supports only UTF-8 `.txt` exports, on-demand generation, and a single local model. Future work could add more export parsers, user-configurable prompts, explicit date normalization, and optional scheduling without claiming that messages are read automatically today.

`#devchallenge` `#hf26challenge`

**AI disclosure:** This article was prepared with AI assistance and reviewed by the project author.
