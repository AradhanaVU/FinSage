from typing import Iterable, List, Tuple


def signed_amount(amount: float, transaction_type: str) -> float:
    """Store expenses as negative cash flows and income as positive."""
    magnitude = abs(float(amount))
    if transaction_type == "expense":
        return -magnitude
    return magnitude


def largest_remainder_percents(values: Iterable[float], decimals: int = 2) -> List[float]:
    """
    Allocate percentages that sum exactly to 100 (or 0 if the total is 0)
    using the largest-remainder method.
    """
    amounts: List[float] = [float(v) for v in values]
    total = sum(amounts)
    if total <= 0 or not amounts:
        return [0.0] * len(amounts)

    scale = 10 ** decimals
    target = 100 * scale
    exact = [a / total * target for a in amounts]
    floors = [int(x) for x in exact]
    leftover = int(round(target - sum(floors)))
    remainders: List[Tuple[float, int]] = sorted(
        ((exact[i] - floors[i], i) for i in range(len(floors))),
        reverse=True,
    )
    for _, idx in remainders[: max(0, leftover)]:
        floors[idx] += 1
    return [f / scale for f in floors]
