"""Information Set Monte Carlo Tree Search (ISMCTS) for Unstable Unicorns.

ISMCTS is better suited for games with hidden information than
standard MCTS with determinization. It builds a single tree over
information sets rather than multiple trees over determinized states.

Based on: "Information Set Monte Carlo Tree Search" by Cowling, Powley, Whitehouse
"""

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, TYPE_CHECKING

from players.player import Player

if TYPE_CHECKING:
    from game.game_state import GameState
    from game.action import Action


@dataclass
class ISMCTSNode:
    """Node in the ISMCTS tree.

    Unlike regular MCTS, nodes represent information sets (what the
    acting player knows) rather than complete game states.
    """
    player_idx: int  # Player who acts at this node
    parent: Optional['ISMCTSNode'] = None
    parent_action: Optional['Action'] = None
    children: Dict[str, 'ISMCTSNode'] = field(default_factory=dict)  # action_key -> node

    # Statistics
    visits: int = 0
    total_value: float = 0.0
    availability_count: int = 0  # Times this node was available

    # Actions that lead to this node (for availability tracking)
    incoming_actions: Set[str] = field(default_factory=set)

    @property
    def value(self) -> float:
        """Average value of this node."""
        if self.visits == 0:
            return 0.0
        return self.total_value / self.visits

    def ucb1(self, exploration: float = 1.41) -> float:
        """Calculate UCB1 score with availability correction."""
        if self.visits == 0:
            return float('inf')
        if self.availability_count == 0:
            return float('inf')

        exploitation = self.value
        exploration_term = exploration * math.sqrt(
            math.log(self.availability_count) / self.visits
        )
        return exploitation + exploration_term


class ISMCTS:
    """Information Set Monte Carlo Tree Search.

    Key differences from regular MCTS:
    1. Single tree shared across all determinizations
    2. Nodes track availability (how often they're reachable)
    3. Selection considers only available actions in current determinization
    """

    def __init__(
        self,
        iterations: int = 1000,
        exploration: float = 0.7,
        rollout_depth: int = 50
    ):
        """Initialize ISMCTS.

        Args:
            iterations: Number of iterations to run
            exploration: UCB1 exploration constant (lower than MCTS due to noise)
            rollout_depth: Maximum rollout depth
        """
        self.iterations = iterations
        self.exploration = exploration
        self.rollout_depth = rollout_depth

    def search(self, state: 'GameState', player_idx: int) -> 'Action':
        """Search for the best action using ISMCTS.

        Args:
            state: Current game state (from player's perspective)
            player_idx: Index of the player making the decision

        Returns:
            Best action found
        """
        from game.action import get_legal_actions

        # Get initial legal actions
        actions = get_legal_actions(state)
        if len(actions) <= 1:
            return actions[0] if actions else None

        # Create root node
        root = ISMCTSNode(player_idx=state.current_player_idx)

        for _ in range(self.iterations):
            # Create a determinization for this iteration
            det_state = state.determinize_for_player(player_idx)

            # Run one iteration of ISMCTS
            self._iterate(root, det_state, player_idx)

        # Select best action based on visit counts
        best_action = self._select_best_action(root, actions)
        return best_action

    def _iterate(
        self,
        root: ISMCTSNode,
        state: 'GameState',
        perspective_player: int
    ) -> None:
        """Run one iteration of ISMCTS."""
        from game.action import get_legal_actions, apply_action

        node = root
        state = state.copy()
        path: List[Tuple[ISMCTSNode, str]] = []

        # Selection phase
        while True:
            actions = get_legal_actions(state)
            if not actions or state.is_game_over():
                break

            action_keys = [self._action_key(a) for a in actions]

            # Update availability for existing children
            for key in action_keys:
                if key in node.children:
                    node.children[key].availability_count += 1

            # Check for unexplored actions
            unexplored = [
                (a, k) for a, k in zip(actions, action_keys)
                if k not in node.children
            ]

            if unexplored:
                # Expansion: add a new child
                action, key = random.choice(unexplored)
                child = ISMCTSNode(
                    player_idx=state.get_next_player_idx() if action.action_type.name != "NEIGH" else state.current_player_idx,
                    parent=node,
                    parent_action=action
                )
                child.availability_count = 1
                node.children[key] = child
                path.append((node, key))

                state = apply_action(state, action)
                node = child
                break
            else:
                # Selection: choose among available children
                available_children = [
                    (node.children[k], k, a)
                    for a, k in zip(actions, action_keys)
                    if k in node.children
                ]

                if not available_children:
                    break

                # Select using UCB1
                best_child, best_key, best_action = max(
                    available_children,
                    key=lambda x: x[0].ucb1(self.exploration)
                )

                path.append((node, best_key))
                state = apply_action(state, best_action)
                node = best_child

        # Rollout phase
        value = self._rollout(state, perspective_player)

        # Backpropagation
        for parent_node, action_key in path:
            child = parent_node.children[action_key]
            child.visits += 1
            child.total_value += value

        # Update root
        root.visits += 1

    def _rollout(self, state: 'GameState', player_idx: int) -> float:
        """Perform a random rollout and return value for player."""
        from game.action import get_legal_actions, apply_action

        state = state.copy()
        depth = 0

        while not state.is_game_over() and depth < self.rollout_depth:
            actions = get_legal_actions(state)
            if not actions:
                break

            # Use simple heuristic for rollout policy
            action = self._rollout_policy(state, actions, player_idx)
            state = apply_action(state, action)
            depth += 1

        return self._evaluate(state, player_idx)

    def _rollout_policy(
        self,
        state: 'GameState',
        actions: List['Action'],
        player_idx: int
    ) -> 'Action':
        """Policy for selecting actions during rollout.

        Uses a mix of random and heuristic selection.
        """
        from game.action import ActionType

        # 70% random, 30% heuristic
        if random.random() < 0.7:
            return random.choice(actions)

        # Simple heuristics
        scores = []
        for action in actions:
            score = 0.0

            if action.action_type == ActionType.PLAY_CARD:
                if action.card.is_unicorn():
                    score += 2.0
                if action.card.card_type.name == "MAGIC":
                    score += 1.0

            elif action.action_type == ActionType.NEIGH:
                if state.card_being_played and state.card_being_played.is_unicorn():
                    score += 1.5

            elif action.action_type == ActionType.END_ACTION_PHASE:
                score -= 0.5

            scores.append(score)

        # Softmax selection
        max_score = max(scores)
        exp_scores = [math.exp(s - max_score) for s in scores]
        total = sum(exp_scores)
        probs = [e / total for e in exp_scores]

        r = random.random()
        cumsum = 0.0
        for action, prob in zip(actions, probs):
            cumsum += prob
            if r <= cumsum:
                return action

        return actions[-1]

    def _evaluate(self, state: 'GameState', player_idx: int) -> float:
        """Evaluate terminal or near-terminal state."""
        if state.winner == player_idx:
            return 1.0
        elif state.winner is not None:
            return 0.0

        # Heuristic evaluation
        player = state.players[player_idx]
        target = state.unicorns_to_win

        progress = player.unicorn_count() / target

        other_max = max(
            p.unicorn_count() for p in state.players
            if p.player_idx != player_idx
        )
        threat = other_max / target

        return 0.5 + 0.3 * progress - 0.2 * threat

    def _action_key(self, action: 'Action') -> str:
        """Create a unique key for an action."""
        key_parts = [action.action_type.name, str(action.player_idx)]

        if action.card:
            key_parts.append(action.card.card.id)

        if action.target_card:
            key_parts.append(f"t:{action.target_card.card.id}")

        if action.target_player_idx is not None:
            key_parts.append(f"p:{action.target_player_idx}")

        return "|".join(key_parts)

    def _select_best_action(
        self,
        root: ISMCTSNode,
        actions: List['Action']
    ) -> 'Action':
        """Select the best action based on visit counts."""
        action_visits = []

        for action in actions:
            key = self._action_key(action)
            if key in root.children:
                action_visits.append((action, root.children[key].visits))
            else:
                action_visits.append((action, 0))

        # Select action with most visits
        best_action, _ = max(action_visits, key=lambda x: x[1])
        return best_action


class ISMCTSPlayer(Player):
    """Player using Information Set MCTS."""

    def __init__(
        self,
        name: str,
        iterations: int = 500,
        exploration: float = 0.7
    ):
        """Initialize ISMCTS player.

        Args:
            name: Player name
            iterations: MCTS iterations
            exploration: UCB1 exploration constant
        """
        super().__init__(name)
        self.ismcts = ISMCTS(iterations=iterations, exploration=exploration)
        self.player_idx: Optional[int] = None

    def choose_action(
        self,
        state: 'GameState',
        valid_actions: List['Action']
    ) -> 'Action':
        """Choose action using ISMCTS."""
        if len(valid_actions) == 1:
            return valid_actions[0]

        self.player_idx = valid_actions[0].player_idx
        return self.ismcts.search(state, self.player_idx)

    def choose_target(
        self,
        state: 'GameState',
        valid_targets: List,
        prompt: str
    ) -> object:
        """Choose target (uses heuristics for now)."""
        # Simple heuristic: prefer opponent's cards for destruction
        # For more complex targeting, could run mini-MCTS
        return random.choice(valid_targets)
