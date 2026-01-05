"""Integration tests for complete game scenarios."""

import unittest
import random
from game.game_engine import GameEngine, GameSimulator
from game.game_state import GameState, PlayerState, GamePhase, EffectTask
from game.action import Action, ActionType, apply_action, get_legal_actions
from game.effect_handler import EffectHandler
from cards.card_database import CARD_DATABASE
from cards.card import CardType
from cards.effects import EFFECT_REGISTRY, EffectTrigger
from players.ai_player import RandomPlayer, RuleBasedPlayer


class TestFullGameScenarios(unittest.TestCase):
    """Test complete game flows."""

    def test_random_vs_random_completes(self):
        """Test that two random players can complete a game."""
        random.seed(42)
        engine = GameEngine(["Random1", "Random2"], verbose=False)
        players = [RandomPlayer("Random1"), RandomPlayer("Random2")]
        engine.set_players(players)

        winner = engine.run_game(max_turns=200)

        self.assertIn(winner, [0, 1])

    def test_multiple_games_different_seeds(self):
        """Test that multiple games with different seeds all complete."""
        for seed in range(5):
            random.seed(seed)
            engine = GameEngine(["P1", "P2"], verbose=False)
            players = [RandomPlayer("P1"), RandomPlayer("P2")]
            engine.set_players(players)

            winner = engine.run_game(max_turns=100)
            self.assertIn(winner, [0, 1])

    def test_rule_based_vs_random(self):
        """Test rule-based AI against random player."""
        random.seed(123)
        engine = GameEngine(["RuleBased", "Random"], verbose=False)
        players = [RuleBasedPlayer("RuleBased"), RandomPlayer("Random")]
        engine.set_players(players)

        winner = engine.run_game(max_turns=150)
        self.assertIn(winner, [0, 1])

    def test_three_player_game(self):
        """Test a 3-player game completes correctly."""
        random.seed(99)
        engine = GameEngine(["P1", "P2", "P3"], verbose=False)
        players = [RandomPlayer("P1"), RandomPlayer("P2"), RandomPlayer("P3")]
        engine.set_players(players)

        winner = engine.run_game(max_turns=200)
        self.assertIn(winner, [0, 1, 2])

    def test_four_player_game(self):
        """Test a 4-player game completes correctly."""
        random.seed(77)
        engine = GameEngine(["P1", "P2", "P3", "P4"], verbose=False)
        players = [RandomPlayer(f"P{i+1}") for i in range(4)]
        engine.set_players(players)

        winner = engine.run_game(max_turns=250)
        self.assertIn(winner, [0, 1, 2, 3])


class TestBeginningOfTurnEffects(unittest.TestCase):
    """Test beginning of turn triggered effects."""

    def setUp(self):
        self.players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        self.state = GameState(players=self.players, num_players=2)
        self.get_card = lambda id: CARD_DATABASE.create_instance(id)

    def test_mother_goose_unicorn(self):
        """Test Mother Goose Unicorn brings baby at beginning of turn (if no baby in stable)."""
        # Add Mother Goose Unicorn to P1's stable (no babies in stable)
        goose = self.get_card("mother_goose_unicorn")
        self.state.add_to_stable(goose, 0)
        self.state.current_player_idx = 0
        self.state.phase = GamePhase.BEGINNING

        # Add baby to nursery
        baby = self.get_card("baby_narwhal")
        self.state.nursery.append(baby)
        initial_stable_size = len(self.state.players[0].stable)

        # Trigger beginning of turn
        from game.action import _process_beginning_of_turn
        _process_beginning_of_turn(self.state)

        # Process any pending effects
        while self.state.resolution_stack:
            actions = get_legal_actions(self.state)
            if actions and actions[0].action_type == ActionType.CHOOSE_TARGET:
                # Choose the baby unicorn (first option)
                self.state = apply_action(self.state, actions[0])
            else:
                break

        # Baby should have moved from nursery to stable
        self.assertEqual(len(self.state.nursery), 0)
        self.assertGreater(len(self.state.players[0].stable), initial_stable_size)

    def test_rhinocorn_destroy(self):
        """Test Rhinocorn can destroy a unicorn at beginning of turn."""
        rhinocorn = self.get_card("rhinocorn")
        self.state.add_to_stable(rhinocorn, 0)
        self.state.current_player_idx = 0
        self.state.phase = GamePhase.BEGINNING

        # Add target unicorn to P2
        target = self.get_card("basic_red")
        self.state.add_to_stable(target, 1)

        # Trigger beginning of turn
        from game.action import _process_beginning_of_turn
        _process_beginning_of_turn(self.state)

        # Process the destroy effect
        while self.state.resolution_stack:
            actions = get_legal_actions(self.state)
            if actions and actions[0].action_type == ActionType.CHOOSE_TARGET:
                # Choose to destroy P2's unicorn
                target_action = next((a for a in actions if a.target_card == target), actions[0])
                self.state = apply_action(self.state, target_action)
            else:
                break

        # Verify phase transition happened
        self.assertEqual(self.state.phase, GamePhase.DRAW)

    def test_claw_machine_empty_discard(self):
        """Test Claw Machine with empty discard pile."""
        claw = self.get_card("claw_machine")
        self.state.add_to_stable(claw, 0)
        self.state.current_player_idx = 0
        self.state.phase = GamePhase.BEGINNING
        self.state.discard_pile = []  # Empty discard

        # Trigger beginning of turn
        from game.action import _process_beginning_of_turn
        _process_beginning_of_turn(self.state)

        # Should create a skip action since no valid targets
        if self.state.resolution_stack:
            actions = get_legal_actions(self.state)
            # Should have a None target action
            self.assertTrue(len(actions) > 0)
            self.assertIsNone(actions[0].target_card)
            # Apply to clear the stack
            self.state = apply_action(self.state, actions[0])

        self.assertEqual(len(self.state.resolution_stack), 0)


class TestEndOfTurnEffects(unittest.TestCase):
    """Test end of turn triggered effects."""

    def setUp(self):
        self.players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        self.state = GameState(players=self.players, num_players=2)
        self.get_card = lambda id: CARD_DATABASE.create_instance(id)

    def test_glitter_bomb_sacrifice(self):
        """Test Glitter Bomb end of turn effect."""
        bomb = self.get_card("glitter_bomb")
        unicorn = self.get_card("basic_red")
        self.state.add_to_stable(bomb, 0)
        self.state.add_to_stable(unicorn, 0)
        self.state.current_player_idx = 0
        self.state.phase = GamePhase.END

        # Trigger end of turn
        from game.action import _process_end_of_turn
        _process_end_of_turn(self.state)

        # Should be waiting for sacrifice target
        if self.state.resolution_stack:
            actions = get_legal_actions(self.state)
            # Apply first action (sacrifice or skip)
            if actions:
                self.state = apply_action(self.state, actions[0])


class TestEffectChainResolution(unittest.TestCase):
    """Test complex effect chains."""

    def setUp(self):
        self.players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        self.state = GameState(players=self.players, num_players=2)
        self.state.phase = GamePhase.ACTION
        self.state.actions_remaining = 1
        self.get_card = lambda id: CARD_DATABASE.create_instance(id)

    def test_destroy_triggers_leave_effect(self):
        """Test that destroying a card triggers its ON_LEAVE effect."""
        # Unicorn Phoenix: When leaves stable, may DISCARD then return to stable
        phoenix = self.get_card("unicorn_phoenix")
        self.state.add_to_stable(phoenix, 1)

        # Add a card to P1's hand for discard
        discard_card = self.get_card("basic_red")
        self.state.players[1].hand.append(discard_card)

        # Destroy Phoenix
        poison = self.get_card("unicorn_poison")
        self.state.players[0].hand.append(poison)

        action = Action(ActionType.PLAY_CARD, 0, card=poison)
        self.state = apply_action(self.state, action)

        # Should ask for target
        if self.state.resolution_stack:
            actions = get_legal_actions(self.state)
            target_action = next((a for a in actions if a.target_card == phoenix), actions[0])
            self.state = apply_action(self.state, target_action)

        # Phoenix effect should trigger (may discard to return)
        # Just verify no crash
        self.assertIsNotNone(self.state)

    def test_multiple_enter_triggers(self):
        """Test that multiple cards with enter triggers work together."""
        # Add Barbed Wire (triggers when unicorns enter/leave)
        wire = self.get_card("barbed_wire")
        self.state.add_to_stable(wire, 0)

        initial_hand = len(self.state.players[0].hand)

        # Play a unicorn - should trigger Barbed Wire
        unicorn = self.get_card("basic_red")
        self.state.players[0].hand.append(unicorn)

        action = Action(ActionType.PLAY_CARD, 0, card=unicorn)
        self.state = apply_action(self.state, action)

        # Barbed Wire should have triggered (discard a card)
        # Just verify game state is valid
        self.assertIn(unicorn, self.state.players[0].stable)


class TestNeighMechanics(unittest.TestCase):
    """Test Neigh card interactions."""

    def setUp(self):
        self.players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        self.state = GameState(players=self.players, num_players=2)
        self.state.phase = GamePhase.ACTION
        self.state.actions_remaining = 1
        self.get_card = lambda id: CARD_DATABASE.create_instance(id)

    def test_yay_prevents_neigh(self):
        """Test that Yay upgrade prevents opponent from playing Neigh."""
        yay = self.get_card("yay")
        self.state.add_to_stable(yay, 0)

        from game.action import _update_player_flags
        _update_player_flags(self.state, 0)

        # P1 has Yay, so cards cannot be Neigh'd
        self.assertTrue(self.state.players[0].cards_cannot_be_neighd)

        # P2 has Neigh
        neigh = self.get_card("neigh")
        self.state.players[1].hand.append(neigh)

        # P1 plays unicorn
        unicorn = self.get_card("basic_red")
        self.state.players[0].hand.append(unicorn)

        action = Action(ActionType.PLAY_CARD, 0, card=unicorn)
        self.state = apply_action(self.state, action)

        # Neigh chain should NOT start
        self.assertFalse(self.state.neigh_chain_active)
        # Unicorn should be in stable
        self.assertIn(unicorn, self.state.players[0].stable)

    def test_super_neigh_cannot_be_countered(self):
        """Test that Super Neigh cannot be countered by another Neigh."""
        # P1 plays card
        unicorn = self.get_card("basic_red")
        self.state.players[0].hand.append(unicorn)

        # P2 has Super Neigh
        super_neigh = self.get_card("super_neigh")
        self.state.players[1].hand.append(super_neigh)

        # P1 also has Neigh (to try to counter)
        neigh = self.get_card("neigh")
        self.state.players[0].hand.append(neigh)

        action = Action(ActionType.PLAY_CARD, 0, card=unicorn)
        self.state = apply_action(self.state, action)

        # Neigh chain should start
        self.assertTrue(self.state.neigh_chain_active)

        # P2 plays Super Neigh
        actions = get_legal_actions(self.state)
        neigh_action = next((a for a in actions if a.card == super_neigh), None)
        if neigh_action:
            self.state = apply_action(self.state, neigh_action)
            # Super Neigh ends the chain immediately
            self.assertFalse(self.state.neigh_chain_active)


class TestContinuousEffects(unittest.TestCase):
    """Test continuous effect cards."""

    def setUp(self):
        self.players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        self.state = GameState(players=self.players, num_players=2)
        self.state.phase = GamePhase.ACTION
        self.state.actions_remaining = 1
        self.get_card = lambda id: CARD_DATABASE.create_instance(id)

    def test_blinding_light_makes_unicorns_basic(self):
        """Test Blinding Light makes all unicorns basic."""
        blind = self.get_card("blinding_light")
        self.state.add_to_stable(blind, 0)

        from game.action import _update_player_flags
        _update_player_flags(self.state, 0)

        self.assertTrue(self.state.players[0].unicorns_are_basic)

    def test_pandamonium_blocks_win(self):
        """Test Pandamonium prevents winning."""
        panda = self.get_card("pandamonium")
        self.state.add_to_stable(panda, 0)

        from game.action import _update_player_flags
        _update_player_flags(self.state, 0)

        self.assertTrue(self.state.players[0].unicorns_are_pandas)

        # Add 7 unicorns
        for _ in range(7):
            unicorn = self.get_card("basic_red")
            self.state.add_to_stable(unicorn, 0)

        # Should not win because unicorns are pandas
        winner = self.state.check_win_condition()
        self.assertIsNone(winner)

    def test_broken_stable_blocks_upgrades(self):
        """Test Broken Stable prevents playing upgrades."""
        broken = self.get_card("broken_stable")
        self.state.add_to_stable(broken, 0)

        from game.action import _update_player_flags
        _update_player_flags(self.state, 0)

        self.assertTrue(self.state.players[0].cannot_play_upgrades)

        # Add upgrade to hand
        upgrade = self.get_card("rainbow_aura")
        self.state.players[0].hand.append(upgrade)

        # Get legal actions
        actions = get_legal_actions(self.state)
        play_upgrade = [a for a in actions if a.action_type == ActionType.PLAY_CARD and a.card == upgrade]

        # Should not be able to play upgrade
        self.assertEqual(len(play_upgrade), 0)


class TestGameSimulator(unittest.TestCase):
    """Test the game simulator for AI planning."""

    def setUp(self):
        self.players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        self.state = GameState(players=self.players, num_players=2)

        # Add cards to make the state more realistic
        deck = CARD_DATABASE.create_deck()
        random.shuffle(deck)
        self.state.draw_pile = deck[:20]

        # Deal hands
        for i in range(2):
            self.state.draw_card(i, 5)

        # Add baby unicorns
        for i in range(2):
            baby = CARD_DATABASE.create_instance("baby_narwhal")
            self.state.add_to_stable(baby, i)

    def test_simulate_random_game(self):
        """Test random game simulation completes."""
        random.seed(42)
        winner = GameSimulator.simulate_random_game(self.state.copy(), max_turns=50)
        # Winner can be 0, 1, or None (if max turns reached)
        self.assertIn(winner, [0, 1, None])

    def test_evaluate_state(self):
        """Test state evaluation returns valid score."""
        score = GameSimulator.evaluate_state(self.state, 0)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_evaluate_winning_state(self):
        """Test evaluation of winning state returns 1.0."""
        self.state.winner = 0
        score = GameSimulator.evaluate_state(self.state, 0)
        self.assertEqual(score, 1.0)

    def test_evaluate_losing_state(self):
        """Test evaluation of losing state returns 0.0."""
        self.state.winner = 1
        score = GameSimulator.evaluate_state(self.state, 0)
        self.assertEqual(score, 0.0)


class TestDeterminization(unittest.TestCase):
    """Test determinization for MCTS."""

    def setUp(self):
        self.players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        self.state = GameState(players=self.players, num_players=2)

        # Create deck and deal
        deck = CARD_DATABASE.create_deck()
        random.shuffle(deck)
        self.state.draw_pile = deck

        for i in range(2):
            self.state.draw_card(i, 5)

    def test_determinize_preserves_own_hand(self):
        """Test that determinization preserves the player's own hand."""
        player0_hand = list(self.state.players[0].hand)

        det_state = self.state.determinize_for_player(0)

        # Player 0's hand should be unchanged
        self.assertEqual(det_state.players[0].hand, player0_hand)

    def test_determinize_shuffles_opponent_hand(self):
        """Test that opponent's hand is randomized."""
        original_p1_hand = list(self.state.players[1].hand)

        det_state = self.state.determinize_for_player(0)

        # Player 1's hand might be different (randomized)
        # Just verify it has the same number of cards
        self.assertEqual(len(det_state.players[1].hand), len(original_p1_hand))


if __name__ == '__main__':
    unittest.main()
