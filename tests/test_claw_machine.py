"""Tests for Claw Machine mechanic."""

import unittest
from game.game_state import GameState, PlayerState, GamePhase, EffectTask
from game.action import Action, ActionType, apply_action
from game.effect_handler import EffectHandler
from cards.card_database import CARD_DATABASE
from cards.effects import EFFECT_REGISTRY, TargetType, ActionType as EActionType

class TestClawMachine(unittest.TestCase):
    def setUp(self):
        players = [PlayerState(0, "P1"), PlayerState(1, "P2")]
        self.state = GameState(players=players, num_players=2)
        self.state.draw_pile = CARD_DATABASE.create_deck()
        self.state.phase = GamePhase.BEGINNING
        self.get_card = lambda id: CARD_DATABASE.create_instance(id)

    def test_claw_machine_basic(self):
        """Test picking a card from discard."""
        claw = self.get_card("claw_machine")
        self.state.add_to_stable(claw, 0)
        
        # Add target to discard
        target = self.get_card("basic_red")
        self.state.discard_pile.append(target)
        
        effect = EFFECT_REGISTRY.get("claw_machine")
        self.state.resolution_stack.append(EffectTask(effect, 0, claw))
        
        EffectHandler.process_stack(self.state)
        
        # Choose target
        self.state = apply_action(self.state, Action(ActionType.CHOOSE_TARGET, 0, target_card=target))
        
        # Verify
        self.assertIn(target, self.state.players[0].hand)
        self.assertNotIn(target, self.state.discard_pile)

    def test_claw_machine_optional(self):
        """Test skipping the choice."""
        claw = self.get_card("claw_machine")
        self.state.add_to_stable(claw, 0)
        
        target = self.get_card("basic_red")
        self.state.discard_pile.append(target)
        
        effect = EFFECT_REGISTRY.get("claw_machine")
        self.state.resolution_stack.append(EffectTask(effect, 0, claw))
        
        EffectHandler.process_stack(self.state)
        
        # Choose None
        self.state = apply_action(self.state, Action(ActionType.CHOOSE_TARGET, 0, target_card=None))
        
        # Verify nothing happened
        self.assertNotIn(target, self.state.players[0].hand)
        self.assertIn(target, self.state.discard_pile)

if __name__ == '__main__':
    unittest.main()
