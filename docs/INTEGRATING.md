# Integrating Sweep

## 1. Upload and seal (owner)

```bash
genlayer write <sweep> open_document --args "Token terms v1" 5112 <sha256 hex of the full text>
genlayer write <sweep> append --args D1 "<up to 8,000 characters>"
```

Append pieces in order until the full length is reached. The last append
returns `SEALED` if the sha256 matches, or `CORRUPT`, in which case open a new
document. Up to 48,000 characters, 30 chunks. Refusals: `TITLE_SHAPE`,
`LENGTH_SHAPE`, `LENGTH_RANGE`, `DIGEST_SHAPE`, `NOT_OWNER`, `NOT_UPLOADING`,
`PIECE_SHAPE`, `TOO_LONG`.

## 2. Ask (anyone)

```bash
genlayer write <sweep> ask --args D1 "a clause letting the team create new tokens without a fixed limit" 86400
```

The target is up to 300 characters; the window is 0 to 7 days, in seconds.
Returns `q1`. Refusals: `NOT_SEALED`, `TARGET_SHAPE`, `WINDOW_SHAPE`,
`WINDOW_RANGE`, `TOO_MANY_QUESTIONS`.

## 3. Scan (anyone)

```bash
genlayer write <sweep> scan --args q1 0
```

One chunk per transaction, each once. Returns `SCANNING`, `PRESENT` (a
verified quote was found, the scan ends) or `ABSENT` (this was the last
chunk). Refusals: `NO_SUCH_CHUNK`, `ALREADY_SCANNED`, `SCAN_CLOSED`. A model
error or validator disagreement stores nothing; send it again.

## 4. Contest (anyone, during the window)

```bash
genlayer write <sweep> contest --args q1 2 "<exact text from chunk 2>"
```

Refusals: `NOT_CONTESTABLE`, `NO_SUCH_CHUNK`, `QUOTE_NOT_IN_CHUNK` (checked
before any model call), `NOT_A_MENTION`. `get_chunk(D1, i)` returns the exact
text of a chunk to quote from.

## 5. Consume

```python
q = json.loads(gl.get_contract_at(SWEEP).view().get_question(question_id))
if q["doc"] != MY_DOC or q["target"] != MY_TARGET or q["window"] < MY_MIN_WINDOW:
    raise gl.vm.UserError("[EXPECTED] WRONG_QUESTION")
if q["verdict"] == "PRESENT":          # q["quote"], q["hit_chunk"], q["found_by"]
    ...
elif q["verdict"] == "ABSENT_FINAL":
    ...
```

| View | Returns |
| --- | --- |
| `verdict(q)` | `SCANNING`, `PRESENT`, `ABSENT_CONTESTABLE` or `ABSENT_FINAL` |
| `get_question(q)` | document, target, window, chunks scanned, verdict, quote, chunk, finder |
| `get_document(D)` | owner, title, length, sha256, status, number of chunks |
| `get_chunk(D, i)` | the exact text of chunk `i` |

Pin the target text and a minimum window, as `Listing` does: anyone can ask
any question, so a consumer must check it is reading the question it means.
`Listing` and `Bounty` in this repository are the two reference consumers.
