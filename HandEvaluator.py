from typing import Any, List, Tuple

# ---------------------------------------------------------
#  Dictionaries
# ---------------------------------------------------------

HAND_RANKS = {
    "high_card": 0,
    "one_pair": 1,
    "two_pair": 2,
    "three_of_a_kind": 3,
    "straight": 4,
    "flush": 5,
    "full_house": 6,
    "four_of_a_kind": 7,
    "straight_flush": 8,
    "royal_flush": 9,
    "five_of_a_kind": 10
}

RANK_NAMES = {
    0: "High Card",
    1: "One Pair",
    2: "Two Pair",
    3: "Three of a Kind",
    4: "Straight",
    5: "Flush",
    6: "Full House",
    7: "Four of a Kind",
    8: "Straight Flush",
    9: "Royal Flush",
    10: "Five of a Kind"
}

VALUE_TO_NAME = {
    2: "2", 3: "3", 4: "4", 5: "5", 6: "6",
    7: "7", 8: "8", 9: "9", 10: "10",
    11: "Jack", 12: "Queen", 13: "King", 14: "Ace"
}

PAYOUT_MULTIPLIERS = {
    10: 500,
    9: 250,
    8: 50,
    7: 25,
    6: 10,
    5: 8,
    4: 5,
    3: 4,
    2: 3,
    1: 2,
    0: 1
}

# ---------------------------------------------------------
#  EVALUATOR — ALWAYS RETURNS (rank: int, tiebreakers: list[int])
# ---------------------------------------------------------

def evaluate_hand(hand: Any) -> tuple[int, list[int]]:
    ranks = [card.rank for card in hand]
    suits = [card.suit for card in hand]
    values = convert_ranks_to_values(ranks)

    # Five of a Kind (secret joke hand)
    is_5k, fk5_val = is_five_of_a_kind(values)
    if is_5k:
        return HAND_RANKS["five_of_a_kind"], fk5_val

    # Royal Flush
    is_rf, rf_val = is_royal_flush(values, suits)
    if is_rf:
        return HAND_RANKS["royal_flush"], rf_val

    # Straight Flush
    is_sf, sf_val = is_straight_flush(values, suits)
    if is_sf:
        return HAND_RANKS["straight_flush"], sf_val

    # Four of a Kind
    is_4k, fk_val = is_four_of_a_kind(values)
    if is_4k:
        return HAND_RANKS["four_of_a_kind"], fk_val

    # Full House
    is_fh, fh_val = is_full_house(values)
    if is_fh:
        return HAND_RANKS["full_house"], fh_val

    # Flush
    is_f, f_val = is_flush(suits, values)
    if is_f:
        return HAND_RANKS["flush"], f_val

    # Straight
    is_s, s_val = is_straight(values)
    if is_s:
        return HAND_RANKS["straight"], s_val

    # Three of a Kind
    is_3k, tk_val = is_three_of_a_kind(values)
    if is_3k:
        return HAND_RANKS["three_of_a_kind"], tk_val

    # Two Pair
    is_tp, tp_val = is_two_pair(values)
    if is_tp:
        return HAND_RANKS["two_pair"], tp_val

    # One Pair
    is_op, op_val = is_one_pair(values)
    if is_op:
        return HAND_RANKS["one_pair"], op_val

    # High Card
    return HAND_RANKS["high_card"], sorted(values, reverse=True)


# ---------------------------------------------------------
#  FORMATTER
# ---------------------------------------------------------

def format_hand(rank: int, tiebreakers: list[int]) -> str:
    name = RANK_NAMES[rank]

    if rank == 10:
        return f"Five of a Kind ({VALUE_TO_NAME[tiebreakers[0]]}s)"

    if rank == 9:
        return "Royal Flush"

    if rank in (4, 8):  # Straight / Straight Flush
        high = VALUE_TO_NAME[tiebreakers[0]]
        return f"{name} (to {high})"

    if rank == 7:  # Four of a Kind
        quad, kicker = tiebreakers
        return f"{name} ({VALUE_TO_NAME[quad]}s) — Kicker: {VALUE_TO_NAME[kicker]}"

    if rank == 6:  # Full House
        trip, pair = tiebreakers
        return f"{name} ({VALUE_TO_NAME[trip]}s over {VALUE_TO_NAME[pair]}s)"

    if rank == 5:  # Flush
        cards = ", ".join(VALUE_TO_NAME[v] for v in tiebreakers)
        return f"{name} — {cards}"

    if rank == 3:  # Trips
        trip = tiebreakers[0]
        kickers = ", ".join(VALUE_TO_NAME[v] for v in tiebreakers[1:])
        return f"{name} ({VALUE_TO_NAME[trip]}s) — Kickers: {kickers}"

    if rank == 2:  # Two Pair
        high, low, kicker = tiebreakers
        return f"{name} ({VALUE_TO_NAME[high]}s and {VALUE_TO_NAME[low]}s) — Kicker: {VALUE_TO_NAME[kicker]}"

    if rank == 1:  # One Pair
        pair = tiebreakers[0]
        kickers = ", ".join(VALUE_TO_NAME[v] for v in tiebreakers[1:])
        return f"{name} ({VALUE_TO_NAME[pair]}s) — Kickers: {kickers}"

    if rank == 0:  # High Card
        cards = ", ".join(VALUE_TO_NAME[v] for v in tiebreakers)
        return f"{name} — {cards}"

    return name


# ---------------------------------------------------------
#  HELPERS
# ---------------------------------------------------------

def convert_ranks_to_values(ranks: list[str]) -> list[int]:
    RANK_VALUE = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
        "7": 7, "8": 8, "9": 9, "10": 10,
        "Jack": 11, "Queen": 12, "King": 13, "Ace": 14
    }
    return [RANK_VALUE[r] for r in ranks]

def get_payout_multiplier(rank: int) -> int:
    return PAYOUT_MULTIPLIERS[rank]


# ---------------------------------------------------------
#  HAND TYPE CHECKS — ALWAYS RETURN list[int]
# ---------------------------------------------------------

def is_five_of_a_kind(values: list[int]) -> tuple[bool, list[int]]:
    if len(set(values)) == 1:
        return True, [values[0]]
    return False, []


def is_royal_flush(values: list[int], suits: list[str]) -> tuple[bool, list[int]]:
    if set(values) == {10, 11, 12, 13, 14} and len(set(suits)) == 1:
        return True, [14]
    return False, []


def is_straight_flush(values: list[int], suits: list[str]) -> tuple[bool, list[int]]:
    straight, high = is_straight(values)
    flush, _ = is_flush(suits, values)
    if straight and flush:
        return True, high
    return False, []


def is_four_of_a_kind(values: list[int]) -> tuple[bool, list[int]]:
    counts = {v: values.count(v) for v in set(values)}
    quads = [v for v, c in counts.items() if c == 4]
    if quads:
        quad = quads[0]
        kicker = [v for v in values if v != quad][0]
        return True, [quad, kicker]
    return False, []


def is_full_house(values: list[int]) -> tuple[bool, list[int]]:
    counts = {v: values.count(v) for v in set(values)}
    trips = [v for v, c in counts.items() if c == 3]
    pairs = [v for v, c in counts.items() if c == 2]
    if trips and pairs:
        return True, [trips[0], pairs[0]]
    return False, []


def is_flush(suits: list[str], values: list[int]) -> tuple[bool, list[int]]:
    if len(set(suits)) == 1:
        return True, sorted(values, reverse=True)
    return False, []


def is_straight(values: list[int]) -> tuple[bool, list[int]]:
    sorted_vals = sorted(values)

    # Ace-low straight
    if sorted_vals == [2, 3, 4, 5, 14]:
        return True, [5]

    # Normal straight
    if all(sorted_vals[i] + 1 == sorted_vals[i+1] for i in range(4)):
        return True, [sorted_vals[-1]]

    return False, []


def is_three_of_a_kind(values: list[int]) -> tuple[bool, list[int]]:
    counts = {v: values.count(v) for v in set(values)}
    trips = [v for v, c in counts.items() if c == 3]
    if trips:
        trip = trips[0]
        kickers = sorted([v for v in values if v != trip], reverse=True)
        return True, [trip] + kickers
    return False, []


def is_two_pair(values: list[int]) -> tuple[bool, list[int]]:
    counts = {v: values.count(v) for v in set(values)}
    pairs = sorted([v for v, c in counts.items() if c == 2], reverse=True)
    if len(pairs) == 2:
        kicker = [v for v in values if v not in pairs][0]
        return True, [pairs[0], pairs[1], kicker]
    return False, []


def is_one_pair(values: list[int]) -> tuple[bool, list[int]]:
    counts = {v: values.count(v) for v in set(values)}
    pairs = [v for v, c in counts.items() if c == 2]
    if pairs:
        pair = pairs[0]
        kickers = sorted([v for v in values if v != pair], reverse=True)
        return True, [pair] + kickers
    return False, []


# ---------------------------------------------------------
#  GROUPING FOR UI
# ---------------------------------------------------------

def sort_and_group_cards(hand: Any) -> list[list[Any]]:
    values = [convert_ranks_to_values([card.rank])[0] for card in hand]
    counts = {v: values.count(v) for v in set(values)}

    card_value_pairs = [(card, convert_ranks_to_values([card.rank])[0]) for card in hand]

    # Sort by group size first, then by value
    card_value_pairs.sort(key=lambda x: (counts[x[1]], x[1]), reverse=True)

    grouped = []
    used = set()

    for card, value in card_value_pairs:
        if value in used:
            continue
        group = [c for c, v in card_value_pairs if v == value]
        grouped.append(group)
        used.add(value)

    return grouped
