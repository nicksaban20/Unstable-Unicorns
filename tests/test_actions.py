"""Unit tests for action system."""

import unittest
from game.game_state import GameState, PlayerState, GamePhase
from game.action import Action, ActionType, get_legal_actions, apply_action
from cards.card_database import CARD_DATABASE
from cards.card import CardType


class TestAction(unittest.TestCase):
    """Tests for Action class."""

    def test_action_creation(self):
        """Test basic action creation."""
        action = Action(
            action_type=ActionType.DRAW_CARD,
            player_idx=0
        )

        self.assertEqual(action.action_type, ActionType.DRAW_CARD)
        self.assertEqual(action.player_idx, 0)
        self.assertIsNone(action.card)

    def test_action_with_card(self):
        """Test action with card."""
        card = CARD_DATABASE.create_instance("rhinocorn")
        action = Action(
            action_type=ActionType.PLAY_CARD,
            player_idx=0,
            card=card
        )

        self.assertEqual(action.card, card)

    def test_action_repr(self):
        """Test action string representation."""
        action = Action(action_type=ActionType.DRAW_CARD, player_idx=0)
        self.assertEqual(str(action), "Draw")

        action = Action(action_type=ActionType.END_ACTION_PHASE, player_idx=0)
        self.assertEqual(str(action), "EndAction")


class TestGetLegalActions(unittest.TestCase):
    """Tests for get_legal_actions function."""

    def setUp(self):
        """Set up test game state."""
        self.players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        self.state = GameState(players=self.players, num_players=2)
        self.state.draw_pile = CARD_DATABASE.create_deck()

    def test_draw_phase_actions(self):
        """Test actions available in draw phase."""
        self.state.phase = GamePhase.DRAW

        actions = get_legal_actions(self.state)

        # Should be able to draw
        self.assertTrue(any(a.action_type == ActionType.DRAW_CARD for a in actions))

    def test_action_phase_with_empty_hand(self):
        """Test actions with empty hand."""
        self.state.phase = GamePhase.ACTION
        self.state.actions_remaining = 1

        actions = get_legal_actions(self.state)

        # Can only end action phase
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].action_type, ActionType.END_ACTION_PHASE)

    def test_action_phase_with_playable_cards(self):
        """Test actions with playable cards in hand."""
        self.state.phase = GamePhase.ACTION
        self.state.actions_remaining = 1

        # Add a unicorn to hand
        unicorn = CARD_DATABASE.create_instance("basic_red")
        self.state.players[0].hand.append(unicorn)

        actions = get_legal_actions(self.state)

        # Should be able to play or end
        self.assertGreater(len(actions), 1)
        play_actions = [a for a in actions if a.action_type == ActionType.PLAY_CARD]
        self.assertEqual(len(play_actions), 1)
        self.assertEqual(play_actions[0].card, unicorn)

    def test_instant_not_playable_in_action_phase(self):
        """Test that instant cards can't be played normally."""
        self.state.phase = GamePhase.ACTION
        self.state.actions_remaining = 1

        # Add a Neigh to hand
        neigh = CARD_DATABASE.create_instance("neigh")
        self.state.players[0].hand.append(neigh)

        actions = get_legal_actions(self.state)

        # Neigh should not be playable
        play_actions = [a for a in actions if a.action_type == ActionType.PLAY_CARD]
        self.assertEqual(len(play_actions), 0)

    def test_broken_stable_blocks_upgrades(self):
        """Test that Broken Stable prevents playing upgrades."""
        self.state.phase = GamePhase.ACTION
        self.state.actions_remaining = 1
        self.state.players[0].cannot_play_upgrades = True

        # Add an upgrade to hand
        upgrade = CARD_DATABASE.create_instance("yay")
        self.state.players[0].hand.append(upgrade)

        actions = get_legal_actions(self.state)

        # Upgrade should not be playable
        play_actions = [a for a in actions if a.action_type == ActionType.PLAY_CARD]
        self.assertEqual(len(play_actions), 0)


class TestApplyAction(unittest.TestCase):
    """Tests for apply_action function."""

    def setUp(self):
        """Set up test game state."""
        self.players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        self.state = GameState(players=self.players, num_players=2)
        self.state.draw_pile = CARD_DATABASE.create_deck()

    def test_draw_card_action(self):
        """Test drawing a card."""
        self.state.phase = GamePhase.DRAW
        initial_hand = len(self.state.players[0].hand)
        initial_deck = len(self.state.draw_pile)

        action = Action(action_type=ActionType.DRAW_CARD, player_idx=0)
        self.state = apply_action(self.state, action)

        self.assertEqual(len(self.state.players[0].hand), initial_hand + 1)
        self.assertEqual(len(self.state.draw_pile), initial_deck - 1)
        self.assertEqual(self.state.phase, GamePhase.ACTION)

    def test_play_unicorn(self):
        """Test playing a unicorn card."""
        self.state.phase = GamePhase.ACTION
        self.state.actions_remaining = 1

        # Add unicorn to hand and disable Neigh chain
        unicorn = CARD_DATABASE.create_instance("basic_red")
        self.state.players[0].hand.append(unicorn)
        self.state.players[0].cards_cannot_be_neighd = True

        action = Action(
            action_type=ActionType.PLAY_CARD,
            player_idx=0,
            card=unicorn
        )
        self.state = apply_action(self.state, action)

        self.assertEqual(len(self.state.players[0].hand), 0)
        self.assertEqual(len(self.state.players[0].stable), 1)
        self.assertEqual(self.state.actions_remaining, 0)

    def test_end_action_phase(self):
        """Test ending action phase."""
        self.state.phase = GamePhase.ACTION
        self.state.current_player_idx = 0

        action = Action(action_type=ActionType.END_ACTION_PHASE, player_idx=0)
        self.state = apply_action(self.state, action)

        # Should advance to next player's beginning phase
        self.assertEqual(self.state.current_player_idx, 1)

    def test_win_condition_checked(self):
        """Test that win condition is checked after action."""
        self.state.phase = GamePhase.ACTION
        self.state.actions_remaining = 1
        self.state.players[0].cards_cannot_be_neighd = True

        # Add 6 unicorns to stable
        for i in range(6):
            self.state.players[0].stable.append(
                CARD_DATABASE.create_instance("basic_red")
            )

        # Play 7th unicorn
        unicorn = CARD_DATABASE.create_instance("basic_blue")
        self.state.players[0].hand.append(unicorn)

        action = Action(
            action_type=ActionType.PLAY_CARD,
            player_idx=0,
            card=unicorn
        )
        self.state = apply_action(self.state, action)

        self.assertEqual(self.state.winner, 0)
        self.assertEqual(self.state.phase, GamePhase.GAME_OVER)


class TestNeighChain(unittest.TestCase):
    """Tests for Neigh chain mechanics."""

    def setUp(self):
        """Set up test game state."""
        self.players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        self.state = GameState(players=self.players, num_players=2)
        self.state.draw_pile = CARD_DATABASE.create_deck()

    def test_neigh_chain_starts(self):
        """Test that playing a card starts Neigh chain."""
        self.state.phase = GamePhase.ACTION
        self.state.actions_remaining = 1

        # P1 has a unicorn, P2 has a Neigh
        unicorn = CARD_DATABASE.create_instance("basic_red")
        self.state.players[0].hand.append(unicorn)

        neigh = CARD_DATABASE.create_instance("neigh")
        self.state.players[1].hand.append(neigh)

        action = Action(
            action_type=ActionType.PLAY_CARD,
            player_idx=0,
            card=unicorn
        )
        self.state = apply_action(self.state, action)

        # Neigh chain should be active
        self.assertTrue(self.state.neigh_chain_active)
        self.assertEqual(self.state.card_being_played, unicorn)

    def test_pass_neigh_resolves_card(self):
        """Test that passing on Neigh resolves the card."""
        self.state.neigh_chain_active = True
        unicorn = CARD_DATABASE.create_instance("basic_red")
        self.state.card_being_played = unicorn

        # No one has Neigh cards, pass
        action = Action(action_type=ActionType.PASS_NEIGH, player_idx=1)
        self.state = apply_action(self.state, action)

        # Card should resolve
        self.assertFalse(self.state.neigh_chain_active)


if __name__ == "__main__":
    unittest.main()
