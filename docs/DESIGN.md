# Sweep: design

## The asymmetry

Proving that a document says something is cheap: show the sentence. Proving
that it does **not** say something is the expensive direction, and it is the
one people actually need before they act. A launchpad wants to know the
terms contain no unlimited-mint clause. A buyer wants to know a contract has
no hidden auto-renewal. A grant program wants to know a licence has no
copyleft terms. An AI reading the whole document in one call cannot give
that assurance: its context, attention and summary all leave room for a
clause it never looked at.

Sweep turns "it is not there" into a statement with a coverage proof.

## Coverage, by construction

A document is uploaded once and sealed by its sha256. It is then cut into
fixed windows: chunk `i` is `[i*1600, i*1600 + 2400)`, so consecutive chunks
overlap by 800 characters, and the last chunk reaches the end.

Two properties follow, and both are tested exhaustively, over every start
position, for fourteen document lengths from 1 to 48,000 characters:

1. Every character is in some chunk.
2. **Every passage of up to 800 characters lies wholly inside at least one
   chunk.** A clause cannot hide by straddling a boundary.

A question scans each chunk at most once. Its status becomes `ABSENT` only in
the transaction that scans the **last unscanned chunk** and finds nothing, so
there is no code path to `ABSENT` without full coverage. A brute force over
every order of every subset of chunks checks exactly that.

## What validators agree on

| Step | Leader returns | A validator accepts it when |
| --- | --- | --- |
| `scan` | `{"found": bit, "quote": text}` | its own scan gives the **same bit**; if found, the leader's quote is **verbatim** in the chunk (checked in code) **and** its own model confirms that quote is a mention |
| `contest` | `{"mentions": bit}` | its own answer is the same bit |

The bit is compared exactly. The quote is not part of the vote (two honest
models may pick different sentences), but it cannot be invented, because the
contract checks it is a substring of the chunk, and it cannot be irrelevant,
because every validator re-checks it is a mention before agreeing. A stored
`PRESENT` therefore always carries a real, verified quote.

## The contest window

The weak point of any negative is a false negative: every validator missed
it. Sweep does not pretend that cannot happen. A question carries a contest
window, chosen when it is asked and fixed forever. During the window, anyone
who finds the clause can submit a verbatim quote from a named chunk:

- the substring check runs first, so a fabricated quote is refused
  (`QUOTE_NOT_IN_CHUNK`) before any model is called;
- validators then agree, exactly, whether that quote is a mention;
- if it is, the verdict becomes `PRESENT` permanently.

A narrow quote is a far easier question than a whole chunk, which is why a
contest can surface what a scan missed. After the window, `ABSENT` is final.
`PRESENT` is never reversed: the text is sealed and the quote is in it.

## Who may write

| Write | Who | Policy |
| --- | --- | --- |
| `open_document` | anyone | sender is the owner; length and sha256 fixed |
| `append` | the owner | only while uploading; the seal is checked when the last character arrives (`SEALED` or `CORRUPT`) |
| `ask` | anyone | only on a sealed document; target and window fixed; 50 per document |
| `scan` | anyone | question id and chunk index only; once per chunk |
| `contest` | anyone | only while `ABSENT` is contestable; verbatim quote checked before any model call |

The only text that reaches a model is the sealed document, the question's
target and, for a contest, a substring of the sealed document. Nobody can
change a document after sealing, so a consumer that names a document and a
question names exactly what was read.

## Consumers

`Listing` pins its red flags word for word and a minimum window. A question
counts only if its target is exactly a pinned flag, it is about the same
document, and its window is long enough, so a project cannot rephrase a red
flag into something harmless or shorten the contest. Any flag `PRESENT`
rejects permanently, with the quote; all flags `ABSENT_FINAL` lists.

`Bounty` pays the account whose transaction produced the verified mention,
scan or contest. That pays for the reading. A document's owner is never paid
for finding something in its own document. A final `ABSENT` returns the
money to the sponsor.

## What it does not claim

- A mention is found when some passage of up to 800 characters expresses it.
  A "clause" assembled from sentences far apart is not guaranteed to be seen.
- `ABSENT` means no validator found it and nobody contested it in time. The
  window is the defence against a shared false negative; choose it to match
  what is at stake.
- Sweep reads text. It says nothing about what the deployed token contract
  actually does.
