"""Unit tests for AI players."""

import unittest
from game.game_state import GameState, PlayerState, GamePhase
from game.action import Action, ActionType, get_legal_actions
from game.game_engine import GameEngine
from players.ai_player import RandomPlayer, RuleBasedPlayer
from ai.mcts import MCTS, MCTSPlayer
from ai.evolutionary import EvolutionaryPlayer, EvolutionaryWeights, TRAINED_WEIGHTS
from ai.heuristics import evaluate_state, evaluate_card_value, should_neigh
from cards.card_database import CARD_DATABASE


class TestRandomPlayer(unittest.TestCase):
    """Tests for RandomPlayer."""

    def test_chooses_action(self):
        """Test that random player chooses an action."""
        player = RandomPlayer("Random")
        players = [
            PlayerState(player_idx=0, name="Random"),
            PlayerState(player_idx=1, name="Other"),
        ]
        state = GameState(players=players, num_players=2)
        state.phase = GamePhase.ACTION
        state.actions_remaining = 1

        actions = get_legal_actions(state)
        chosen = player.choose_action(state, actions)

        self.assertIn(chosen, actions)

    def test_chooses_target(self):
        """Test that random player chooses a target."""
        player = RandomPlayer("Random")
        players = [PlayerState(player_idx=0, name="P1")]
        state = GameState(players=players, num_players=1)

        targets = ["target1", "target2", "target3"]
        chosen = player.choose_target(state, targets, "Pick one")

        self.assertIn(chosen, targets)


class TestRuleBasedPlayer(unittest.TestCase):
    """Tests for RuleBasedPlayer."""

    def test_prefers_unicorns(self):
        """Test that rule-based player prefers playing unicorns."""
        player = RuleBasedPlayer("RuleBased")
        players = [
            PlayerState(player_idx=0, name="RuleBased"),
            PlayerState(player_idx=1, name="Other"),
        ]
        state = GameState(players=players, num_players=2)
        state.phase = GamePhase.ACTION
        state.actions_remaining = 1
        state.players[0].cards_cannot_be_neighd = True

        # Add both a unicorn and magic card
        unicorn = CARD_DATABASE.create_instance("basic_red")
        magic = CARD_DATABASE.create_instance("good_deal")
        state.players[0].hand.append(magic)
        state.players[0].hand.append(unicorn)

        actions = get_legal_actions(state)
        chosen = player.choose_action(state, actions)

        # Should prefer unicorn
        if chosen.action_type == ActionType.PLAY_CARD:
            self.assertTrue(chosen.card.is_unicorn())

    def test_considers_neigh_value(self):
        """Test that rule-based player considers Neigh value."""
        player = RuleBasedPlayer("RuleBased")

        # Set up Neigh chain scenario
        players = [
            PlayerState(player_idx=0, name="Playing"),
            PlayerState(player_idx=1, name="RuleBased"),
        ]
        state = GameState(players=players, num_players=2)
        state.neigh_chain_active = True
        state.card_being_played = CARD_DATABASE.create_instance("basic_red")
        state.current_player_idx = 0

        # Give player Neigh cards
        neigh = CARD_DATABASE.create_instance("neigh")
        state.players[1].hand.append(neigh)

        actions = get_legal_actions(state)
        if actions:
            chosen = player.choose_action(state, actions)
            self.assertIsNotNone(chosen)


class TestMCTS(unittest.TestCase):
    """Tests for MCTS algorithm."""

    def test_search_returns_action(self):
        """Test that MCTS search returns a valid action."""
        mcts = MCTS(iterations=50, determinizations=2)

        players = [
            PlayerState(player_idx=0, name="MCTS"),
            PlayerState(player_idx=1, name="Other"),
        ]
        state = GameState(players=players, num_players=2)
        state.draw_pile = CARD_DATABASE.create_deck()
        state.phase = GamePhase.ACTION
        state.actions_remaining = 1

        # Add some cards
        state.players[0].hand.append(CARD_DATABASE.create_instance("basic_red"))

        action = mcts.search(state, 0)

        self.assertIsNotNone(action)
        self.assertIsInstance(action, Action)

    def test_single_action_returns_immediately(self):
        """Test that single action is returned without search."""
        mcts = MCTS(iterations=1000)  # High iterations

        players = [PlayerState(player_idx=0, name="MCTS")]
        state = GameState(players=players, num_players=1)
        state.phase = GamePhase.ACTION
        state.actions_remaining = 1

        # Only end action available
        actions = get_legal_actions(state)
        self.assertEqual(len(actions), 1)

        action = mcts.search(state, 0)
        self.assertEqual(action.action_type, ActionType.END_ACTION_PHASE)


class TestMCTSPlayer(unittest.TestCase):
    """Tests for MCTSPlayer."""

    def test_can_play_game(self):
        """Test that MCTS player can complete a game."""
        engine = GameEngine(["MCTS", "Random"], verbose=False)
        mcts_player = MCTSPlayer("MCTS", iterations=30, determinizations=2)
        random_player = RandomPlayer("Random")
        engine.set_players([mcts_player, random_player])

        winner = engine.run_game(max_turns=100)

        self.assertIn(winner, [0, 1])


class TestEvolutionaryWeights(unittest.TestCase):
    """Tests for EvolutionaryWeights."""

    def test_default_weights(self):
        """Test default weight values."""
        weights = EvolutionaryWeights()

        self.assertGreater(weights.magical_unicorn, weights.basic_unicorn)
        self.assertGreater(weights.unicorn_count, 0)
        self.assertLess(weights.downgrade_penalty, 0)

    def test_mutate(self):
        """Test weight mutation."""
        weights = EvolutionaryWeights()
        original_value = weights.unicorn_count

        # Mutate with high rate
        mutated = weights.mutate(mutation_rate=1.0, mutation_strength=0.5)

        # At least some weights should change
        self.assertNotEqual(
            (weights.unicorn_count, weights.magical_unicorn),
            (mutated.unicorn_count, mutated.magical_unicorn)
        )

    def test_crossover(self):
        """Test weight crossover."""
        parent1 = EvolutionaryWeights()
        parent1.unicorn_count = 10.0
        parent1.magical_unicorn = 5.0

        parent2 = EvolutionaryWeights()
        parent2.unicorn_count = 0.0
        parent2.magical_unicorn = 0.0

        child = EvolutionaryWeights.crossover(parent1, parent2)

        # Child values should come from either parent
        self.assertIn(child.unicorn_count, [10.0, 0.0])
        self.assertIn(child.magical_unicorn, [5.0, 0.0])


class TestEvolutionaryPlayer(unittest.TestCase):
    """Tests for EvolutionaryPlayer."""

    def test_uses_trained_weights(self):
        """Test that player uses trained weights."""
        player = EvolutionaryPlayer("Evo", weights=TRAINED_WEIGHTS)

        self.assertEqual(player.weights, TRAINED_WEIGHTS)

    def test_can_play_game(self):
        """Test that evolutionary player can complete a game."""
        engine = GameEngine(["Evo", "Random"], verbose=False)
        evo_player = EvolutionaryPlayer("Evo", weights=TRAINED_WEIGHTS)
        random_player = RandomPlayer("Random")
        engine.set_players([evo_player, random_player])

        winner = engine.run_game(max_turns=100)

        self.assertIn(winner, [0, 1])


class TestHeuristics(unittest.TestCase):
    """Tests for heuristic evaluation functions."""

    def test_evaluate_winning_state(self):
        """Test evaluation of winning state."""
        players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        state = GameState(players=players, num_players=2)
        state.winner = 0

        self.assertEqual(evaluate_state(state, 0), 1.0)
        self.assertEqual(evaluate_state(state, 1), 0.0)

    def test_evaluate_progress(self):
        """Test that more unicorns = higher score."""
        players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        state = GameState(players=players, num_players=2)

        # No unicorns
        score_0 = evaluate_state(state, 0)

        # Add unicorns
        for i in range(3):
            state.players[0].stable.append(
                CARD_DATABASE.create_instance("basic_red")
            )

        score_3 = evaluate_state(state, 0)

        self.assertGreater(score_3, score_0)

    def test_should_neigh_critical(self):
        """Test Neigh value for critical situations."""
        players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        state = GameState(players=players, num_players=2)

        # P1 is close to winning
        for i in range(6):
            state.players[0].stable.append(
                CARD_DATABASE.create_instance("basic_red")
            )

        # P1 is playing a unicorn
        state.card_being_played = CARD_DATABASE.create_instance("basic_blue")

        # Give P2 a Neigh
        state.players[1].hand.append(CARD_DATABASE.create_instance("neigh"))

        neigh_value = should_neigh(state, 1)

        # Should strongly recommend Neighing
        self.assertGreater(neigh_value, 1.0)


if __name__ == "__main__":
    unittest.main()
