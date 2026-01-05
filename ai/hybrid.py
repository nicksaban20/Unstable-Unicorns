"""Hybrid AI combining MCTS with Evolutionary-trained heuristics."""

import math
import random
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from game.game_state import GameState
from game.action import Action, get_legal_actions, apply_action
from ai.evolutionary import EvolutionaryWeights, TRAINED_WEIGHTS
from ai.heuristics import evaluate_state


@dataclass
class HybridNode:
    """Node in the hybrid MCTS tree."""
    state: GameState
    parent: Optional['HybridNode']
    action: Optional[Action]
    children: Dict[str, 'HybridNode']
    visits: int
    total_value: float
    untried_actions: List[Action]
    player_idx: int
    prior_probability: float  # From evolutionary heuristics

    def __init__(self, state: GameState, parent: Optional['HybridNode'] = None,
                 action: Optional[Action] = None, player_idx: int = 0,
                 prior_probability: float = 1.0):
        self.state = state
        self.parent = parent
        self.action = action
        self.children = {}
        self.visits = 0
        self.total_value = 0.0
        self.player_idx = player_idx
        self.prior_probability = prior_probability
        self.untried_actions = get_legal_actions(state) if not state.is_game_over() else []

    @property
    def value(self) -> float:
        """Average value of this node."""
        return self.total_value / self.visits if self.visits > 0 else 0.0

    def ucb1_with_prior(self, exploration: float = 1.414, prior_weight: float = 0.5) -> float:
        """UCB1 formula enhanced with prior probability from evolutionary heuristics."""
        if self.visits == 0:
            return float('inf')

        exploitation = self.value
        exploration_term = exploration * math.sqrt(math.log(self.parent.visits) / self.visits)
        prior_bonus = prior_weight * self.prior_probability / (1 + self.visits)

        return exploitation + exploration_term + prior_bonus

    def select_child(self, exploration: float = 1.414) -> 'HybridNode':
        """Select child using UCB1 with prior."""
        return max(self.children.values(), key=lambda c: c.ucb1_with_prior(exploration))

    def is_fully_expanded(self) -> bool:
        """Check if all actions have been tried."""
        return len(self.untried_actions) == 0

    def is_terminal(self) -> bool:
        """Check if this is a terminal node."""
        return self.state.is_game_over()


class HybridMCTS:
    """
    Hybrid AI combining MCTS with Evolutionary-trained heuristics.

    Key innovations:
    1. Uses evolutionary weights to compute prior probabilities for actions
    2. MCTS exploration is biased toward evolutionary-preferred actions
    3. State evaluation uses evolutionary heuristics during rollouts
    4. Progressive widening to focus on promising actions
    """

    def __init__(self, iterations: int = 500, determinizations: int = 5,
                 weights: Optional[EvolutionaryWeights] = None,
                 exploration: float = 1.414, prior_weight: float = 0.5,
                 rollout_depth: int = 30):
        self.iterations = iterations
        self.determinizations = determinizations
        self.weights = weights or TRAINED_WEIGHTS
        self.exploration = exploration
        self.prior_weight = prior_weight
        self.rollout_depth = rollout_depth

    def compute_action_priors(self, state: GameState, actions: List[Action],
                              player_idx: int) -> Dict[str, float]:
        """Compute prior probabilities for actions using evolutionary weights."""
        if not actions:
            return {}

        scores = {}
        for action in actions:
            score = self._evaluate_action(state, action, player_idx)
            scores[self._action_key(action)] = score

        # Convert scores to probabilities using softmax
        if not scores:
            return {}

        max_score = max(scores.values())
        exp_scores = {k: math.exp(v - max_score) for k, v in scores.items()}
        total = sum(exp_scores.values())

        return {k: v / total for k, v in exp_scores.items()}

    def _evaluate_action(self, state: GameState, action: Action, player_idx: int) -> float:
        """Evaluate an action using evolutionary weights."""
        from game.action import ActionType

        score = 0.0

        if action.action_type == ActionType.PLAY_CARD and action.card:
            card = action.card

            # Card type bonuses from evolutionary weights
            if card.is_unicorn():
                if card.card_type.name == 'MAGICAL_UNICORN':
                    score += self.weights.magical_unicorn
                elif card.card_type.name == 'BABY_UNICORN':
                    score += self.weights.baby_unicorn
                else:
                    score += self.weights.basic_unicorn
            elif card.card_type.name == 'UPGRADE':
                score += self.weights.upgrade
            elif card.card_type.name == 'DOWNGRADE':
                score += self.weights.downgrade
            elif card.card_type.name == 'MAGIC':
                score += self.weights.magic

        elif action.action_type == ActionType.NEIGH:
            # Evaluate whether to neigh based on card being played
            if state.card_being_played:
                threat = self._evaluate_threat(state.card_being_played, state, player_idx)
                score += threat * self.weights.neigh_value

        elif action.action_type == ActionType.END_ACTION_PHASE:
            score += self.weights.end_action_penalty

        return score

    def _evaluate_threat(self, card, state: GameState, player_idx: int) -> float:
        """Evaluate how threatening a card is."""
        threat = 0.0

        if card.is_unicorn():
            # Check if opponent is close to winning
            for i, player in enumerate(state.players):
                if i != player_idx:
                    unicorns = player.unicorn_count()
                    if unicorns >= state.unicorns_to_win - 2:
                        threat += 2.0  # Critical threat
                    elif unicorns >= state.unicorns_to_win - 3:
                        threat += 1.0

        # Magical unicorns are more threatening
        if card.card_type.name == 'MAGICAL_UNICORN':
            threat += 0.5

        return threat

    def _action_key(self, action: Action) -> str:
        """Create a unique key for an action."""
        if action.card:
            return f"{action.action_type.name}_{action.card.instance_id}"
        return action.action_type.name

    def search(self, root_state: GameState, player_idx: int) -> Action:
        """Run hybrid MCTS search and return best action."""
        actions = get_legal_actions(root_state)

        if len(actions) == 0:
            raise ValueError("No legal actions available")
        if len(actions) == 1:
            return actions[0]

        # Aggregate action scores across determinizations
        action_scores: Dict[str, Tuple[float, int, Action]] = {}

        for _ in range(self.determinizations):
            # Determinize hidden information
            det_state = root_state.determinize_for_player(player_idx)

            # Run MCTS iterations
            scores = self._run_iterations(det_state, player_idx)

            # Aggregate scores
            for key, (score, visits, action) in scores.items():
                if key in action_scores:
                    old_score, old_visits, _ = action_scores[key]
                    action_scores[key] = (old_score + score, old_visits + visits, action)
                else:
                    action_scores[key] = (score, visits, action)

        # Select best action by visit count (more robust than value)
        if not action_scores:
            return random.choice(actions)

        best_key = max(action_scores.keys(), key=lambda k: action_scores[k][1])
        return action_scores[best_key][2]

    def _run_iterations(self, state: GameState, player_idx: int) -> Dict[str, Tuple[float, int, Action]]:
        """Run MCTS iterations on a determinized state."""
        # Compute priors for root actions
        actions = get_legal_actions(state)
        priors = self.compute_action_priors(state, actions, player_idx)

        root = HybridNode(state, player_idx=player_idx)

        for _ in range(self.iterations):
            node = root

            # Selection
            while node.is_fully_expanded() and not node.is_terminal():
                node = node.select_child(self.exploration)

            # Expansion
            if not node.is_terminal() and node.untried_actions:
                action = self._select_untried_action(node, priors)
                new_state = apply_action(node.state.copy(), action)
                prior = priors.get(self._action_key(action), 1.0 / len(node.untried_actions))

                child = HybridNode(
                    new_state,
                    parent=node,
                    action=action,
                    player_idx=player_idx,
                    prior_probability=prior
                )
                node.children[self._action_key(action)] = child
                node.untried_actions.remove(action)
                node = child

            # Simulation (rollout with heuristic cutoff)
            value = self._simulate(node.state, player_idx)

            # Backpropagation
            while node is not None:
                node.visits += 1
                node.total_value += value
                node = node.parent

        # Collect results
        results = {}
        for key, child in root.children.items():
            results[key] = (child.total_value, child.visits, child.action)

        return results

    def _select_untried_action(self, node: HybridNode, priors: Dict[str, float]) -> Action:
        """Select an untried action, biased by prior probabilities."""
        if not node.untried_actions:
            return None

        # Weight untried actions by their priors
        weights = []
        for action in node.untried_actions:
            key = self._action_key(action)
            weight = priors.get(key, 0.1)
            weights.append(weight)

        total = sum(weights)
        if total == 0:
            return random.choice(node.untried_actions)

        weights = [w / total for w in weights]
        return random.choices(node.untried_actions, weights=weights, k=1)[0]

    def _simulate(self, state: GameState, player_idx: int) -> float:
        """Simulate game with heuristic-guided rollout."""
        sim_state = state.copy()
        depth = 0

        while not sim_state.is_game_over() and depth < self.rollout_depth:
            actions = get_legal_actions(sim_state)
            if not actions:
                break

            # Use evolutionary heuristics for action selection during rollout
            if random.random() < 0.7:  # 70% guided, 30% random for exploration
                action = self._select_heuristic_action(sim_state, actions)
            else:
                action = random.choice(actions)

            sim_state = apply_action(sim_state, action)
            depth += 1

        # Evaluate final state
        if sim_state.winner is not None:
            return 1.0 if sim_state.winner == player_idx else 0.0

        return evaluate_state(sim_state, player_idx)

    def _select_heuristic_action(self, state: GameState, actions: List[Action]) -> Action:
        """Select action using evolutionary heuristics."""
        if not actions:
            return None

        current_player = state.current_player_idx
        best_action = actions[0]
        best_score = float('-inf')

        for action in actions:
            score = self._evaluate_action(state, action, current_player)
            # Add small random noise to break ties
            score += random.random() * 0.01
            if score > best_score:
                best_score = score
                best_action = action

        return best_action


class HybridPlayer:
    """Player that uses hybrid MCTS + Evolutionary AI."""

    def __init__(self, name: str, iterations: int = 500, determinizations: int = 5,
                 weights: Optional[EvolutionaryWeights] = None):
        self.name = name
        self.player_idx = 0
        self.hybrid = HybridMCTS(
            iterations=iterations,
            determinizations=determinizations,
            weights=weights or TRAINED_WEIGHTS
        )

    def choose_action(self, state: GameState, valid_actions: List[Action]) -> Action:
        """Choose action using hybrid search."""
        if len(valid_actions) == 1:
            return valid_actions[0]
        return self.hybrid.search(state, self.player_idx)

    def choose_target(self, state: GameState, valid_targets: List,
                      prompt: str) -> any:
        """Choose target using heuristics."""
        if not valid_targets:
            return None
        if len(valid_targets) == 1:
            return valid_targets[0]

        # Use evolutionary evaluation to pick best target
        return self._evaluate_targets(state, valid_targets, prompt)

    def _evaluate_targets(self, state: GameState, targets: List, prompt: str) -> any:
        """Evaluate targets and pick the best one."""
        # For now, use simple heuristics
        # Could be enhanced with more sophisticated target evaluation

        prompt_lower = prompt.lower()

        if "destroy" in prompt_lower or "sacrifice" in prompt_lower:
            # Pick opponent's best card or own worst card
            best_target = targets[0]
            best_score = float('-inf')

            for target in targets:
                score = self._target_destruction_value(target, state)
                if score > best_score:
                    best_score = score
                    best_target = target

            return best_target

        elif "steal" in prompt_lower:
            # Steal opponent's best card
            best_target = targets[0]
            best_score = float('-inf')

            for target in targets:
                if hasattr(target, 'is_unicorn') and target.is_unicorn():
                    score = 2.0 if target.card_type.name == 'MAGICAL_UNICORN' else 1.0
                    if score > best_score:
                        best_score = score
                        best_target = target

            return best_target

        return random.choice(targets)

    def _target_destruction_value(self, target, state: GameState) -> float:
        """Evaluate value of destroying a target."""
        if not hasattr(target, 'is_unicorn'):
            return 0.0

        value = 0.0

        # Find who owns this card
        for i, player in enumerate(state.players):
            if i == self.player_idx:
                # Own card - negative value to destroy
                if target in player.stable:
                    value = -1.0
                    if target.card_type.name == 'MAGICAL_UNICORN':
                        value = -2.0
            else:
                # Opponent card - positive value to destroy
                if target in player.stable:
                    value = 1.0
                    if target.card_type.name == 'MAGICAL_UNICORN':
                        value = 2.0
                    # Extra value if opponent is close to winning
                    if player.unicorn_count() >= state.unicorns_to_win - 2:
                        value += 1.0

        return value

    def respond_to_neigh_opportunity(self, state: GameState,
                                     card_being_played) -> bool:
        """Decide whether to Neigh using hybrid evaluation."""
        from ai.heuristics import should_neigh

        neigh_value = should_neigh(state, self.player_idx)

        # More aggressive Neighing for Hybrid player
        threshold = 0.4  # Lower threshold than pure evolutionary

        return neigh_value > threshold
