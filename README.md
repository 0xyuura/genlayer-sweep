# Sweep

**Consensus that a document does NOT say something.**

Deployed on GenLayer Studio (studionet) at
[`0x168295C86AB1b2b4D3F8662002B5FBA5F8415ff9`](https://explorer-studio.genlayer.com/address/0x168295C86AB1b2b4D3F8662002B5FBA5F8415ff9),
with two consumer contracts. See [Exercised on chain](#exercised-on-chain).

Call it without a local setup:
[open it in GenLayer Studio](https://studio.genlayer.com/?import-contract=0x168295C86AB1b2b4D3F8662002B5FBA5F8415ff9)

> Built during Bradbury's Phase 2 reset, when builders were asked to use
> Studio. The same three files will be redeployed unchanged to the new
> Bradbury once it opens.

## The problem

Proving a document **says** something is cheap: show the sentence. Proving it
does **not** is the hard direction, and it is the one that protects people.
"These token terms contain no clause letting the team mint without limit" is
only worth something if every part of the terms was read. An AI that reads a
long document in one go and answers "no such clause" gives no such
assurance: nothing shows which parts it actually looked at.

Every earlier primitive of this kind confirms that something is there. None
proves that something is absent.

## The move: coverage you can check

1. **Seal.** The owner uploads the document; the contract checks its sha256
   when the last character arrives (`SEALED`, or `CORRUPT`). It never changes
   again.
2. **Chunk.** The text is cut into fixed windows of 2,400 characters every
   1,600: consecutive chunks overlap by 800, so **any passage of up to 800
   characters lies wholly inside some chunk**. A clause cannot hide on a
   boundary.
3. **Ask.** Anyone asks a question ("a clause letting the team create new
   tokens without a fixed limit") with a contest window.
4. **Scan.** Each chunk is scanned once, by exact consensus on one bit.
   - **PRESENT** needs one hit. Its quote must appear **verbatim** in the
     chunk (checked in code) and every validator's own model must confirm the
     quote is a mention. The scan stops there.
   - **ABSENT** is set only by the scan of the **last unscanned chunk**, so
     there is no path to it without full coverage.
5. **Contest.** While the window is open, anyone can overturn ABSENT with a
   verbatim quote from a named chunk. A fabricated quote is refused before
   any model is called. After the window, ABSENT is final.

What validators compare on a scan:

```json
{"found": true, "quote": "To fund ongoing operations, the Foundation may issue additional LUMEN at any time..."}
```

The bit must match exactly. The quote may differ between honest models, but
it must be in the text and must itself be a mention.

## Who may write

| Write | Who | Policy |
| --- | --- | --- |
| `open_document` | anyone | sender is the owner; length and sha256 fixed |
| `append` | the owner | only while uploading; seal checked at the last character |
| `ask` | anyone | sealed documents only; target and window fixed forever |
| `scan` | anyone | question id + chunk index only; once per chunk |
| `contest` | anyone | only while ABSENT is contestable; verbatim check before any model call |

## Two consumers, opposite directions

| Consumer | Acts on | Guarantee |
| --- | --- | --- |
| `Listing` | **ABSENT_FINAL** for every red flag, or **PRESENT** for any | a project is listed only when every pinned red flag is provably absent; one quote rejects it forever |
| `Bounty` | **PRESENT** | pays whoever's transaction found the verified mention, never the document's owner; final ABSENT returns the money |

`Listing` pins its red flags word for word and a minimum contest window, so a
project cannot rephrase a red flag into something harmless (`NOT_A_RED_FLAG`)
or shorten the window (`WINDOW_TOO_SHORT`). `Bounty` makes the exhaustive
scan self-funding: the reward goes to whoever does the reading that matters.

Full argument in [docs/DESIGN.md](docs/DESIGN.md); interface in
[docs/INTEGRATING.md](docs/INTEGRATING.md).

## Exercised on chain

GenLayer Studio, 5 validators per transaction. All three deployments are byte
identical to the files here (`tools/verify.mjs`):

| Contract | Address |
| --- | --- |
| `Sweep` | [`0x168295C86AB1b2b4D3F8662002B5FBA5F8415ff9`](https://explorer-studio.genlayer.com/address/0x168295C86AB1b2b4D3F8662002B5FBA5F8415ff9) |
| `Bounty` (question `q1`) | [`0x06A5a43F433E04aDCa60995d359b7F562EF4DBD7`](https://explorer-studio.genlayer.com/address/0x06A5a43F433E04aDCa60995d359b7F562EF4DBD7) |
| `Listing` | [`0x914F992fcee59948c7B9A69Df40985ae5EBcB934`](https://explorer-studio.genlayer.com/address/0x914F992fcee59948c7B9A69Df40985ae5EBcB934) |

Two versions of a token's terms of use, twelve sections each, differing in
one clause:

- `D1`, v1.2: section 7.3 reads "To fund ongoing operations, the Foundation
  may issue additional LUMEN at any time, in any amount it considers
  appropriate, without notice to holders."
- `D2`, v1.3: section 7.3 reads "The total supply is fixed at 100,000,000
  LUMEN. No further LUMEN can ever be issued by anyone, including the
  Foundation."

| Question | Document | Target | Result |
| --- | --- | --- | --- |
| `q1` | D1 | unlimited minting | **PRESENT** in chunk 0, with the 7.3 quote; scan stopped |
| `q2` | D1 | freezing or seizing balances | **ABSENT** after chunks 0 and 1; final after 60 s |
| `q3` | D2 | unlimited minting | **ABSENT** after both chunks |
| `q4` | D2 | freezing or seizing balances | **ABSENT** after both chunks |
| `q5` | D1 | freezing or seizing balances (1 h window) | **ABSENT**; a contest with a real but irrelevant sentence was refused `NOT_A_MENTION` |

Then: an outsider's `append` was refused `NOT_OWNER`; scanning `q1` after
PRESENT, `SCAN_CLOSED`; a fabricated contest quote, and a real sentence quoted
from the wrong chunk, both `QUOTE_NOT_IN_CHUNK` with no model call; the
Bounty refused an outsider's funding (`[REFUSED] NOT_SPONSOR`, value credited
back) and an early settle (`NOT_RESOLVED`), then paid the whole 0.005 GEN to
the account whose scan found the clause; the Listing **REJECTED** D1 with the
7.3 quote, refused D2 while its window was open (`NOT_FINAL`), and **LISTED**
D2 once it closed.

All 34 transactions on Studio, with what each returned or refused:

| Step | Result | Transaction |
| --- | --- | --- |
| `sweep_deploy` | null | `0x662e337a2b36e17fe8b0427533c396e9344f19343a4d4aadcf221e8d9448d5f0` |
| `open_D1` | D1 | `0x4e9cf254c2e3ea4c0d818a7c154712783133980db05b526913b80aff3cb64709` |
| `append_by_outsider` | [EXPECTED] NOT_OWNER | `0x78c8ea7be2d339f2d12e11c45cc231d4808ce3087587d56fbc79315db7f7557b` |
| `append_D1` | SEALED | `0xd55baf5da8c5166bf03592d917088c0d49fbc92d6b32bc372eda0532fd8adc1e` |
| `ask_q1_mint` | q1 | `0xc2b06b639b4a9646203a258542e024be60bd8b1a517d6666bb2d48510e727b2d` |
| `ask_q2_freeze` | q2 | `0xcefbf63ab4b5e5180810e98016ec5a9a1b613fbc3732d409f68e51f6fee825ac` |
| `bounty_deploy` | null | `0xa91e9e92236a3e998644cddc3a1180075438c5a2bf3c9742f3c49cccdb30bcb9` |
| `fund_by_outsider` | [REFUSED] NOT_SPONSOR | `0xabf94368a61bf4dfb4cae4a1fb9cb74c8e0071356b860769639077da7dcde25a` |
| `fund` | FUNDED 5000000000000000 | `0x8b44820b31f84201556d6817c8e9b3a4066d1b3d168fc8def465880e577d0e54` |
| `settle_too_early` | [EXPECTED] NOT_RESOLVED | `0x0933e87106337c129bc8e4b796e8287dad3659653d3883855c362faa9e86ce87` |
| `scan_q1_c0` | PRESENT | `0xa1c21a03660bf8db29f95ed056f346084a4f348dbb30e07fef284405dccc9baf` |
| `scan_q1_after_present` | [EXPECTED] SCAN_CLOSED | `0xa0fb7bf1072ba010822b116e6460860f665b6559f4c02fcb31bcb726d2fb4269` |
| `scan_q2_c0` | SCANNING | `0x18f3592a75c02172fa70eca81a328b50b411664761a85c5de4d03494ab4d2e79` |
| `scan_q2_c1` | ABSENT | `0xa02dcc81707744a459e704c589b418678ade23ead6bcbc5af62d874c36f95daa` |
| `contest_fabricated` | [EXPECTED] QUOTE_NOT_IN_CHUNK | `0xa560feaf196b63a761fa68a8c4672992b684bcc22857fb691e51413924b54862` |
| `contest_not_a_mention` | [EXPECTED] QUOTE_NOT_IN_CHUNK | `0x18b1a32eb612493620fa8670d7179452257b93418ebac40b5ee7d31090063ed8` |
| `settle_bounty` | FOUND | `0x6503e1fae0622e15f94ede7674d61e671a209e010182d32e9a7a864a88adcd75` |
| `withdraw_eve` | null | `0x2bc59f80067e3991a96aca69293ecd76ff337822dcd46aad27eca7142935779f` |
| `open_D2` | D2 | `0xef864facd8bba47e3040b4492adfc3b179064a0fd614a88126cf568714d81930` |
| `append_D2` | SEALED | `0x340d5f707c22372a4667b63c0f7aa01fbacb3dd2921270c4ac9e04ecb2ef7b6b` |
| `ask_q3_mint` | q3 | `0x951486e5ea6bee405cd224f09c2b75dba95e9f3d6be3081e6e48e0568ff4d47c` |
| `ask_q4_freeze` | q4 | `0x0ada9b1df2cdb1a9c43d1429138027739ed4a2300b56c7107a0e39d1dbbb3000` |
| `scan_q3_c0` | SCANNING | `0x04faa9f7c9258317b68b8a69b07edad4b964c78d6aa6d2cec6c6dd5007e805c0` |
| `scan_q3_c1` | ABSENT | `0xf4a6ffb35ea0789d5f1a95059d2fdc9c2c0ede8b4e68205bce65dc1dc6041b82` |
| `scan_q4_c0` | SCANNING | `0xb38d62372c5e10f9596a3307183d59a9430d3fd52b7569a19ab35170269d62eb` |
| `scan_q4_c1` | ABSENT | `0xab1e08634607495b6386c86fd256116e9ff9fa5e1af0ac6a80754e7d4ecdaeea` |
| `listing_deploy` | null | `0x645617e204ae99033cafad71305d51bfb8e01bf55286e06fed18f07e7a966a16` |
| `apply_D1` | REJECTED | `0x5dd2aa5cbe3ad458134c10669456042763816017133973c74881948bb9e3abd1` |
| `apply_D2_early` | [EXPECTED] NOT_FINAL | `0xe89977d94f3496ef2217859ac415b01f8e8750f7fa77744abe1ca6a2b708779f` |
| `apply_D2` | LISTED | `0x107ee262da4768328a042052c8ecf7320ac6ad88a77753a87b4babe046352561` |
| `ask_q5_freeze_1h` | q5 | `0x0864bda1c01601975022ef31f6a4a26f9b3ed86e36ed1540411171873ee52ac5` |
| `scan_q5_c0` | SCANNING | `0x6f160ab684e3c23b7d09850ab742dd8171495aa2f996030fe15b781ebd5f3e58` |
| `scan_q5_c1` | ABSENT | `0xac6f2699c882e529eab076d2e882aeb5bb3da297112a91abbee472bdd86e319f` |
| `contest_q5_not_a_mention` | [EXPECTED] NOT_A_MENTION | `0x0c1fe08af759252b68a790ba7572c48ef25290ed99ac0c16abe2047ab6dc73f3` |

```bash
genlayer network set studionet
genlayer call 0x168295C86AB1b2b4D3F8662002B5FBA5F8415ff9 get_question --args q1
genlayer call 0x168295C86AB1b2b4D3F8662002B5FBA5F8415ff9 get_chunk --args D1 0
genlayer call 0x914F992fcee59948c7B9A69Df40985ae5EBcB934 register
genlayer call 0x06A5a43F433E04aDCa60995d359b7F562EF4DBD7 status
```

## Honest limitations

1. A mention is guaranteed to be inside one chunk only if it fits in 800
   characters. A "clause" assembled from sentences far apart is not
   guaranteed to be seen.
2. ABSENT means every chunk was scanned and no validator found it, and nobody
   contested it in time. The window is the defence against a false negative
   every validator shares; choose it to match what is at stake.
3. Sweep reads text. It says nothing about what a deployed token contract
   actually does.
4. 48,000 characters (30 chunks) per document, 300-character targets and
   quotes, 50 questions per document, windows up to 7 days.

## Tests

```bash
python -m unittest discover -s tests     # 25 tests, offline, no model, no chain
```

Covers the chunking proven exhaustively (every start position, fourteen
lengths from 1 to 48,000: full coverage, every 800-character passage inside
one chunk, no wasted chunk), every input rejection, the seal, both reply
rules, the agreement rule (bit mismatch, invented quote, irrelevant quote),
the verdict clock, the prompt fence, PRESENT ending a scan, ABSENT only after
full coverage (a brute force over every order of every subset of chunks),
contests (fabricated quotes cost no model call), model errors and validator
disagreement storing nothing, both consumers against a real Sweep instance,
and six mutations (early ABSENT, trusting the quote, a bit-only validator, no
chunk overlap, a rephrased red flag, paying the owner).

## Layout

```
contracts/sweep.py      the primitive: sealed documents, questions, scans, contests
contracts/listing.py    consumer: lists only when every red flag is provably absent
contracts/bounty.py     consumer: pays whoever finds the mention
tests/test_sweep.py     the suite
tools/                  report.mjs (decode every demo receipt), verify.mjs (deployed code = these files)
docs/                   DESIGN.md, INTEGRATING.md
```

## Licence

MIT, see [LICENSE](LICENSE).
