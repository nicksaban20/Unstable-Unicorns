"""Heuristic evaluation functions for Unstable Unicorns."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.game_state import GameState


def evaluate_state(state: 'GameState', player_idx: int) -> float:
    """Evaluate a game state from a player's perspective.

    Returns a value between 0 and 1, where:
    - 1.0 = player has won
    - 0.0 = player has lost
    - 0.5 = neutral position

    Args:
        state: Current game state
        player_idx: Index of the player to evaluate for

    Returns:
        Evaluation score between 0 and 1
    """
    # Check terminal states
    if state.winner == player_idx:
        return 1.0
    elif state.winner is not None:
        return 0.0

    player = state.players[player_idx]
    target = state.unicorns_to_win

    # === Primary factor: Progress toward winning ===
    unicorn_count = player.unicorn_count()
    progress = unicorn_count / target

    # === Threat assessment ===
    other_max = 0
    for p in state.players:
        if p.player_idx != player_idx:
            count = p.unicorn_count()
            if count > other_max:
                other_max = count

    threat = other_max / target

    # === Hand quality ===
    hand_value = 0.0
    for card in player.hand:
        if card.is_unicorn():
            hand_value += 0.15
        elif card.card_type.name == "INSTANT":
            hand_value += 0.08
        elif card.card_type.name == "MAGIC":
            hand_value += 0.05
        else:
            hand_value += 0.03

    hand_value = min(hand_value, 0.15)  # Cap contribution

    # === Stable quality ===
    upgrade_value = len(player.upgrades) * 0.03
    downgrade_penalty = len(player.downgrades) * 0.04

    # === Special card bonuses ===
    special_bonus = 0.0
    for card in player.stable + player.upgrades:
        effect_id = card.card.effect_id
        if effect_id == "yay":
            special_bonus += 0.05
        elif effect_id == "rainbow_aura":
            special_bonus += 0.06
        elif effect_id == "ginormous_unicorn":
            special_bonus += 0.03
        elif effect_id == "magical_kittencorn":
            special_bonus += 0.04

    # === Combine factors ===
    # Progress is the most important (70%)
    # Threat matters (15%)
    # Other factors (15%)
    score = (
        progress * 0.70 +
        (1 - threat) * 0.15 +
        hand_value +
        upgrade_value -
        downgrade_penalty +
        special_bonus
    )

    # Clamp to [0, 1]
    return max(0.0, min(1.0, score))


def evaluate_card_value(state: 'GameState', card, player_idx: int) -> float:
    """Evaluate the value of playing a specific card.

    Args:
        state: Current game state
        card: Card to evaluate
        player_idx: Player who would play the card

    Returns:
        Value score for playing this card
    """
    from cards.card import CardType

    player = state.players[player_idx]
    score = 0.0

    # Base value by type
    type_values = {
        CardType.BABY_UNICORN: 3.0,
        CardType.BASIC_UNICORN: 4.0,
        CardType.MAGICAL_UNICORN: 5.0,
        CardType.UPGRADE: 3.5,
        CardType.DOWNGRADE: 2.5,
        CardType.MAGIC: 2.0,
        CardType.INSTANT: 1.0,  # Instants are reactive
    }
    score += type_values.get(card.card_type, 1.0)

    # Unicorns more valuable when close to winning
    if card.is_unicorn():
        unicorns_needed = state.unicorns_to_win - player.unicorn_count()
        if unicorns_needed <= 2:
            score += 3.0
        elif unicorns_needed <= 3:
            score += 1.5

    # Special card bonuses
    effect_id = card.card.effect_id
    if effect_id:
        high_value_effects = [
            "yay", "rainbow_aura", "ginormous_unicorn",
            "magical_kittencorn", "unicorn_phoenix"
        ]
        if effect_id in high_value_effects:
            score += 2.0

        # Draw effects are good
        draw_effects = ["greedy_flying_unicorn", "unicorn_on_the_cob", "good_deal"]
        if effect_id in draw_effects:
            score += 1.0

        # Destruction effects value depends on game state
        destruction_effects = ["unicorn_poison", "two_for_one", "chainsaw_unicorn"]
        if effect_id in destruction_effects:
            # More valuable if opponent is ahead
            other_max = max(p.unicorn_count() for p in state.players if p.player_idx != player_idx)
            if other_max >= player.unicorn_count():
                score += 2.0

    return score


def should_neigh(state: 'GameState', player_idx: int) -> float:
    """Evaluate whether to use a Neigh card.

    Returns a value where:
    - >1.0 = strongly recommend Neighing
    - 0.5-1.0 = moderate recommendation
    - <0.5 = recommend passing

    Args:
        state: Current game state
        player_idx: Player considering the Neigh

    Returns:
        Recommendation score
    """
    from cards.card import CardType

    player = state.players[player_idx]
    card_being_played = state.card_being_played

    if not card_being_played:
        return 0.0

    # Count our Neigh cards
    neigh_count = sum(1 for c in player.hand if c.card_type == CardType.INSTANT)

    # Base value of Neighing
    score = 0.5

    # Check who played the card
    for p in state.players:
        if p.player_idx == player_idx:
            continue

        # If opponent is close to winning and plays a unicorn
        if p.unicorn_count() >= state.unicorns_to_win - 1:
            if card_being_played.is_unicorn():
                score += 5.0  # Critical!
            else:
                score += 1.0

    # Value of the card being played
    if card_being_played.is_unicorn():
        score += 1.0
        if card_being_played.card_type == CardType.MAGICAL_UNICORN:
            score += 0.5

    # Conservation factor - save Neighs if we have few
    if neigh_count <= 1:
        score -= 0.5
    elif neigh_count >= 3:
        score += 0.3

    # Consider special cards
    if card_being_played.card.effect_id:
        dangerous_effects = [
            "seductive_unicorn",  # Steals unicorns
            "two_for_one",        # Mass destruction
            "blatant_thievery",   # Steals from hand
            "rainbow_lasso",      # Steals unicorn
        ]
        if card_being_played.card.effect_id in dangerous_effects:
            score += 1.5

    return score
