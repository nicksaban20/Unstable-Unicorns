"""Game simulation utilities for AI planning."""

import random
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from game.game_state import GameState


def simulate_random_playout(
    state: 'GameState',
    max_turns: int = 100
) -> Optional[int]:
    """Simulate a game to completion with random moves.

    Args:
        state: Starting state (will be copied)
        max_turns: Maximum turns before giving up

    Returns:
        Winner index or None if max_turns reached
    """
    from game.game_state import GamePhase
    from game.action import get_legal_actions, apply_action, _process_end_of_turn

    state = state.copy()
    turns = 0

    while not state.is_game_over() and turns < max_turns:
        actions = get_legal_actions(state)

        if not actions:
            # Handle stuck states
            if state.phase == GamePhase.ACTION:
                state.phase = GamePhase.END
                _process_end_of_turn(state)
            elif state.phase == GamePhase.DRAW:
                state.phase = GamePhase.ACTION
            elif state.phase == GamePhase.BEGINNING:
                state.phase = GamePhase.DRAW
            elif state.phase == GamePhase.END:
                _process_end_of_turn(state)
            continue

        # Choose random action
        action = random.choice(actions)
        state = apply_action(state, action)
        turns += 1

    return state.winner


def simulate_with_policy(
    state: 'GameState',
    policy_fn,
    max_turns: int = 100
) -> Optional[int]:
    """Simulate a game using a policy function.

    Args:
        state: Starting state
        policy_fn: Function(state, actions) -> action
        max_turns: Maximum turns

    Returns:
        Winner index or None
    """
    from game.game_state import GamePhase
    from game.action import get_legal_actions, apply_action, _process_end_of_turn

    state = state.copy()
    turns = 0

    while not state.is_game_over() and turns < max_turns:
        actions = get_legal_actions(state)

        if not actions:
            if state.phase == GamePhase.ACTION:
                state.phase = GamePhase.END
                _process_end_of_turn(state)
            elif state.phase == GamePhase.DRAW:
                state.phase = GamePhase.ACTION
            elif state.phase == GamePhase.BEGINNING:
                state.phase = GamePhase.DRAW
            continue

        action = policy_fn(state, actions)
        state = apply_action(state, action)
        turns += 1

    return state.winner


def run_simulations(
    state: 'GameState',
    num_simulations: int = 100,
    max_turns: int = 100
) -> List[Optional[int]]:
    """Run multiple random simulations from a state.

    Args:
        state: Starting state
        num_simulations: Number of simulations to run
        max_turns: Max turns per simulation

    Returns:
        List of winners (or None for timeouts)
    """
    results = []
    for _ in range(num_simulations):
        winner = simulate_random_playout(state, max_turns)
        results.append(winner)
    return results


def estimate_win_probability(
    state: 'GameState',
    player_idx: int,
    num_simulations: int = 100
) -> float:
    """Estimate win probability for a player through simulation.

    Args:
        state: Current state
        player_idx: Player to estimate for
        num_simulations: Number of simulations

    Returns:
        Estimated win probability (0.0 to 1.0)
    """
    results = run_simulations(state, num_simulations)

    wins = sum(1 for w in results if w == player_idx)
    valid = sum(1 for w in results if w is not None)

    if valid == 0:
        return 0.5  # No valid results, return neutral

    return wins / valid
