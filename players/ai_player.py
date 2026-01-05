"""AI player implementations for Unstable Unicorns."""

import random
from typing import List, TYPE_CHECKING

from players.player import Player

if TYPE_CHECKING:
    from game.game_state import GameState
    from game.action import Action


class RandomPlayer(Player):
    """AI player that makes random legal moves.

    Useful as a baseline and for testing.
    """

    def choose_action(self, state: 'GameState', valid_actions: List['Action']) -> 'Action':
        """Choose a random valid action."""
        return random.choice(valid_actions)

    def choose_target(
        self,
        state: 'GameState',
        valid_targets: List,
        prompt: str
    ) -> object:
        """Choose a random valid target."""
        return random.choice(valid_targets)


class RuleBasedPlayer(Player):
    """AI player that uses heuristic rules to make decisions.

    Prioritizes actions based on game state analysis.
    """

    def choose_action(self, state: 'GameState', valid_actions: List['Action']) -> 'Action':
        """Choose action based on heuristic rules."""
        from game.action import ActionType

        player_idx = state.current_player_idx
        player = state.players[player_idx]

        # Score each action
        scored_actions = []
        for action in valid_actions:
            score = self._score_action(state, action, player_idx)
            scored_actions.append((score, action))

        # Sort by score and pick best
        scored_actions.sort(key=lambda x: x[0], reverse=True)
        return scored_actions[0][1]

    def _score_action(self, state: 'GameState', action: 'Action', player_idx: int) -> float:
        """Score an action based on heuristics."""
        from game.action import ActionType
        from cards.card import CardType

        score = 0.0
        player = state.players[player_idx]

        if action.action_type == ActionType.END_ACTION_PHASE:
            # Ending is neutral, slightly negative
            return -0.1

        if action.action_type == ActionType.DRAW_CARD:
            # Drawing is always good
            return 1.0

        if action.action_type == ActionType.PLAY_CARD:
            card = action.card

            # Playing unicorns is usually good
            if card.is_unicorn():
                score += 5.0

                # Magical unicorns with effects are better
                if card.card_type == CardType.MAGICAL_UNICORN:
                    score += 2.0

                # Extra value if close to winning
                unicorn_count = player.unicorn_count()
                if unicorn_count >= state.unicorns_to_win - 2:
                    score += 3.0

            # Upgrades are good
            if card.card_type == CardType.UPGRADE:
                score += 3.0

                # Yay is great
                if card.card.effect_id == "yay":
                    score += 2.0

                # Rainbow Aura is great
                if card.card.effect_id == "rainbow_aura":
                    score += 2.0

            # Magic cards value depends on effect
            if card.card_type == CardType.MAGIC:
                # Destruction effects are good when opponent is ahead
                other_max = max(p.unicorn_count() for p in state.get_other_players(player_idx))
                if other_max >= player.unicorn_count():
                    if card.card.effect_id in ["unicorn_poison", "two_for_one"]:
                        score += 4.0
                    else:
                        score += 2.0
                else:
                    score += 1.0

            # Downgrades are good to play on leading opponent
            if card.card_type == CardType.DOWNGRADE:
                # Find opponent with most unicorns
                other_max = max(p.unicorn_count() for p in state.get_other_players(player_idx))
                if other_max >= player.unicorn_count():
                    score += 3.0
                else:
                    score += 1.0

        if action.action_type == ActionType.NEIGH:
            # Neigh is valuable when card being played is threatening
            if state.card_being_played:
                card = state.card_being_played
                if card.is_unicorn():
                    # Check if player is close to winning
                    for p in state.players:
                        if p.player_idx != player_idx:
                            if p.unicorn_count() >= state.unicorns_to_win - 1:
                                score += 10.0  # Critical to Neigh!
                                break
                    score += 3.0
                else:
                    score += 1.0

        if action.action_type == ActionType.PASS_NEIGH:
            # Sometimes passing is better to save Neigh cards
            neigh_count = sum(
                1 for c in player.hand
                if c.card_type == CardType.INSTANT
            )
            if neigh_count > 2:
                score -= 0.5  # More likely to use Neigh
            else:
                score += 0.5  # Save Neigh cards

        return score

    def choose_target(
        self,
        state: 'GameState',
        valid_targets: List,
        prompt: str
    ) -> object:
        """Choose target based on heuristics."""
        # For now, pick randomly
        # TODO: Add smarter target selection
        return random.choice(valid_targets)
