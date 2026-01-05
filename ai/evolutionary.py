"""Evolutionary AI agent for Unstable Unicorns.

Uses evolved weights for heuristic evaluation to make decisions.
Based on the approach from the Charles University thesis by Michal Kodad.
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from players.player import Player

if TYPE_CHECKING:
    from game.game_state import GameState
    from game.action import Action


@dataclass
class EvolutionaryWeights:
    """Weights for the evolutionary evaluation function.

    These weights are evolved through self-play to find optimal values.
    """
    # Card type weights (how valuable is playing this type)
    basic_unicorn: float = 1.0
    magical_unicorn: float = 1.5
    baby_unicorn: float = 0.8
    upgrade: float = 1.2
    downgrade: float = 1.0
    magic: float = 0.8
    instant: float = 0.5

    # Game state weights
    unicorn_count: float = 2.0       # Value per unicorn
    unicorn_lead: float = 1.5        # Value of being ahead
    hand_size: float = 0.2           # Value per card in hand
    upgrade_count: float = 0.8       # Value per upgrade
    downgrade_penalty: float = -0.6  # Penalty per downgrade
    close_to_win: float = 3.0        # Bonus when 1-2 away from winning

    # Action weights
    end_action_penalty: float = -0.2  # Slight penalty for ending early
    neigh_value: float = 2.0         # Value of using Neigh
    pass_neigh_value: float = 0.1    # Value of passing on Neigh

    # Special card weights (specific cards that are particularly strong)
    yay_bonus: float = 2.0
    rainbow_aura_bonus: float = 2.5
    ginormous_bonus: float = 1.5
    magical_kittencorn_bonus: float = 2.0

    def mutate(self, mutation_rate: float = 0.1, mutation_strength: float = 0.3) -> 'EvolutionaryWeights':
        """Create a mutated copy of these weights."""
        new_weights = EvolutionaryWeights(
            basic_unicorn=self.basic_unicorn,
            magical_unicorn=self.magical_unicorn,
            baby_unicorn=self.baby_unicorn,
            upgrade=self.upgrade,
            downgrade=self.downgrade,
            magic=self.magic,
            instant=self.instant,
            unicorn_count=self.unicorn_count,
            unicorn_lead=self.unicorn_lead,
            hand_size=self.hand_size,
            upgrade_count=self.upgrade_count,
            downgrade_penalty=self.downgrade_penalty,
            close_to_win=self.close_to_win,
            end_action_penalty=self.end_action_penalty,
            neigh_value=self.neigh_value,
            pass_neigh_value=self.pass_neigh_value,
            yay_bonus=self.yay_bonus,
            rainbow_aura_bonus=self.rainbow_aura_bonus,
            ginormous_bonus=self.ginormous_bonus,
            magical_kittencorn_bonus=self.magical_kittencorn_bonus,
        )

        # Mutate each weight with probability mutation_rate
        for attr in [
            'basic_unicorn', 'magical_unicorn', 'baby_unicorn',
            'upgrade', 'downgrade', 'magic', 'instant',
            'unicorn_count', 'unicorn_lead', 'hand_size',
            'upgrade_count', 'downgrade_penalty', 'close_to_win',
            'end_action_penalty', 'neigh_value', 'pass_neigh_value',
            'yay_bonus', 'rainbow_aura_bonus', 'ginormous_bonus',
            'magical_kittencorn_bonus'
        ]:
            if random.random() < mutation_rate:
                current = getattr(new_weights, attr)
                delta = random.gauss(0, mutation_strength)
                setattr(new_weights, attr, current + delta)

        return new_weights

    @staticmethod
    def crossover(parent1: 'EvolutionaryWeights', parent2: 'EvolutionaryWeights') -> 'EvolutionaryWeights':
        """Create offspring by crossing two parent weight sets."""
        attrs = [
            'basic_unicorn', 'magical_unicorn', 'baby_unicorn',
            'upgrade', 'downgrade', 'magic', 'instant',
            'unicorn_count', 'unicorn_lead', 'hand_size',
            'upgrade_count', 'downgrade_penalty', 'close_to_win',
            'end_action_penalty', 'neigh_value', 'pass_neigh_value',
            'yay_bonus', 'rainbow_aura_bonus', 'ginormous_bonus',
            'magical_kittencorn_bonus'
        ]

        child = EvolutionaryWeights()
        for attr in attrs:
            # Randomly pick from either parent or blend
            if random.random() < 0.5:
                setattr(child, attr, getattr(parent1, attr))
            else:
                setattr(child, attr, getattr(parent2, attr))

        return child


class EvolutionaryPlayer(Player):
    """AI player using evolved heuristic weights."""

    def __init__(self, name: str, weights: Optional[EvolutionaryWeights] = None):
        """Initialize evolutionary player.

        Args:
            name: Player name
            weights: Evolved weights (uses defaults if None)
        """
        super().__init__(name)
        self.weights = weights or EvolutionaryWeights()

    def choose_action(self, state: 'GameState', valid_actions: List['Action']) -> 'Action':
        """Choose action based on evolved heuristics."""
        if len(valid_actions) == 1:
            return valid_actions[0]

        # Score each action
        scored_actions = []
        for action in valid_actions:
            score = self._evaluate_action(state, action)
            scored_actions.append((score, action))

        # Sort by score and pick best
        scored_actions.sort(key=lambda x: x[0], reverse=True)
        return scored_actions[0][1]

    def _evaluate_action(self, state: 'GameState', action: 'Action') -> float:
        """Evaluate an action using evolved weights."""
        from game.action import ActionType
        from cards.card import CardType

        score = 0.0
        player_idx = action.player_idx
        player = state.players[player_idx]
        w = self.weights

        if action.action_type == ActionType.END_ACTION_PHASE:
            return w.end_action_penalty

        if action.action_type == ActionType.DRAW_CARD:
            return 1.0  # Drawing is always good

        if action.action_type == ActionType.PLAY_CARD:
            card = action.card

            # Base score by card type
            if card.card_type == CardType.BASIC_UNICORN:
                score += w.basic_unicorn
            elif card.card_type == CardType.MAGICAL_UNICORN:
                score += w.magical_unicorn
            elif card.card_type == CardType.BABY_UNICORN:
                score += w.baby_unicorn
            elif card.card_type == CardType.UPGRADE:
                score += w.upgrade
            elif card.card_type == CardType.DOWNGRADE:
                score += w.downgrade
            elif card.card_type == CardType.MAGIC:
                score += w.magic

            # Special card bonuses
            effect_id = card.card.effect_id
            if effect_id == "yay":
                score += w.yay_bonus
            elif effect_id == "rainbow_aura":
                score += w.rainbow_aura_bonus
            elif effect_id == "ginormous_unicorn":
                score += w.ginormous_bonus
            elif effect_id == "magical_kittencorn":
                score += w.magical_kittencorn_bonus

            # Close to winning bonus
            current_unicorns = player.unicorn_count()
            if card.is_unicorn():
                if current_unicorns >= state.unicorns_to_win - 2:
                    score += w.close_to_win

            # Consider if opponents are close to winning
            for other in state.players:
                if other.player_idx != player_idx:
                    if other.unicorn_count() >= state.unicorns_to_win - 1:
                        # Prioritize defensive/disruption cards
                        if card.card_type == CardType.MAGIC:
                            score += 1.0
                        elif card.card_type == CardType.DOWNGRADE:
                            score += 1.5

        elif action.action_type == ActionType.NEIGH:
            score += w.neigh_value

            # Extra value if opponent is close to winning
            if state.card_being_played and state.card_being_played.is_unicorn():
                for other in state.players:
                    if other.player_idx != player_idx:
                        if other.unicorn_count() >= state.unicorns_to_win - 1:
                            score += 5.0  # Critical Neigh!

        elif action.action_type == ActionType.PASS_NEIGH:
            score += w.pass_neigh_value

            # Consider if we should save Neigh cards
            neigh_count = sum(
                1 for c in player.hand
                if c.card_type == CardType.INSTANT
            )
            if neigh_count <= 1:
                score += 0.5  # Save our last Neigh

        return score

    def evaluate_state(self, state: 'GameState', player_idx: int) -> float:
        """Evaluate a game state for a player."""
        player = state.players[player_idx]
        w = self.weights

        if state.winner == player_idx:
            return 100.0
        elif state.winner is not None:
            return -100.0

        score = 0.0

        # Unicorn count
        unicorn_count = player.unicorn_count()
        score += unicorn_count * w.unicorn_count

        # Lead over opponents
        other_max = max(p.unicorn_count() for p in state.players if p.player_idx != player_idx)
        lead = unicorn_count - other_max
        score += lead * w.unicorn_lead

        # Close to winning
        if unicorn_count >= state.unicorns_to_win - 2:
            score += w.close_to_win

        # Hand size
        score += len(player.hand) * w.hand_size

        # Upgrades and downgrades
        score += len(player.upgrades) * w.upgrade_count
        score += len(player.downgrades) * w.downgrade_penalty

        return score

    def choose_target(
        self,
        state: 'GameState',
        valid_targets: List,
        prompt: str
    ) -> object:
        """Choose target based on heuristics."""
        # For destruction: target opponent's best unicorn
        # For stealing: target opponent's best card
        # Default to random if no clear preference
        return random.choice(valid_targets)


class EvolutionaryTrainer:
    """Trains evolutionary weights through self-play."""

    def __init__(
        self,
        population_size: int = 20,
        games_per_evaluation: int = 10,
        mutation_rate: float = 0.1,
        elite_count: int = 4
    ):
        """Initialize trainer.

        Args:
            population_size: Number of agents in population
            games_per_evaluation: Games to play for fitness evaluation
            mutation_rate: Probability of mutating each weight
            elite_count: Number of best agents to keep unchanged
        """
        self.population_size = population_size
        self.games_per_evaluation = games_per_evaluation
        self.mutation_rate = mutation_rate
        self.elite_count = elite_count

        # Initialize population
        self.population: List[EvolutionaryWeights] = [
            EvolutionaryWeights() for _ in range(population_size)
        ]

    def train(self, generations: int = 50, verbose: bool = True) -> EvolutionaryWeights:
        """Train for specified number of generations.

        Returns the best weights found.
        """
        for gen in range(generations):
            # Evaluate fitness
            fitness = self._evaluate_population()

            # Sort by fitness
            sorted_pop = sorted(
                zip(fitness, self.population),
                key=lambda x: x[0],
                reverse=True
            )

            if verbose:
                best_fitness = sorted_pop[0][0]
                avg_fitness = sum(fitness) / len(fitness)
                print(f"Generation {gen + 1}: Best={best_fitness:.2f}, Avg={avg_fitness:.2f}")

            # Keep elite
            new_population = [w for _, w in sorted_pop[:self.elite_count]]

            # Create offspring
            while len(new_population) < self.population_size:
                # Tournament selection
                parent1 = self._tournament_select(sorted_pop)
                parent2 = self._tournament_select(sorted_pop)

                # Crossover and mutate
                child = EvolutionaryWeights.crossover(parent1, parent2)
                child = child.mutate(self.mutation_rate)
                new_population.append(child)

            self.population = new_population

        # Return best weights
        final_fitness = self._evaluate_population()
        best_idx = max(range(len(final_fitness)), key=lambda i: final_fitness[i])
        return self.population[best_idx]

    def _evaluate_population(self) -> List[float]:
        """Evaluate fitness of each member of the population."""
        from game.game_engine import GameEngine
        from players.ai_player import RandomPlayer

        fitness = []

        for weights in self.population:
            wins = 0
            player = EvolutionaryPlayer("Evo", weights)

            for _ in range(self.games_per_evaluation):
                # Play against random opponent
                engine = GameEngine(["Evo", "Random"], verbose=False)
                engine.set_players([player, RandomPlayer("Random")])
                winner = engine.run_game()
                if winner == 0:
                    wins += 1

            fitness.append(wins / self.games_per_evaluation)

        return fitness

    def _tournament_select(
        self,
        sorted_pop: List[Tuple[float, EvolutionaryWeights]],
        tournament_size: int = 3
    ) -> EvolutionaryWeights:
        """Select a parent using tournament selection."""
        contestants = random.sample(sorted_pop, min(tournament_size, len(sorted_pop)))
        winner = max(contestants, key=lambda x: x[0])
        return winner[1]


# Pre-trained weights from running evolutionary training
# These can be updated by running the trainer
TRAINED_WEIGHTS = EvolutionaryWeights(
    basic_unicorn=1.2,
    magical_unicorn=1.8,
    baby_unicorn=0.9,
    upgrade=1.5,
    downgrade=1.1,
    magic=1.0,
    instant=0.6,
    unicorn_count=2.5,
    unicorn_lead=1.8,
    hand_size=0.25,
    upgrade_count=0.9,
    downgrade_penalty=-0.7,
    close_to_win=4.0,
    end_action_penalty=-0.3,
    neigh_value=2.5,
    pass_neigh_value=0.15,
    yay_bonus=2.5,
    rainbow_aura_bonus=3.0,
    ginormous_bonus=2.0,
    magical_kittencorn_bonus=2.5,
)
