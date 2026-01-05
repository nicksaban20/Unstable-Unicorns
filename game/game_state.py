"""Game state representation for Unstable Unicorns."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Any
from copy import deepcopy
import random

from cards.card import CardInstance, CardType


class GamePhase(Enum):
    """Phases within a turn."""
    BEGINNING = auto()  # Beginning of turn effects
    DRAW = auto()       # Draw phase
    ACTION = auto()     # Action phase (play cards)
    DISCARD_TO_LIMIT = auto() # Discard down to 7
    END = auto()        # End of turn effects
    GAME_OVER = auto()  # Game has ended


@dataclass
class PlayerState:
    """State of a single player."""
    player_idx: int
    name: str

    # Cards
    hand: List[CardInstance] = field(default_factory=list)
    stable: List[CardInstance] = field(default_factory=list)  # Unicorns
    upgrades: List[CardInstance] = field(default_factory=list)
    downgrades: List[CardInstance] = field(default_factory=list)

    # Flags for special effects
    hand_visible: bool = False  # Nanny Cam, Classy Narwhal
    cannot_play_upgrades: bool = False  # Broken Stable
    cannot_play_instants: bool = False  # Slowdown
    cards_cannot_be_neighd: bool = False  # Yay
    unicorns_cannot_be_destroyed: bool = False  # Rainbow Aura
    unicorns_are_basic: bool = False  # Blinding Light
    unicorns_are_pandas: bool = False  # Pandamonium

    def unicorn_count(self) -> int:
        """Count unicorns in stable (considering Ginormous Unicorn)."""
        count = 0
        for card in self.stable:
            if card.card.effect_id == "ginormous_unicorn":
                count += 2
            else:
                count += 1
        return count

    def get_all_stable_cards(self) -> List[CardInstance]:
        """Get all cards in stable (unicorns + upgrades + downgrades)."""
        return self.stable + self.upgrades + self.downgrades

    def has_downgrade(self) -> bool:
        """Check if player has any downgrade cards."""
        return len(self.downgrades) > 0

    def has_baby_unicorn(self) -> bool:
        """Check if player has a baby unicorn in stable."""
        return any(c.card_type == CardType.BABY_UNICORN for c in self.stable)

    def copy(self) -> 'PlayerState':
        """Create a deep copy of this player state."""
        return PlayerState(
            player_idx=self.player_idx,
            name=self.name,
            hand=list(self.hand),
            stable=list(self.stable),
            upgrades=list(self.upgrades),
            downgrades=list(self.downgrades),
            hand_visible=self.hand_visible,
            cannot_play_upgrades=self.cannot_play_upgrades,
            cannot_play_instants=self.cannot_play_instants,
            cards_cannot_be_neighd=self.cards_cannot_be_neighd,
            unicorns_cannot_be_destroyed=self.unicorns_cannot_be_destroyed,
            unicorns_are_basic=self.unicorns_are_basic,
            unicorns_are_pandas=self.unicorns_are_pandas,
        )


@dataclass
class GameState:
    """Complete state of the game.

    This class is designed to be immutable-ish for MCTS simulation.
    Use copy() to create a mutable copy for simulations.
    """
    # Players
    players: List[PlayerState] = field(default_factory=list)
    num_players: int = 2

    # Card piles
    draw_pile: List[CardInstance] = field(default_factory=list)
    discard_pile: List[CardInstance] = field(default_factory=list)
    nursery: List[CardInstance] = field(default_factory=list)

    # Turn tracking
    current_player_idx: int = 0
    phase: GamePhase = GamePhase.BEGINNING
    turn_number: int = 1
    actions_remaining: int = 1  # Cards that can be played this turn

    # Win condition (adjusted by player count)
    unicorns_to_win: int = 7

    # Game over state
    winner: Optional[int] = None

    # Effect tracking
    resolution_stack: List['EffectTask'] = field(default_factory=list)  # Stack of effects/actions to resolve

    # Neigh chain tracking
    card_being_played: Optional[CardInstance] = None
    neigh_chain_active: bool = False
    players_passed_on_neigh: Set[int] = field(default_factory=set)

    def __post_init__(self):
        """Set unicorns to win based on player count."""
        if self.num_players <= 2:
            self.unicorns_to_win = 7
        elif self.num_players <= 5:
            self.unicorns_to_win = 7
        elif self.num_players >= 6:
            self.unicorns_to_win = 6

    @property
    def current_player(self) -> PlayerState:
        """Get the current player."""
        return self.players[self.current_player_idx]

    def get_player(self, player_idx: int) -> PlayerState:
        """Get a player by index."""
        return self.players[player_idx]

    def is_game_over(self) -> bool:
        """Check if the game has ended."""
        return self.winner is not None or self.phase == GamePhase.GAME_OVER

    def check_win_condition(self) -> Optional[int]:
        """Check if any player has won. Returns winner index or None."""
        for player in self.players:
            # Pandamonium makes unicorns not count as unicorns
            if player.unicorns_are_pandas:
                continue
            if player.unicorn_count() >= self.unicorns_to_win:
                return player.player_idx
        return None

    def get_other_players(self, player_idx: int) -> List[PlayerState]:
        """Get all players except the specified one."""
        return [p for p in self.players if p.player_idx != player_idx]

    def get_next_player_idx(self) -> int:
        """Get the index of the next player."""
        return (self.current_player_idx + 1) % self.num_players

    def draw_card(self, player_idx: int, count: int = 1) -> List[CardInstance]:
        """Draw cards from the draw pile to a player's hand."""
        drawn = []
        for _ in range(count):
            if not self.draw_pile:
                # Reshuffle discard pile if draw pile is empty
                if self.discard_pile:
                    self.draw_pile = self.discard_pile
                    self.discard_pile = []
                    random.shuffle(self.draw_pile)
                else:
                    break  # No cards left anywhere

            if self.draw_pile:
                card = self.draw_pile.pop()
                self.players[player_idx].hand.append(card)
                drawn.append(card)

        return drawn

    def discard_card(self, card: CardInstance, from_player_idx: int) -> None:
        """Move a card from a player's hand to the discard pile."""
        player = self.players[from_player_idx]
        if card in player.hand:
            player.hand.remove(card)
            self.discard_pile.append(card)

    def add_to_stable(self, card: CardInstance, player_idx: int) -> None:
        """Add a card to a player's stable."""
        player = self.players[player_idx]

        if card.card_type == CardType.UPGRADE:
            player.upgrades.append(card)
        elif card.card_type == CardType.DOWNGRADE:
            player.downgrades.append(card)
        elif card.is_unicorn():
            player.stable.append(card)

    def remove_from_stable(self, card: CardInstance, player_idx: int) -> None:
        """Remove a card from a player's stable to the discard pile."""
        player = self.players[player_idx]

        if card in player.stable:
            player.stable.remove(card)
        elif card in player.upgrades:
            player.upgrades.remove(card)
        elif card in player.downgrades:
            player.downgrades.remove(card)

        self.discard_pile.append(card)

    def get_baby_unicorn_from_nursery(self) -> Optional[CardInstance]:
        """Get a baby unicorn from the nursery."""
        if self.nursery:
            return self.nursery.pop()
        return None

    def return_baby_to_nursery(self, card: CardInstance) -> None:
        """Return a baby unicorn to the nursery."""
        if card.card_type == CardType.BABY_UNICORN:
            self.nursery.append(card)

    def find_card_owner(self, card: CardInstance) -> Optional[int]:
        """Find which player owns a card (in stable or hand)."""
        for player in self.players:
            if card in player.hand:
                return player.player_idx
            if card in player.stable:
                return player.player_idx
            if card in player.upgrades:
                return player.player_idx
            if card in player.downgrades:
                return player.player_idx
        return None

    def copy(self) -> 'GameState':
        """Create a deep copy of the game state for simulation."""
        return GameState(
            players=[p.copy() for p in self.players],
            num_players=self.num_players,
            draw_pile=list(self.draw_pile),
            discard_pile=list(self.discard_pile),
            nursery=list(self.nursery),
            current_player_idx=self.current_player_idx,
            phase=self.phase,
            turn_number=self.turn_number,
            actions_remaining=self.actions_remaining,
            unicorns_to_win=self.unicorns_to_win,
            winner=self.winner,
            resolution_stack=deepcopy(self.resolution_stack),
            card_being_played=self.card_being_played,
            neigh_chain_active=self.neigh_chain_active,
            players_passed_on_neigh=set(self.players_passed_on_neigh),
        )

    def determinize_for_player(self, player_idx: int) -> 'GameState':
        """Create a determinized copy for MCTS from a player's perspective.

        This replaces unknown information (other players' hands, deck order)
        with random samples from the possible card pool.
        """
        state = self.copy()

        # Collect all cards that are hidden from this player
        hidden_cards: List[CardInstance] = []

        # Add cards from other players' hands (unless visible)
        for player in state.players:
            if player.player_idx != player_idx and not player.hand_visible:
                hidden_cards.extend(player.hand)
                player.hand = []

        # Add draw pile cards (unknown order)
        hidden_cards.extend(state.draw_pile)
        state.draw_pile = []

        # Shuffle all hidden cards
        random.shuffle(hidden_cards)

        # Redistribute to players and deck
        for player in state.players:
            if player.player_idx != player_idx and not player.hand_visible:
                # Restore hand with random cards
                original_hand_size = len(self.players[player.player_idx].hand)
                player.hand = hidden_cards[:original_hand_size]
                hidden_cards = hidden_cards[original_hand_size:]

        # Remaining cards go to draw pile
        state.draw_pile = hidden_cards

        return state

    def get_legal_actions(self) -> List:
        """Get all legal actions for the current player."""
        # This will be implemented in action.py and linked here
        from game.action import get_legal_actions
        return get_legal_actions(self)

    def apply_action(self, action) -> 'GameState':
        """Apply an action and return the new state."""
        # This will be implemented in action.py and linked here
        from game.action import apply_action
        return apply_action(self, action)

    def __repr__(self) -> str:
        player_info = ", ".join(
            f"{p.name}: {p.unicorn_count()} unicorns"
            for p in self.players
        )
        return f"GameState(turn={self.turn_number}, phase={self.phase.name}, {player_info})"


@dataclass
class EffectTask:
    """A task in the resolution stack."""
    effect: 'Effect'
    controller_idx: int
    source_card: CardInstance
    current_action_idx: int = 0
    targets_chosen: List[Any] = field(default_factory=list)  # Stored targets for multi-step effects

    def __repr__(self) -> str:
        return f"Task({self.effect.name}, step={self.current_action_idx})"
