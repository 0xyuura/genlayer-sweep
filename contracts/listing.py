# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Listing: a launchpad that lists a project only when its terms are clean.

It holds no model. At deployment it pins its red flags, word for word, and
the shortest contest window it accepts. A project applies with its sealed
terms document and one Sweep question per red flag. The listing reads Sweep:

- any red flag PRESENT: REJECTED, permanently, with the quote that sank it;
- every red flag ABSENT and final: LISTED, permanently;
- anything else: nothing is recorded yet.

A question only counts if its target is exactly a pinned red flag, it is about
the same document, and its window is at least the pinned minimum, so an
applicant cannot rephrase a red flag into something harmless or close the
contest window early.
"""

import json
import typing
from genlayer import *

ERROR_EXPECTED = "[EXPECTED]"
MAX_FLAGS = 5
MAX_TARGET = 300
MAX_WINDOW = 7 * 24 * 3600


def flags_from_input(raw: typing.Any) -> list:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            raise ValueError("FLAGS_NOT_JSON")
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_FLAGS:
        raise ValueError("FLAGS_SHAPE")
    out = []
    for f in raw:
        if not isinstance(f, str) or not f.strip() or len(f) > MAX_TARGET:
            raise ValueError("FLAG_SHAPE")
        if f.strip() in out:
            raise ValueError("FLAG_DUP")
        out.append(f.strip())
    return out


def decide(doc_id: str, flags: list, min_window: int, questions: list) -> dict:
    """questions: Sweep's get_question for each id the applicant named.
    Returns {"decision": LISTED|REJECTED|"", ...} or raises ValueError(code)."""
    if len(questions) != len(flags):
        raise ValueError("ONE_QUESTION_PER_FLAG")
    by_flag = {}
    for q in questions:
        if q["doc"] != doc_id:
            raise ValueError("OTHER_DOCUMENT")
        if q["target"] not in flags:
            raise ValueError("NOT_A_RED_FLAG")
        if q["target"] in by_flag:
            raise ValueError("FLAG_TWICE")
        if q["window"] < min_window:
            raise ValueError("WINDOW_TOO_SHORT")
        by_flag[q["target"]] = q
    for f in flags:
        q = by_flag[f]
        if q["verdict"] == "PRESENT":
            return {"decision": "REJECTED", "flag": f, "quote": q["quote"], "chunk": q["hit_chunk"]}
    if all(by_flag[f]["verdict"] == "ABSENT_FINAL" for f in flags):
        return {"decision": "LISTED"}
    return {"decision": ""}


def _fail(code: str) -> typing.NoReturn:
    raise gl.vm.UserError(ERROR_EXPECTED + " " + code)


class Listing(gl.Contract):
    sweep: Address
    flags: str
    min_window: u256
    decisions: TreeMap[str, str]
    decision_ids: DynArray[str]

    def __init__(self, sweep: typing.Any, red_flags: typing.Any, min_window: typing.Any) -> None:
        self.sweep = sweep if isinstance(sweep, Address) else Address(str(sweep))
        try:
            self.flags = json.dumps(flags_from_input(red_flags))
        except ValueError as err:
            _fail(str(err))
        w = int(str(min_window))
        if not 0 <= w <= MAX_WINDOW:
            _fail("WINDOW_RANGE")
        self.min_window = u256(w)

    @gl.public.write
    def apply(self, doc_id: str, question_ids: typing.Any) -> str:
        did = str(doc_id)
        if did in self.decisions:
            _fail("ALREADY_DECIDED")
        ids = json.loads(question_ids) if isinstance(question_ids, str) else list(question_ids)
        sweep = gl.get_contract_at(self.sweep).view()
        questions = [json.loads(sweep.get_question(str(q))) for q in ids]
        try:
            result = decide(did, json.loads(str(self.flags)), int(self.min_window), questions)
        except ValueError as err:
            _fail(str(err))
        if not result["decision"]:
            _fail("NOT_FINAL")
        self.decisions[did] = json.dumps(dict(result, questions=[str(q) for q in ids]), sort_keys=True)
        self.decision_ids.append(did)
        return result["decision"]

    @gl.public.view
    def decision(self, doc_id: str) -> str:
        did = str(doc_id)
        return str(self.decisions[did]) if did in self.decisions else "{}"

    @gl.public.view
    def is_listed(self, doc_id: str) -> bool:
        did = str(doc_id)
        return did in self.decisions and json.loads(str(self.decisions[did]))["decision"] == "LISTED"

    @gl.public.view
    def register(self) -> str:
        return json.dumps({"red_flags": json.loads(str(self.flags)), "min_window": int(self.min_window),
                           "decisions": {d: json.loads(str(self.decisions[d])) for d in self.decision_ids}},
                          sort_keys=True)
