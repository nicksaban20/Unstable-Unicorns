"""Monte Carlo Tree Search implementation for Unstable Unicorns.

Uses determinization to handle hidden information (opponent hands).
"""

import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from game.game_state import GameState
    from game.action import Action


@dataclass
class MCTSNode:
    """Node in the MCTS tree."""
    state: 'GameState'
    parent: Optional['MCTSNode'] = None
    parent_action: Optional['Action'] = None
    children: Dict[int, 'MCTSNode'] = field(default_factory=dict)  # action_idx -> node
    visits: int = 0
    total_value: float = 0.0
    untried_actions: List['Action'] = field(default_factory=list)

    @property
    def value(self) -> float:
        """Average value of this node."""
        if self.visits == 0:
            return 0.0
        return self.total_value / self.visits

    def is_fully_expanded(self) -> bool:
        """Check if all actions have been tried."""
        return len(self.untried_actions) == 0

    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return self.state.is_game_over()

    def ucb1(self, exploration: float = 1.41) -> float:
        """Calculate UCB1 score for node selection."""
        if self.visits == 0:
            return float('inf')
        if self.parent is None:
            return self.value

        exploitation = self.value
        exploration_term = exploration * math.sqrt(
            math.log(self.parent.visits) / self.visits
        )
        return exploitation + exploration_term


class MCTS:
    """Monte Carlo Tree Search with determinization for hidden information."""

    def __init__(
        self,
        iterations: int = 1000,
        exploration: float = 1.41,
        determinizations: int = 5,
        rollout_depth: int = 50
    ):
        """Initialize MCTS.

        Args:
            iterations: Number of MCTS iterations per determinization
            exploration: UCB1 exploration constant
            determinizations: Number of determinized samples to average
            rollout_depth: Maximum depth for rollout simulations
        """
        self.iterations = iterations
        self.exploration = exploration
        self.determinizations = determinizations
        self.rollout_depth = rollout_depth

    def search(self, state: 'GameState', player_idx: int) -> 'Action':
        """Search for the best action from the given state.

        Uses determinization to handle hidden information by sampling
        possible worlds and averaging results.

        Args:
            state: Current game state
            player_idx: Index of the player making the decision

        Returns:
            The best action found
        """
        from game.action import get_legal_actions

        # Get legal actions
        actions = get_legal_actions(state)
        if len(actions) == 1:
            return actions[0]

        # Aggregate action scores across determinizations
        action_scores: Dict[int, float] = {i: 0.0 for i in range(len(actions))}
        action_visits: Dict[int, int] = {i: 0 for i in range(len(actions))}

        for _ in range(self.determinizations):
            # Create determinized state
            det_state = state.determinize_for_player(player_idx)

            # Run MCTS on determinized state
            root = self._create_node(det_state)
            root.untried_actions = list(actions)  # Use same action list

            for _ in range(self.iterations):
                node = self._select(root)
                if not node.is_terminal():
                    if not node.is_fully_expanded():
                        node = self._expand(node)
                    value = self._rollout(node.state, player_idx)
                else:
                    value = self._evaluate_terminal(node.state, player_idx)
                self._backpropagate(node, value)

            # Aggregate results
            for action_idx, child in root.children.items():
                action_scores[action_idx] += child.total_value
                action_visits[action_idx] += child.visits

        # Select action with highest average value
        best_action_idx = max(
            range(len(actions)),
            key=lambda i: (
                action_scores[i] / action_visits[i]
                if action_visits[i] > 0 else -float('inf')
            )
        )

        return actions[best_action_idx]

    def _create_node(self, state: 'GameState') -> MCTSNode:
        """Create a new MCTS node."""
        from game.action import get_legal_actions

        node = MCTSNode(state=state)
        if not state.is_game_over():
            node.untried_actions = get_legal_actions(state)
        return node

    def _select(self, node: MCTSNode) -> MCTSNode:
        """Select a node to expand using UCB1."""
        while not node.is_terminal():
            if not node.is_fully_expanded():
                return node
            # Check if there are any children to select from
            if not node.children:
                return node  # No children, treat as terminal
            # Select child with highest UCB1
            best_child = max(
                node.children.values(),
                key=lambda n: n.ucb1(self.exploration)
            )
            node = best_child
        return node

    def _expand(self, node: MCTSNode) -> MCTSNode:
        """Expand the node by trying an untried action."""
        from game.action import apply_action

        # Pick a random untried action
        action_idx = random.randrange(len(node.untried_actions))
        action = node.untried_actions.pop(action_idx)

        # Apply action to get new state
        new_state = node.state.copy()
        new_state = apply_action(new_state, action)

        # Create child node
        child = self._create_node(new_state)
        child.parent = node
        child.parent_action = action

        # Store child by the action's index in the original list
        # We need to find the original index
        from game.action import get_legal_actions
        original_actions = get_legal_actions(node.state)
        for i, orig_action in enumerate(original_actions):
            if self._actions_equal(orig_action, action):
                node.children[i] = child
                break

        return child

    def _actions_equal(self, a1: 'Action', a2: 'Action') -> bool:
        """Check if two actions are equivalent."""
        if a1.action_type != a2.action_type:
            return False
        if a1.player_idx != a2.player_idx:
            return False
        if a1.card is not None and a2.card is not None:
            if a1.card.instance_id != a2.card.instance_id:
                return False
        elif a1.card is not a2.card:
            return False
        return True

    def _rollout(self, state: 'GameState', player_idx: int) -> float:
        """Perform a random rollout and return the value."""
        from game.action import get_legal_actions, apply_action

        state = state.copy()
        depth = 0

        while not state.is_game_over() and depth < self.rollout_depth:
            actions = get_legal_actions(state)
            if not actions:
                break
            action = random.choice(actions)
            state = apply_action(state, action)
            depth += 1

        return self._evaluate_terminal(state, player_idx)

    def _evaluate_terminal(self, state: 'GameState', player_idx: int) -> float:
        """Evaluate a terminal or near-terminal state."""
        if state.winner == player_idx:
            return 1.0
        elif state.winner is not None:
            return 0.0

        # Non-terminal: use heuristic evaluation
        from game.game_engine import GameSimulator
        return GameSimulator.evaluate_state(state, player_idx)

    def _backpropagate(self, node: MCTSNode, value: float) -> None:
        """Backpropagate the value up the tree."""
        while node is not None:
            node.visits += 1
            node.total_value += value
            node = node.parent


class MCTSPlayer:
    """MCTS-based AI player."""

    def __init__(
        self,
        name: str,
        iterations: int = 500,
        determinizations: int = 3
    ):
        """Initialize MCTS player.

        Args:
            name: Player name
            iterations: MCTS iterations per determinization
            determinizations: Number of world samples
        """
        self.name = name
        self.mcts = MCTS(
            iterations=iterations,
            determinizations=determinizations
        )
        self.player_idx: Optional[int] = None

    def choose_action(
        self,
        state: 'GameState',
        valid_actions: List['Action']
    ) -> 'Action':
        """Choose action using MCTS."""
        if len(valid_actions) == 1:
            return valid_actions[0]

        # Determine our player index from the actions
        self.player_idx = valid_actions[0].player_idx

        return self.mcts.search(state, self.player_idx)

    def choose_target(
        self,
        state: 'GameState',
        valid_targets: List,
        prompt: str
    ) -> object:
        """Choose target (simplified: random for now)."""
        return random.choice(valid_targets)
