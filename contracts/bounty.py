# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Bounty: pay whoever finds it, or give it back once it is provably not there.

It holds no model. It is bound to one Sweep question. A sponsor funds it.
Anyone may then scan chunks or contest an ABSENT, and the account whose
transaction produced the verified mention is paid. That makes the exhaustive
scan self-funding: the reward goes to whoever does the reading that matters.

If the verdict becomes final ABSENT, the sponsor gets the money back. The
document's own owner is never paid for finding something in its own
document; in that case the money also returns to the sponsor.

On Bradbury a payable write that reverts keeps its value, so a refused fund
credits the value back to the sender instead of reverting.
"""

import json
import typing
from genlayer import *

ERROR_EXPECTED = "[EXPECTED]"
REFUSED = "[REFUSED]"
_HEX = set("0123456789abcdef")


def address_text(value: typing.Any) -> str:
    text = value if isinstance(value, str) else str(value)
    ok = len(text) == 42 and text[:2] == "0x" and set(text[2:].lower()) <= _HEX
    return text.lower() if ok else ""


def payee_of(question: dict, owner: str, sponsor: str) -> tuple:
    """(who is paid, why) once the question is resolved, or ("", "") if not yet."""
    if question["verdict"] == "PRESENT":
        finder = address_text(question["found_by"])
        if finder == address_text(owner):
            return sponsor, "OWNER_FOUND"
        return finder, "FOUND"
    if question["verdict"] == "ABSENT_FINAL":
        return sponsor, "ABSENT"
    return "", ""


def _fail(code: str) -> typing.NoReturn:
    raise gl.vm.UserError(ERROR_EXPECTED + " " + code)


@gl.evm.contract_interface
class _Recipient:
    class View:
        pass

    class Write:
        pass


class Bounty(gl.Contract):
    sweep: Address
    question_id: str
    sponsor: str
    owner: str
    amount: u256
    state: str
    outcome: str
    credits: TreeMap[str, u256]

    def __init__(self, sweep: typing.Any, question_id: str) -> None:
        self.sweep = sweep if isinstance(sweep, Address) else Address(str(sweep))
        self.question_id = str(question_id)
        view = gl.get_contract_at(self.sweep).view()
        q = json.loads(view.get_question(self.question_id))
        if q["status"] != "SCANNING":
            _fail("ALREADY_RESOLVED")
        self.owner = address_text(json.loads(view.get_document(q["doc"]))["owner"])
        self.sponsor = address_text(gl.message.sender_address)
        self.amount = u256(0)
        self.state = "OPEN"
        self.outcome = ""

    @gl.public.write.payable
    def fund(self) -> str:
        paid = int(gl.message.value)
        if paid == 0:
            _fail("NOTHING_SENT")
        who = address_text(gl.message.sender_address)
        if who != str(self.sponsor):
            self._credit(who, paid)
            return REFUSED + " NOT_SPONSOR"
        if str(self.state) != "OPEN":
            self._credit(who, paid)
            return REFUSED + " SETTLED"
        self.amount = u256(int(self.amount) + paid)
        return "FUNDED " + str(int(self.amount))

    @gl.public.write
    def settle(self) -> str:
        if str(self.state) != "OPEN":
            _fail("ALREADY_SETTLED")
        if int(self.amount) == 0:
            _fail("NOT_FUNDED")
        q = json.loads(gl.get_contract_at(self.sweep).view().get_question(self.question_id))
        payee, why = payee_of(q, str(self.owner), str(self.sponsor))
        if not payee:
            _fail("NOT_RESOLVED")
        self._credit(payee, int(self.amount))
        self.state = "SETTLED"
        self.outcome = json.dumps({"paid": payee, "why": why, "amount": str(int(self.amount))}, sort_keys=True)
        return why

    @gl.public.write
    def withdraw(self) -> None:
        who = address_text(gl.message.sender_address)
        amount = int(self.credits[who]) if who in self.credits else 0
        if amount == 0:
            _fail("NOTHING_TO_WITHDRAW")
        self.credits[who] = u256(0)
        _Recipient(gl.message.sender_address).emit_transfer(value=u256(amount))

    @gl.public.view
    def credit_of(self, who: typing.Any) -> str:
        key = address_text(who)
        return str(int(self.credits[key]) if key in self.credits else 0)

    @gl.public.view
    def status(self) -> str:
        return json.dumps({"question_id": str(self.question_id), "sponsor": str(self.sponsor),
                           "owner": str(self.owner), "amount": str(int(self.amount)),
                           "state": str(self.state),
                           "outcome": json.loads(str(self.outcome)) if str(self.outcome) else {}},
                          sort_keys=True)

    def _credit(self, who: str, amount: int) -> None:
        held = int(self.credits[who]) if who in self.credits else 0
        self.credits[who] = u256(held + amount)
