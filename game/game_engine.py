"""Game engine for Unstable Unicorns.

Manages game flow, turn order, and coordinates between players.
"""

import random
from typing import List, Optional, TYPE_CHECKING

from cards.card_database import CARD_DATABASE
from game.game_state import GameState, PlayerState, GamePhase
from game.action import Action, ActionType, get_legal_actions, apply_action

if TYPE_CHECKING:
    from players.player import Player


class GameEngine:
    """Main game engine that runs Unstable Unicorns games."""

    def __init__(self, player_names: List[str], verbose: bool = True):
        """Initialize a new game.

        Args:
            player_names: Names of players (2-6 players)
            verbose: Whether to print game events
        """
        self.num_players = len(player_names)
        if not 2 <= self.num_players <= 6:
            raise ValueError("Game requires 2-6 players")

        self.verbose = verbose
        self.players: List['Player'] = []  # Will be set by set_players()
        self.state = self._create_initial_state(player_names)

    def _create_initial_state(self, player_names: List[str]) -> GameState:
        """Create the initial game state."""
        # Create player states
        players = [
            PlayerState(player_idx=i, name=name)
            for i, name in enumerate(player_names)
        ]

        # Create deck and nursery
        deck = CARD_DATABASE.create_deck()
        nursery = CARD_DATABASE.create_nursery()

        # Shuffle deck
        random.shuffle(deck)

        # Create game state
        state = GameState(
            players=players,
            num_players=self.num_players,
            draw_pile=deck,
            nursery=nursery,
        )

        # Deal starting hands (5 cards each)
        for player in state.players:
            state.draw_card(player.player_idx, 5)

        # Each player gets a baby unicorn
        for player in state.players:
            baby = state.get_baby_unicorn_from_nursery()
            if baby:
                state.add_to_stable(baby, player.player_idx)

        # Randomly determine starting player
        state.current_player_idx = random.randint(0, self.num_players - 1)
        state.phase = GamePhase.BEGINNING

        return state

    def set_players(self, players: List['Player']) -> None:
        """Set the player controllers."""
        if len(players) != self.num_players:
            raise ValueError(f"Expected {self.num_players} players, got {len(players)}")
        self.players = players

    def run_game(self, max_turns: int = 500) -> int:
        """Run a complete game and return the winner's index.

        Args:
            max_turns: Maximum number of turns before declaring a draw (-1 for the player
                       with the most unicorns wins, or 0 if tied).
        """
        if not self.players:
            raise ValueError("No players set. Call set_players() first.")

        if self.verbose:
            print("\n" + "=" * 50)
            print("UNSTABLE UNICORNS")
            print("=" * 50)
            print(f"Players: {', '.join(p.name for p in self.state.players)}")
            print(f"First player: {self.state.current_player.name}")
            print("=" * 50 + "\n")

        turns = 0
        while not self.state.is_game_over() and turns < max_turns:
            self._run_turn()
            turns += 1

        # If max_turns reached without a winner, pick the player with most unicorns
        if self.state.winner is None:
            best_player = max(self.state.players, key=lambda p: p.unicorn_count())
            self.state.winner = best_player.player_idx

        if self.verbose:
            print("\n" + "=" * 50)
            print(f"GAME OVER! Winner: {self.state.players[self.state.winner].name}")
            print("=" * 50)

        return self.state.winner

    def _run_turn(self) -> None:
        """Run a single turn."""
        player_idx = self.state.current_player_idx
        player_controller = self.players[player_idx]

        if self.verbose:
            print(f"\n--- Turn {self.state.turn_number}: {self.state.current_player.name} ---")
            self._print_game_status()

        # Beginning of turn phase
        if self.state.phase == GamePhase.BEGINNING:
            self._process_beginning_phase()
            # Handle any pending effect resolutions
            self._resolve_pending_effects()

        # Draw phase
        if self.state.phase == GamePhase.DRAW:
            self._process_draw_phase(player_controller)

        # Action phase
        while self.state.phase == GamePhase.ACTION and not self.state.is_game_over():
            self._process_action_phase(player_controller)

        # End phase
        if self.state.phase == GamePhase.END:
            self._process_end_phase()
            # Handle any pending effect resolutions
            self._resolve_pending_effects()

    def _resolve_pending_effects(self) -> None:
        """Resolve any pending effects that require targeting."""
        max_iterations = 50  # Safety limit
        iterations = 0

        while self.state.resolution_stack and iterations < max_iterations:
            iterations += 1
            actions = get_legal_actions(self.state)

            if not actions:
                # No valid targets, pop the effect
                if self.state.resolution_stack:
                    self.state.resolution_stack.pop()
                continue

            # Check if these are target choice actions
            target_actions = [a for a in actions if a.action_type == ActionType.CHOOSE_TARGET]
            if not target_actions:
                break  # Not a targeting situation

            # Get the controller for this effect
            task = self.state.resolution_stack[-1]
            controller = self.players[task.controller_idx]

            # Let the controller choose a target
            action = controller.choose_action(self.state, target_actions)

            if self.verbose and action.target_card:
                print(f"  {self.state.players[task.controller_idx].name} targets: {action.target_card.name}")

            self.state = apply_action(self.state, action)

    def _process_beginning_phase(self) -> None:
        """Process the beginning of turn phase."""
        from game.action import _process_beginning_of_turn
        _process_beginning_of_turn(self.state)

    def _process_draw_phase(self, player_controller: 'Player') -> None:
        """Process the draw phase."""
        actions = get_legal_actions(self.state)

        if not actions:
            # No valid actions, skip to action phase
            self.state.phase = GamePhase.ACTION
            return

        # For draw phase, automatically draw (player doesn't choose)
        draw_action = next(
            (a for a in actions if a.action_type == ActionType.DRAW_CARD),
            None
        )

        if draw_action:
            self.state = apply_action(self.state, draw_action)
            if self.verbose:
                print(f"  Drew a card")

    def _process_action_phase(self, player_controller: 'Player') -> None:
        """Process the action phase."""
        # Handle Neigh chain if active
        while self.state.neigh_chain_active:
            self._process_neigh_chain()

        actions = get_legal_actions(self.state)

        if not actions:
            # No valid actions, end action phase
            self.state.phase = GamePhase.END
            return

        # Get player's chosen action
        action = player_controller.choose_action(self.state, actions)

        if self.verbose and action.action_type == ActionType.PLAY_CARD:
            print(f"  Playing: {action.card.name}")
        elif self.verbose and action.action_type == ActionType.END_ACTION_PHASE:
            print(f"  Ending action phase")

        self.state = apply_action(self.state, action)

        # Handle any Neigh chain that started
        while self.state.neigh_chain_active:
            self._process_neigh_chain()

    def _process_neigh_chain(self) -> None:
        """Process Neigh responses."""
        while self.state.neigh_chain_active:
            actions = get_legal_actions(self.state)

            if not actions:
                # Everyone passed, resolve the chain
                self.state.neigh_chain_active = False
                break

            # Find the responding player
            responder_idx = actions[0].player_idx
            responder_controller = self.players[responder_idx]

            action = responder_controller.choose_action(self.state, actions)

            if self.verbose:
                if action.action_type == ActionType.NEIGH:
                    print(f"  {self.state.players[responder_idx].name} plays {action.card.name}!")
                else:
                    print(f"  {self.state.players[responder_idx].name} passes on Neigh")

            self.state = apply_action(self.state, action)

    def _process_end_phase(self) -> None:
        """Process the end of turn phase."""
        from game.action import _process_end_of_turn
        _process_end_of_turn(self.state)

    def _print_game_status(self) -> None:
        """Print current game status."""
        for player in self.state.players:
            unicorn_count = player.unicorn_count()
            marker = " <--" if player.player_idx == self.state.current_player_idx else ""
            print(f"  {player.name}: {unicorn_count}/{self.state.unicorns_to_win} unicorns, "
                  f"{len(player.hand)} cards in hand{marker}")


class GameSimulator:
    """Lightweight game simulator for AI planning.

    Faster than full GameEngine, used for MCTS rollouts.
    """

    @staticmethod
    def simulate_random_game(state: GameState, max_turns: int = 100) -> Optional[int]:
        """Simulate a game to completion with random moves.

        Returns the winner's index or None if max_turns reached.
        """
        state = state.copy()
        turns = 0

        while not state.is_game_over() and turns < max_turns:
            actions = get_legal_actions(state)

            if not actions:
                # Force end of turn if stuck
                if state.phase == GamePhase.ACTION:
                    state.phase = GamePhase.END
                    from game.action import _process_end_of_turn
                    _process_end_of_turn(state)
                elif state.phase == GamePhase.DRAW:
                    state.phase = GamePhase.ACTION
                elif state.phase == GamePhase.BEGINNING:
                    state.phase = GamePhase.DRAW
                continue

            # Choose random action
            action = random.choice(actions)
            state = apply_action(state, action)
            turns += 1

        return state.winner

    @staticmethod
    def evaluate_state(state: GameState, player_idx: int) -> float:
        """Evaluate a game state for a player.

        Returns a score between 0 and 1.
        """
        if state.winner == player_idx:
            return 1.0
        elif state.winner is not None:
            return 0.0

        player = state.players[player_idx]
        target = state.unicorns_to_win

        # Progress toward winning
        progress = player.unicorn_count() / target

        # Adjust for other players' progress
        other_max = max(
            p.unicorn_count() for p in state.players
            if p.player_idx != player_idx
        )
        threat = other_max / target

        # Hand quality (having cards is good)
        hand_value = min(len(player.hand) / 7, 1.0) * 0.1

        # Upgrade/downgrade balance
        upgrade_value = len(player.upgrades) * 0.05
        downgrade_penalty = len(player.downgrades) * 0.05

        score = progress * 0.7 + (1 - threat) * 0.15 + hand_value + upgrade_value - downgrade_penalty

        return max(0.0, min(1.0, score))
