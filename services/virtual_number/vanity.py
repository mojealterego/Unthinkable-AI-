"""All Virtual Phone: on-net alias design and vanity ranking, no PSTN spoofing.

Source basis: GOWM-X/All Virtual Phone reference PDFs supplied by project owner.
Source regex and entropy ideas are adapted, not used as verified number inventory.
"""
from __future__ import annotations

from collections import Counter
import math
import re
import secrets
from dataclasses import asdict, dataclass
from typing import Literal

Style = Literal["random", "repeated", "pairs", "sequence"]
_STYLES = frozenset({"random", "repeated", "pairs", "sequence"})
_SEPARATORS = re.compile(r"[\s\-().]")


@dataclass(frozen=True)
class AliasProposal:
    identifier: str
    tier: str
    score: int
    entropy_bits_per_digit: float
    scope: str = "on_net_only"
    availability: str = "not_checked"
    publicly_routable: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def digits_only(raw: str) -> str:
    """Do not silently interpret punctuation, URLs or international '+' as an on-net ID."""
    if not isinstance(raw, str):
        raise ValueError("Alias must be a string")
    clean = _SEPARATORS.sub("", raw)
    if not re.fullmatch(r"[0-9]{3,18}", clean, re.ASCII):
        raise ValueError("Internal alias must contain 3..18 ASCII digits")
    return clean


def e164_syntax(raw: str) -> bool:
    """Format check ONLY. A valid E.164 shape is never proof of DID allocation."""
    return bool(isinstance(raw, str) and re.fullmatch(r"\+[1-9][0-9]{2,14}", raw, re.ASCII))


def _longest_equal_run(seq: str) -> int:
    longest = current = 1
    for a, b in zip(seq, seq[1:]):
        current = current + 1 if a == b else 1
        longest = max(longest, current)
    return longest


def _longest_step_run(seq: str) -> int:
    """Consecutive strictly rising OR strictly falling digits (no zigzags)."""
    longest = current = 1
    direction = 0
    for a, b in zip(seq, seq[1:]):
        step = int(b) - int(a)
        if abs(step) == 1 and (direction == 0 or step == direction):
            current += 1
        elif abs(step) == 1:
            current = 2
        else:
            current = 1
        direction = step if abs(step) == 1 else 0
        longest = max(longest, current)
    return longest


def classify_alias(raw: str) -> AliasProposal:
    digits = digits_only(raw)
    n = len(digits)
    counts = Counter(digits)
    entropy = -sum((qty / n) * math.log2(qty / n) for qty in counts.values())
    run = _longest_equal_run(digits)
    steps = _longest_step_run(digits)
    two_block = n >= 6 and any(digits[i:i + 2] == digits[i + 2:i + 4] ==
                                   digits[i + 4:i + 6] for i in range(n - 5))
    three_block = n >= 9 and any(digits[i:i + 3] == digits[i + 3:i + 6] ==
                                     digits[i + 6:i + 9] for i in range(n - 8))
    if run >= 6 or steps >= 6:
        tier, score = "PLATINUM", 100
    elif run >= 4 or two_block or three_block or steps >= 4:
        tier, score = "GOLD", 80
    elif len(counts) <= 3:
        tier, score = "SILVER", 50
    else:
        tier, score = "STANDARD", min(40, max(0, int(35 - 8 * entropy)))
    return AliasProposal(
        identifier=digits, tier=tier, score=score,
        entropy_bits_per_digit=round(entropy, 5),
    )


def _candidate(prefix: str, length: int, style: Style, position: int) -> str:
    remaining = length - len(prefix)
    if style == "random":
        return prefix + "".join(str(secrets.randbelow(10)) for _ in range(remaining))
    if style == "repeated":
        digit = prefix[-1] if prefix else str(position % 10)
        # Rotate digits for uniqueness while keeping a visibly repetitive suffix.
        repeat = min(remaining, max(4, remaining - 1))
        return prefix + digit * repeat + "".join(
            str((position + j) % 10) for j in range(remaining - repeat)
        )
    if style == "pairs":
        a, b = str(position % 10), str((position // 10 + 3) % 10)
        block = a + b
        return prefix + (block * (remaining // 2 + 1))[:remaining]
    if style == "sequence":
        return prefix + "".join(str((position + j) % 10) for j in range(remaining))
    raise ValueError("Unsupported suggestion style")


def suggest_internal_aliases(*, prefix: str = "", length: int = 9,
                             style: str = "repeated", count: int = 10) -> list[AliasProposal]:
    if not isinstance(prefix, str) or not re.fullmatch(r"[0-9]{0,15}", prefix, re.ASCII):
        raise ValueError("Prefix must contain 0..15 ASCII digits")
    if not isinstance(length, int) or isinstance(length, bool) or not 4 <= length <= 18:
        raise ValueError("Alias length must be 4..18")
    if length <= len(prefix):
        raise ValueError("Alias length must exceed prefix length")
    if style not in _STYLES:
        raise ValueError("Unknown alias style")
    if not isinstance(count, int) or isinstance(count, bool) or not 1 <= count <= 30:
        raise ValueError("Count must be 1..30")
    if style == "repeated" and length - len(prefix) < 2:
        raise ValueError("Repeated style needs at least two suffix digits")
    if style == "random" and length - len(prefix) < 3 and count > 10 ** (length - len(prefix)):
        raise ValueError("Not enough combinations for unique random aliases")
    proposals: dict[str, AliasProposal] = {}
    attempts = 0
    while len(proposals) < count and attempts < 300:
        pos = attempts if style != "random" else secrets.randbelow(10 ** min(6, length - len(prefix)))
        candidate = _candidate(prefix, length, style, pos)
        if candidate not in proposals:
            proposals[candidate] = classify_alias(candidate)
        attempts += 1
    if len(proposals) < count:
        raise ValueError("Pattern has insufficient distinct candidates; change length or prefix")
    return sorted(proposals.values(), key=lambda x: (-x.score, x.identifier))


def filter_verified_carrier_inventory(records: list[dict]) -> list[dict]:
    """Carrier response filtering, not a remote lookup/provisioning adapter.

    Only entries verified by an actual provider for an authenticated account
    qualify for a prospective DID purchase. Returned status is STILL not
    a reservation and must be rechecked atomically when ordering.
    """
    approved = []
    for item in records:
        did = item.get("e164", "")
        if (e164_syntax(did) and item.get("available") is True and
                item.get("verified_provider") is True and
                isinstance(item.get("provider_reference"), str) and
                len(item["provider_reference"].strip()) >= 3):
            approved.append(item.copy())
    return approved
