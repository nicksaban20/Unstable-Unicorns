"""Unit tests for game state."""

import unittest
from game.game_state import GameState, PlayerState, GamePhase
from cards.card_database import CARD_DATABASE


class TestPlayerState(unittest.TestCase):
    """Tests for PlayerState class."""

    def test_player_creation(self):
        """Test basic player creation."""
        player = PlayerState(player_idx=0, name="Test Player")

        self.assertEqual(player.player_idx, 0)
        self.assertEqual(player.name, "Test Player")
        self.assertEqual(len(player.hand), 0)
        self.assertEqual(len(player.stable), 0)

    def test_unicorn_count(self):
        """Test unicorn counting."""
        player = PlayerState(player_idx=0, name="Test")

        # Add some unicorns
        basic = CARD_DATABASE.create_instance("basic_red")
        magical = CARD_DATABASE.create_instance("rhinocorn")

        player.stable.append(basic)
        self.assertEqual(player.unicorn_count(), 1)

        player.stable.append(magical)
        self.assertEqual(player.unicorn_count(), 2)

    def test_ginormous_counts_as_two(self):
        """Test that Ginormous Unicorn counts as 2."""
        player = PlayerState(player_idx=0, name="Test")

        ginormous = CARD_DATABASE.create_instance("ginormous_unicorn")
        player.stable.append(ginormous)

        self.assertEqual(player.unicorn_count(), 2)

    def test_get_all_stable_cards(self):
        """Test getting all stable cards."""
        player = PlayerState(player_idx=0, name="Test")

        unicorn = CARD_DATABASE.create_instance("basic_red")
        upgrade = CARD_DATABASE.create_instance("yay")
        downgrade = CARD_DATABASE.create_instance("blinding_light")

        player.stable.append(unicorn)
        player.upgrades.append(upgrade)
        player.downgrades.append(downgrade)

        all_cards = player.get_all_stable_cards()
        self.assertEqual(len(all_cards), 3)
        self.assertIn(unicorn, all_cards)
        self.assertIn(upgrade, all_cards)
        self.assertIn(downgrade, all_cards)

    def test_has_downgrade(self):
        """Test downgrade detection."""
        player = PlayerState(player_idx=0, name="Test")

        self.assertFalse(player.has_downgrade())

        downgrade = CARD_DATABASE.create_instance("blinding_light")
        player.downgrades.append(downgrade)

        self.assertTrue(player.has_downgrade())

    def test_player_copy(self):
        """Test player state copying."""
        player = PlayerState(player_idx=0, name="Test")
        player.hand.append(CARD_DATABASE.create_instance("rhinocorn"))
        player.stable.append(CARD_DATABASE.create_instance("basic_red"))

        copy = player.copy()

        # Check values match
        self.assertEqual(copy.player_idx, player.player_idx)
        self.assertEqual(copy.name, player.name)
        self.assertEqual(len(copy.hand), len(player.hand))
        self.assertEqual(len(copy.stable), len(player.stable))

        # Check it's a different object
        self.assertIsNot(copy, player)
        self.assertIsNot(copy.hand, player.hand)


class TestGameState(unittest.TestCase):
    """Tests for GameState class."""

    def test_game_state_creation(self):
        """Test basic game state creation."""
        players = [
            PlayerState(player_idx=0, name="Player 1"),
            PlayerState(player_idx=1, name="Player 2"),
        ]
        state = GameState(players=players, num_players=2)

        self.assertEqual(state.num_players, 2)
        self.assertEqual(len(state.players), 2)
        self.assertEqual(state.phase, GamePhase.BEGINNING)
        self.assertIsNone(state.winner)

    def test_unicorns_to_win_by_player_count(self):
        """Test win condition scales with player count."""
        # 2-5 players need 7 unicorns
        for n in [2, 3, 4, 5]:
            players = [PlayerState(player_idx=i, name=f"P{i}") for i in range(n)]
            state = GameState(players=players, num_players=n)
            self.assertEqual(state.unicorns_to_win, 7)

        # 6 players need 6 unicorns
        players = [PlayerState(player_idx=i, name=f"P{i}") for i in range(6)]
        state = GameState(players=players, num_players=6)
        self.assertEqual(state.unicorns_to_win, 6)

    def test_current_player(self):
        """Test current player property."""
        players = [
            PlayerState(player_idx=0, name="Player 1"),
            PlayerState(player_idx=1, name="Player 2"),
        ]
        state = GameState(players=players, num_players=2)

        state.current_player_idx = 0
        self.assertEqual(state.current_player.name, "Player 1")

        state.current_player_idx = 1
        self.assertEqual(state.current_player.name, "Player 2")

    def test_is_game_over(self):
        """Test game over detection."""
        players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        state = GameState(players=players, num_players=2)

        self.assertFalse(state.is_game_over())

        state.winner = 0
        self.assertTrue(state.is_game_over())

    def test_check_win_condition(self):
        """Test win condition checking."""
        players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        state = GameState(players=players, num_players=2)

        # No winner initially
        self.assertIsNone(state.check_win_condition())

        # Add 7 unicorns to player 1
        for i in range(7):
            state.players[0].stable.append(
                CARD_DATABASE.create_instance("basic_red")
            )

        self.assertEqual(state.check_win_condition(), 0)

    def test_pandamonium_blocks_win(self):
        """Test that Pandamonium prevents winning."""
        players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        state = GameState(players=players, num_players=2)

        # Add 7 unicorns to player 1
        for i in range(7):
            state.players[0].stable.append(
                CARD_DATABASE.create_instance("basic_red")
            )

        # Enable pandamonium
        state.players[0].unicorns_are_pandas = True

        # Should not win
        self.assertIsNone(state.check_win_condition())

    def test_draw_card(self):
        """Test drawing cards."""
        players = [PlayerState(player_idx=0, name="P1")]
        state = GameState(players=players, num_players=1)

        # Add cards to draw pile
        for i in range(5):
            state.draw_pile.append(CARD_DATABASE.create_instance("basic_red"))

        # Draw cards
        drawn = state.draw_card(0, 2)

        self.assertEqual(len(drawn), 2)
        self.assertEqual(len(state.players[0].hand), 2)
        self.assertEqual(len(state.draw_pile), 3)

    def test_draw_reshuffles_discard(self):
        """Test that discard is reshuffled when draw pile is empty."""
        players = [PlayerState(player_idx=0, name="P1")]
        state = GameState(players=players, num_players=1)

        # Empty draw pile, cards in discard
        state.draw_pile = []
        for i in range(3):
            state.discard_pile.append(CARD_DATABASE.create_instance("basic_red"))

        drawn = state.draw_card(0, 2)

        self.assertEqual(len(drawn), 2)
        self.assertEqual(len(state.draw_pile), 1)
        self.assertEqual(len(state.discard_pile), 0)

    def test_add_to_stable(self):
        """Test adding cards to stable."""
        players = [PlayerState(player_idx=0, name="P1")]
        state = GameState(players=players, num_players=1)

        unicorn = CARD_DATABASE.create_instance("basic_red")
        upgrade = CARD_DATABASE.create_instance("yay")
        downgrade = CARD_DATABASE.create_instance("blinding_light")

        state.add_to_stable(unicorn, 0)
        state.add_to_stable(upgrade, 0)
        state.add_to_stable(downgrade, 0)

        self.assertEqual(len(state.players[0].stable), 1)
        self.assertEqual(len(state.players[0].upgrades), 1)
        self.assertEqual(len(state.players[0].downgrades), 1)

    def test_remove_from_stable(self):
        """Test removing cards from stable."""
        players = [PlayerState(player_idx=0, name="P1")]
        state = GameState(players=players, num_players=1)

        unicorn = CARD_DATABASE.create_instance("basic_red")
        state.players[0].stable.append(unicorn)

        state.remove_from_stable(unicorn, 0)

        self.assertEqual(len(state.players[0].stable), 0)
        self.assertEqual(len(state.discard_pile), 1)

    def test_get_baby_from_nursery(self):
        """Test getting baby unicorn from nursery."""
        players = [PlayerState(player_idx=0, name="P1")]
        state = GameState(players=players, num_players=1)

        # Add babies to nursery
        state.nursery = CARD_DATABASE.create_nursery()
        initial_count = len(state.nursery)

        baby = state.get_baby_unicorn_from_nursery()

        self.assertIsNotNone(baby)
        self.assertEqual(len(state.nursery), initial_count - 1)

    def test_state_copy(self):
        """Test game state copying."""
        players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        state = GameState(players=players, num_players=2)
        state.draw_pile = CARD_DATABASE.create_deck()

        copy = state.copy()

        # Check values match
        self.assertEqual(copy.num_players, state.num_players)
        self.assertEqual(copy.current_player_idx, state.current_player_idx)
        self.assertEqual(len(copy.draw_pile), len(state.draw_pile))

        # Check it's a different object
        self.assertIsNot(copy, state)
        self.assertIsNot(copy.players, state.players)
        self.assertIsNot(copy.draw_pile, state.draw_pile)

    def test_determinize_for_player(self):
        """Test determinization for hidden information."""
        players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        state = GameState(players=players, num_players=2)

        # Add cards to hands and deck
        for i in range(5):
            state.players[0].hand.append(CARD_DATABASE.create_instance("basic_red"))
            state.players[1].hand.append(CARD_DATABASE.create_instance("basic_blue"))
        state.draw_pile = CARD_DATABASE.create_deck()

        # Determinize for player 0
        det_state = state.determinize_for_player(0)

        # Player 0's hand should be unchanged
        self.assertEqual(len(det_state.players[0].hand), 5)

        # Player 1's hand should still have 5 cards
        self.assertEqual(len(det_state.players[1].hand), 5)


class TestGamePhase(unittest.TestCase):
    """Tests for GamePhase enum."""

    def test_all_phases_exist(self):
        """Test that all expected phases exist."""
        phases = [GamePhase.BEGINNING, GamePhase.DRAW, GamePhase.ACTION,
                  GamePhase.END, GamePhase.GAME_OVER]

        for phase in phases:
            self.assertIsInstance(phase, GamePhase)


if __name__ == "__main__":
    unittest.main()
