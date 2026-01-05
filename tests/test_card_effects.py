"""Tests for specific complex card effects."""

import unittest
from game.game_state import GameState, PlayerState, GamePhase, EffectTask
from game.action import Action, ActionType, apply_action
from game.effect_handler import EffectHandler
from cards.card_database import CARD_DATABASE
from cards.card import CardType
from cards.effects import EFFECT_REGISTRY, Effect, EffectAction, ActionType as EActionType, TargetType, EffectTrigger, EffectTarget

class TestCardEffects(unittest.TestCase):
    def setUp(self):
        players = [
            PlayerState(player_idx=0, name="P1"),
            PlayerState(player_idx=1, name="P2"),
        ]
        self.state = GameState(players=players, num_players=2)
        self.state.phase = GamePhase.ACTION
        self.state.actions_remaining = 1
        self.state.draw_pile = CARD_DATABASE.create_deck() # Initialize deck
        self.get_card = lambda id: CARD_DATABASE.create_instance(id)

    def test_glitter_tornado(self):
        """Test Glitter Tornado: Shuffle a card from EACH stable into deck."""
        c1 = self.get_card("basic_red")
        self.state.add_to_stable(c1, 0)
        c2 = self.get_card("basic_blue")
        self.state.add_to_stable(c2, 1)
        
        tornado = self.get_card("glitter_tornado")
        self.state.players[0].hand.append(tornado)
        
        effect = EFFECT_REGISTRY.get("glitter_tornado")
        self.state.resolution_stack.append(EffectTask(effect, 0, tornado))
        
        EffectHandler.process_stack(self.state)
        
        self.state = apply_action(self.state, Action(ActionType.CHOOSE_TARGET, 0, target_card=c1))
        self.state = apply_action(self.state, Action(ActionType.CHOOSE_TARGET, 0, target_card=c2))
        
        self.assertIn(c1, self.state.draw_pile)
        self.assertIn(c2, self.state.draw_pile)
        self.assertNotIn(c1, self.state.players[0].stable)
        
    def test_change_of_luck(self):
        """Test Change of Luck: Discard hand, Draw 5, Discard X."""
        p1 = self.state.players[0]
        p1.hand = [self.get_card("basic_red"), self.get_card("basic_blue"), self.get_card("neigh")]
        
        luck = self.get_card("change_of_luck")
        p1.hand.append(luck)
        
        self.state = apply_action(self.state, Action(ActionType.PLAY_CARD, 0, card=luck))
        
        # Check Discard Pile
        # Should contain Red, Blue, Neigh (3 cards) + Change of Luck (1 card) = 4 cards
        self.assertEqual(len(self.state.discard_pile), 4, f"Discard pile has {len(self.state.discard_pile)} cards: {self.state.discard_pile}")
        
        # Hand should be 5 (Draw 5 executed)
        self.assertEqual(len(p1.hand), 5)

    def test_unicorn_swap_mechanic(self):
        """Test the SWAP mechanic implementation."""
        effect = Effect(
            effect_id="test_swap",
            name="Test Swap",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(EActionType.SELECT, EffectTarget(TargetType.OWN_UNICORN)), 
                EffectAction(EActionType.SELECT, EffectTarget(TargetType.OTHER_UNICORN)), 
                EffectAction(EActionType.SWAP, EffectTarget(TargetType.NONE)) 
            ]
        )
        EFFECT_REGISTRY.register(effect)
        
        c1 = self.get_card("basic_red")
        self.state.add_to_stable(c1, 0)
        c2 = self.get_card("basic_blue")
        self.state.add_to_stable(c2, 1)
        
        dummy = self.get_card("basic_green")
        
        self.state.resolution_stack.append(EffectTask(effect, 0, dummy))
        EffectHandler.process_stack(self.state)
        
        self.state = apply_action(self.state, Action(ActionType.CHOOSE_TARGET, 0, target_card=c1))
        self.state = apply_action(self.state, Action(ActionType.CHOOSE_TARGET, 0, target_card=c2))
        
        EffectHandler.process_stack(self.state)
        
        self.assertIn(c2, self.state.players[0].stable)
        self.assertIn(c1, self.state.players[1].stable)

    def test_caffeine_overload_extra_action(self):
        """Test Caffeine Overload gives extra action."""
        caff = self.get_card("caffeine_overload")
        self.state.add_to_stable(caff, 0)
        
        self.state.phase = GamePhase.DRAW
        self.state.draw_pile.append(self.get_card("basic_red"))
        
        self.state = apply_action(self.state, Action(ActionType.DRAW_CARD, 0))
        
        self.assertEqual(self.state.actions_remaining, 2)
        
    def test_nanny_cam_visibility(self):
        """Test Nanny Cam makes hand visible."""
        cam = self.get_card("nanny_cam")
        self.state.add_to_stable(cam, 0)
        
        from game.action import _update_player_flags
        _update_player_flags(self.state, 0)
        
        self.assertTrue(self.state.players[0].hand_visible)
        
        known_card = self.get_card("basic_red")
        self.state.players[0].hand = [known_card]
        
        det_state_view = self.state.determinize_for_player(1)
        self.assertEqual(det_state_view.players[0].hand[0].card.id, "basic_red")

if __name__ == '__main__':
    unittest.main()