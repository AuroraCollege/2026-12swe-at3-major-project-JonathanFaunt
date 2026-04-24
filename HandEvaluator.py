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



def evaluate_hand(hand):
    ranks = [card.rank for card in hand]
    suits = [card.suit for card in hand]
    values = convert_ranks_to_values(ranks)

    # Royal Flush
    is_rf, rf_val = is_royal_flush(values, suits)
    if is_rf:
        return (HAND_RANKS["royal_flush"], rf_val)

    # Straight Flush
    is_sf, sf_val = is_straight_flush(values, suits)
    if is_sf:
        return (HAND_RANKS["straight_flush"], sf_val)

    # Four of a Kind
    is_4k, fk_val = is_four_of_a_kind(values)
    if is_4k:
        return (HAND_RANKS["four_of_a_kind"], fk_val)

    # Full House
    is_fh, fh_val = is_full_house(values)
    if is_fh:
        return (HAND_RANKS["full_house"], fh_val)

    # Flush
    is_f, f_val = is_flush(suits, values)
    if is_f:
        return (HAND_RANKS["flush"], f_val)

    # Straight
    is_s, s_val = is_straight(values)
    if is_s:
        return (HAND_RANKS["straight"], s_val)

    # Three of a Kind
    is_3k, tk_val = is_three_of_a_kind(values)
    if is_3k:
        return (HAND_RANKS["three_of_a_kind"], tk_val)

    # Two Pair
    is_tp, tp_val = is_two_pair(values)
    if is_tp:
        return (HAND_RANKS["two_pair"], tp_val)

    # One Pair
    is_op, op_val = is_one_pair(values)
    if is_op:
        return (HAND_RANKS["one_pair"], op_val)

    # High Card
    return (HAND_RANKS["high_card"], sorted(values, reverse=True))

def format_hand(rank, tiebreakers):
    name = RANK_NAMES[rank]

    # Royal Flush
    if rank == 9:
        return "Royal Flush"

    # Straight / Straight Flush
    if rank in (4, 8):
        high = VALUE_TO_NAME[tiebreakers]
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

def convert_ranks_to_values(ranks):
    RANK_VALUE = {
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "10": 10,
        "Jack": 11,
        "Queen": 12,
        "King": 13,
        "Ace": 14
    }

    values = [RANK_VALUE[rank] for rank in ranks]
    return values

def is_royal_flush(values, suits):
    # Values must be exactly {10, 11, 12, 13, 14}
    if set(values) == {10, 11, 12, 13, 14} and len(set(suits)) == 1:
        return True, 14  # Ace high
    return False, None

def is_straight_flush(values, suits):
    straight, high = is_straight(values)
    flush, _ = is_flush(suits, values)

    if straight and flush:
        return True, high

    return False, None

def is_four_of_a_kind(values):
    counts = {v: values.count(v) for v in set(values)}
    quads = [v for v, c in counts.items() if c == 4]

    if len(quads) == 1:
        quad_value = quads[0]
        kicker = [v for v in values if v != quad_value][0]
        return True, [quad_value, kicker]

    return False, None

def is_full_house(values):
    counts = {v: values.count(v) for v in set(values)}

    trips = [v for v, c in counts.items() if c == 3]
    pairs = [v for v, c in counts.items() if c == 2]

    if len(trips) == 1 and len(pairs) == 1:
        return True, [trips[0], pairs[0]]

    return False, None

def is_flush(suits, values):
    # If all suits are the same, set(suits) has length 1
    if len(set(suits)) == 1:
        return True, sorted(values, reverse=True)
    return False, None

def is_straight(values):
    sorted_vals = sorted(values)

    # Ace-low straight: [2, 3, 4, 5, 14]
    if sorted_vals == [2, 3, 4, 5, 14]:
        return True, 5  # treat as straight to the 5

    # Normal straight: values form a sequence like [6, 7, 8, 9, 10]
    start = sorted_vals[0]
    if sorted_vals == list(range(start, start + 5)):
        return True, sorted_vals[-1]  # highest card

    return False, None

def is_three_of_a_kind(values):
    counts = {v: values.count(v) for v in set(values)}
    trips = [v for v, c in counts.items() if c == 3]

    if len(trips) == 1:
        trip_value = trips[0]
        kickers = sorted([v for v in values if v != trip_value], reverse=True)
        return True, [trip_value] + kickers

    return False, None

def is_two_pair(values):
    counts = {v: values.count(v) for v in set(values)}
    pairs = [v for v, c in counts.items() if c == 2]

    if len(pairs) == 2:
        # Sort pairs so highest pair comes first
        high_pair, low_pair = sorted(pairs, reverse=True)
        # The kicker is the remaining card
        kicker = [v for v in values if v not in pairs][0]
        return True, [high_pair, low_pair, kicker]

    return False, None

def is_one_pair(values):
    # Build a dictionary of value → count
    counts = {v: values.count(v) for v in set(values)}

    # Find all values that appear exactly twice
    pairs = [v for v, c in counts.items() if c == 2]

    if len(pairs) == 1:
        pair_value = pairs[0]
        # All other cards are kickers
        kickers = sorted([v for v in values if v != pair_value], reverse=True)
        return True, [pair_value] + kickers

    return False, None

def sort_and_group_cards(hand):
    # Returns a list of groups of Card objects, sorted by:
    #  1. Group size (quads → trips → pairs → singles)
    #  2. Card value (descending)


    # Extract values
    values = [convert_ranks_to_values([card.rank])[0] for card in hand]

    # Count occurrences
    counts = {v: values.count(v) for v in set(values)}

    # Pair each card with its numeric value
    card_value_pairs = [(card, convert_ranks_to_values([card.rank])[0]) for card in hand]

    # Sort cards by:
    #   1. group size (descending)
    #   2. value (descending)
    card_value_pairs.sort(key=lambda x: (counts[x[1]], x[1]), reverse=True)

    # Now group them
    grouped = []
    used = set()

    for card, value in card_value_pairs:
        if value in used:
            continue

        group_size = counts[value]

        # Collect all cards with this value
        group = [c for c, v in card_value_pairs if v == value]

        grouped.append(group)
        used.add(value)

    return grouped
