# AI exam paper (examiner side, Groq)

An examiner writes ONE prompt, for example *"20 MCQs on Operating Systems, 40% easy, 40% medium, 20% hard"*.
The AI writes every question (4 options, correct answer, solution), saves them in **that examiner's own
question bank**, and builds the exam paper. It opens in **Exam papers**, where it can be edited, printed
and attached to an exam like any other paper.

## One-time setup
1. Make a free key at https://console.groq.com/keys (no card needed).
2. Open the `.env` file in the project root and put it after `GROQ_API_KEY=`.
3. Restart `run_backend.bat`.

## Use it
Log in as an **examiner** -> Question bank -> **AI paper** tab -> write the prompt -> *Create paper with AI*.
(Only examiners and super admins can use it. Admins and students cannot.)

## Settings (all optional, in `.env`)
| Name | Default | Meaning |
|---|---|---|
| `GROQ_API_KEY` | empty | Your Groq key (`LLM_API_KEY` also works) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Main model |
| `GROQ_FALLBACK_MODEL` | `llama-3.1-8b-instant` | Used if the main model is busy or refused |
| `AI_MAX_QUESTIONS` | `40` | Most questions in one paper |
| `AI_BATCH_SIZE` | `8` | Questions per Groq call (small batches suit the free token limits) |

## How it works (backend/app/ai/)
- `routes.py`   `GET /api/v1/ai/status`, `POST /api/v1/ai/generate-paper` (examiner / super admin only)
- `service.py`  plan call -> question batches -> validation (same rules as file import) -> save
- `groq_client.py`  Groq chat API in JSON mode, retries on rate limit, fallback model
- Bad questions (wrong option count, duplicate options, no valid answer letter) are dropped and re-asked.
- A question already in the examiner's bank is reused, never duplicated.

AI can make mistakes: always check the questions and answers before using a paper in an exam.
