# Question bank + exam papers API (Member 3)

Base URL: `/api/v1`

## Questions
| Method | Path | Purpose |
|---|---|---|
| POST | `/questions/import` | Upload .pdf / .xlsx / .csv (multipart field `file`). Returns `{imported, duplicates, errors[{row, reason}]}` |
| GET | `/questions` | List. Query: `subject`, `topic`, `difficulty`, `q`, `page`, `page_size` |
| GET | `/questions/filters` | Dropdown values `{subjects[], topics[], difficulties[]}`; optional `subject` narrows topics |
| POST | `/questions/random` | Random questions: `{subject?, topics?[], difficulty?, count, exclude_ids?[]}` -> `{items, requested, returned, available, shortfall}`. The paper editor's "Change question" uses it, passing every question already in the paper as `exclude_ids` |
| DELETE | `/questions/{id}` | Delete a question (also removes it from any exam paper) |

Question: `{id, subject, difficulty, topic, question, created_at}`

## Exam papers
| Method | Path | Purpose |
|---|---|---|
| POST | `/questions/papers` | Create by hand: `{title, instructions?, duration_minutes?, items:[{question_id, marks}]}` |
| POST | `/questions/papers/generate` | Random paper: `{title, instructions?, duration_minutes?, marks_each?, allow_partial?, subject?, topics?[], difficulty? \| mix?{easy,medium,hard}, count?}`. 409 if fewer questions match than asked (unless `allow_partial`) |
| GET | `/questions/papers` | List: `[{id, title, duration_minutes, created_at, question_count, total_marks}]` |
| GET | `/questions/papers/{id}` | Paper with ordered `items:[{position, marks, question}]` |
| PUT | `/questions/papers/{id}` | Replace title / instructions / duration / questions (same body as create) |
| DELETE | `/questions/papers/{id}` | Delete the paper (questions stay in the bank) |

Tables: `questions`, `exam_papers`, `exam_paper_items(paper_id, question_id, position, marks)`.
Member 2 (`exams`): an exam can reference `exam_papers.id` to know which questions to show.
