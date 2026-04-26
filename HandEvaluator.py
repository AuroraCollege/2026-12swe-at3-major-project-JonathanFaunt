from typing import Any, Tuple, List

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
    "royal_flush": 9
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
    9: "Royal Flush"
}

VALUE_TO_NAME = {
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7",
    8: "8",
    9: "9",
    10: "10",
    11: "Jack",
    12: "Queen",
    13: "King",
    14: "Ace"
}

PAYOUT_MULTIPLIERS = {
    9: 250,  # Royal Flush
    8: 50,   # Straight Flush
    7: 25,   # Four of a Kind
    6: 10,   # Full House
    5: 8,    # Flush
    4: 5,    # Straight
    3: 4,    # Three of a Kind
    2: 3,    # Two Pair
    1: 2,    # One Pair
    0: 1     # High Card
}

# ---------------------------------------------------------
#  EVALUATOR — ALWAYS RETURNS (rank: int, tiebreakers: list[int])
# ---------------------------------------------------------

def evaluate_hand(hand: Any) -> Tuple[int, List[int]]:
    ranks = [card.rank for card in hand]
    suits = [card.suit for card in hand]
    values = convert_ranks_to_values(ranks)

    # Royal Flush
    is_rf, rf_val = is_royal_flush(values, suits)
    if is_rf:
        assert rf_val is not None
        return HAND_RANKS["royal_flush"], rf_val

    # Straight Flush
    is_sf, sf_val = is_straight_flush(values, suits)
    if is_sf:
        assert sf_val is not None
        return HAND_RANKS["straight_flush"], sf_val

    # Four of a Kind
    is_4k, fk_val = is_four_of_a_kind(values)
    if is_4k:
        assert fk_val is not None
        return HAND_RANKS["four_of_a_kind"], fk_val

    # Full House
    is_fh, fh_val = is_full_house(values)
    if is_fh:
        assert fh_val is not None
        return HAND_RANKS["full_house"], fh_val

    # Flush
    is_f, f_val = is_flush(suits, values)
    if is_f:
        assert f_val is not None
        return HAND_RANKS["flush"], f_val

    # Straight
    is_s, s_val = is_straight(values)
    if is_s:
        assert s_val is not None
        return HAND_RANKS["straight"], s_val

    # Three of a Kind
    is_3k, tk_val = is_three_of_a_kind(values)
    if is_3k:
        assert tk_val is not None
        return HAND_RANKS["three_of_a_kind"], tk_val

    # Two Pair
    is_tp, tp_val = is_two_pair(values)
    if is_tp:
        assert tp_val is not None
        return HAND_RANKS["two_pair"], tp_val

    # One Pair
    is_op, op_val = is_one_pair(values)
    if is_op:
        assert op_val is not None
        return HAND_RANKS["one_pair"], op_val

    # High Card
    return HAND_RANKS["high_card"], sorted(values, reverse=True)


# ---------------------------------------------------------
#  FORMATTER
# ---------------------------------------------------------

def format_hand(rank: int, tiebreakers: List[int]) -> str:
    name = RANK_NAMES[rank]

    # Royal Flush
    if rank == 9:
        return "Royal Flush"

    # Straight / Straight Flush
    if rank in (4, 8):
        high = VALUE_TO_NAME[tiebreakers[0]]
        return f"{name} (to {high})"

    # Four of a Kind
    if rank == 7:
        quad, kicker = tiebreakers
        return f"{name} ({VALUE_TO_NAME[quad]}s) — Kicker: {VALUE_TO_NAME[kicker]}"

    # Full House
    if rank == 6:
        trip, pair = tiebreakers
        return f"{name} ({VALUE_TO_NAME[trip]}s over {VALUE_TO_NAME[pair]}s)"

    # Flush
    if rank == 5:
        cards = ", ".join(VALUE_TO_NAME[v] for v in tiebreakers)
        return f"{name} — {cards}"

    # Three of a Kind
    if rank == 3:
        trip = tiebreakers[0]
        kickers = ", ".join(VALUE_TO_NAME[v] for v in tiebreakers[1:])
        return f"{name} ({VALUE_TO_NAME[trip]}s) — Kickers: {kickers}"

    # Two Pair
    if rank == 2:
        high, low, kicker = tiebreakers
        return f"{name} ({VALUE_TO_NAME[high]}s and {VALUE_TO_NAME[low]}s) — Kicker: {VALUE_TO_NAME[kicker]}"

    # One Pair
    if rank == 1:
        pair = tiebreakers[0]
        kickers = ", ".join(VALUE_TO_NAME[v] for v in tiebreakers[1:])
        return f"{name} ({VALUE_TO_NAME[pair]}s) — Kickers: {kickers}"

    # High Card
    if rank == 0:
        cards = ", ".join(VALUE_TO_NAME[v] for v in tiebreakers)
        return f"{name} — {cards}"

    return name


# ---------------------------------------------------------
#  HELPERS
# ---------------------------------------------------------

def convert_ranks_to_values(ranks: List[str]) -> List[int]:
    RANK_VALUE = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
        "7": 7, "8": 8, "9": 9, "10": 10,
        "Jack": 11, "Queen": 12, "King": 13, "Ace": 14
    }
    return [RANK_VALUE[r] for r in ranks]

def get_payout_multiplier(rank: int) -> int:
    return PAYOUT_MULTIPLIERS[rank]

# ---------------------------------------------------------
#  HAND TYPE CHECKS — ALWAYS RETURN list[int] OR None
# ---------------------------------------------------------

def is_royal_flush(values: List[int], suits: List[str]) -> Tuple[bool, List[int] | None]:
    if set(values) == {10, 11, 12, 13, 14} and len(set(suits)) == 1:
        return True, [14]
    return False, None


def is_straight_flush(values: List[int], suits: List[str]) -> Tuple[bool, List[int] | None]:
    straight, high = is_straight(values)
    flush, _ = is_flush(suits, values)
    if straight and flush:
        assert high is not None
        return True, high
    return False, None


def is_four_of_a_kind(values: List[int]) -> Tuple[bool, List[int] | None]:
    counts = {v: values.count(v) for v in set(values)}
    quads = [v for v, c in counts.items() if c == 4]
    if len(quads) == 1:
        quad = quads[0]
        kicker = [v for v in values if v != quad][0]
        return True, [quad, kicker]
    return False, None


def is_full_house(values: List[int]) -> Tuple[bool, List[int] | None]:
    counts = {v: values.count(v) for v in set(values)}
    trips = [v for v, c in counts.items() if c == 3]
    pairs = [v for v, c in counts.items() if c == 2]
    if len(trips) == 1 and len(pairs) == 1:
        return True, [trips[0], pairs[0]]
    return False, None


def is_flush(suits: List[str], values: List[int]) -> Tuple[bool, List[int] | None]:
    if len(set(suits)) == 1:
        return True, sorted(values, reverse=True)
    return False, None


def is_straight(values: List[int]) -> Tuple[bool, List[int] | None]:
    sorted_vals = sorted(values)

    # Ace-low straight
    if sorted_vals == [2, 3, 4, 5, 14]:
        return True, [5]

    # Normal straight
    start = sorted_vals[0]
    if sorted_vals == list(range(start, start + 5)):
        return True, [sorted_vals[-1]]

    return False, None


def is_three_of_a_kind(values: List[int]) -> Tuple[bool, List[int] | None]:
    counts = {v: values.count(v) for v in set(values)}
    trips = [v for v, c in counts.items() if c == 3]
    if len(trips) == 1:
        trip = trips[0]
        kickers = sorted([v for v in values if v != trip], reverse=True)
        return True, [trip] + kickers
    return False, None


def is_two_pair(values: List[int]) -> Tuple[bool, List[int] | None]:
    counts = {v: values.count(v) for v in set(values)}
    pairs = [v for v, c in counts.items() if c == 2]
    if len(pairs) == 2:
        high, low = sorted(pairs, reverse=True)
        kicker = [v for v in values if v not in pairs][0]
        return True, [high, low, kicker]
    return False, None


def is_one_pair(values: List[int]) -> Tuple[bool, List[int] | None]:
    counts = {v: values.count(v) for v in set(values)}
    pairs = [v for v, c in counts.items() if c == 2]
    if len(pairs) == 1:
        pair = pairs[0]
        kickers = sorted([v for v in values if v != pair], reverse=True)
        return True, [pair] + kickers
    return False, None


# ---------------------------------------------------------
#  GROUPING
# ---------------------------------------------------------

def sort_and_group_cards(hand: Any) -> List[List[Any]]:
    values = [convert_ranks_to_values([card.rank])[0] for card in hand]
    counts = {v: values.count(v) for v in set(values)}
    card_value_pairs = [(card, convert_ranks_to_values([card.rank])[0]) for card in hand]

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
