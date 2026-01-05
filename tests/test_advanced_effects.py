"""Tests for advanced card interactions and edge cases."""

import unittest
from game.game_state import GameState, PlayerState, GamePhase, EffectTask
from game.action import Action, ActionType, apply_action
from game.effect_handler import EffectHandler
from cards.card_database import CARD_DATABASE
from cards.card import CardType
from cards.effects import EFFECT_REGISTRY

class TestAdvancedEffects(unittest.TestCase):
    def setUp(self):
        players = [
            PlayerState(player_idx=0, name="Player 1"),
            PlayerState(player_idx=1, name="Player 2"),
        ]
        self.state = GameState(players=players, num_players=2)
        self.state.phase = GamePhase.ACTION
        self.state.actions_remaining = 1
        
        # Helper to get specific card instance
        self.get_card = lambda id: CARD_DATABASE.create_instance(id)

    def test_chain_reaction_resurrection(self):
        """Test: Barbed Wire destroys Phoenix -> Phoenix resurrects."""
        # P1 has Barbed Wire
        wire = self.get_card("barbed_wire")
        self.state.add_to_stable(wire, 0)
        
        # P2 has Unicorn Phoenix
        phoenix = self.get_card("unicorn_phoenix")
        self.state.add_to_stable(phoenix, 1)
        # P2 needs a card to discard for resurrection
        discard_fodder = self.get_card("basic_red")
        self.state.players[1].hand.append(discard_fodder)
        
        # P1 plays a unicorn -> Triggers Barbed Wire
        p1_unicorn = self.get_card("basic_blue")
        self.state.players[0].hand.append(p1_unicorn)
        
        # Action: Play Unicorn
        self.state = apply_action(self.state, Action(ActionType.PLAY_CARD, 0, card=p1_unicorn))
        
        # Stack should have Barbed Wire trigger
        self.assertTrue(len(self.state.resolution_stack) > 0)
        task = self.state.resolution_stack[-1]
        self.assertEqual(task.effect.effect_id, "barbed_wire")
        
        # P1 chooses to destroy Phoenix
        self.state = apply_action(self.state, Action(ActionType.CHOOSE_TARGET, 0, target_card=phoenix))
        
        # Now, Phoenix ON_LEAVE should trigger
        # "If this card would be destroyed... you may DISCARD a card... return to stable"
        # My implementation of Phoenix is ON_LEAVE trigger.
        # Check stack for Phoenix effect
        self.assertTrue(len(self.state.resolution_stack) > 0)
        task = self.state.resolution_stack[-1]
        self.assertEqual(task.effect.effect_id, "unicorn_phoenix")
        
        # Phoenix Effect Action 1: Discard card (TargetType.OWN_HAND)
        # We need to choose the card to discard
        self.state = apply_action(self.state, Action(ActionType.CHOOSE_TARGET, 1, target_card=discard_fodder))
        
        # Verify Phoenix is back in stable (or never left? My implementation creates a new instance or moves it back)
        # In `_execute_action` for BRING_TO_STABLE/RETURN_TO_HAND, it handles movement.
        # Phoenix logic: Action 1 Discard, Action 2 Bring Self to Stable.
        
        self.assertIn(phoenix, self.state.players[1].stable)
        self.assertIn(discard_fodder, self.state.discard_pile)

    def test_pandamonium_protection(self):
        """Test: Pandamonium prevents 'Destroy Unicorn' effects."""
        # P1 has Pandamonium (Unicorns are Pandas)
        panda = self.get_card("pandamonium")
        self.state.add_to_stable(panda, 0)
        
        p1_unicorn = self.get_card("basic_red")
        self.state.add_to_stable(p1_unicorn, 0)
        
        # Verify flags
        from game.action import _update_player_flags
        _update_player_flags(self.state, 0)
        self.assertTrue(self.state.players[0].unicorns_are_pandas)
        
        # P2 plays "Unicorn Poison" (Destroy a Unicorn)
        poison = self.get_card("unicorn_poison")
        self.state.players[1].hand.append(poison)
        
        # Action: Play Poison
        self.state = apply_action(self.state, Action(ActionType.PLAY_CARD, 1, card=poison))
        
        # Effect triggers, asking for target.
        # We try to target P1's unicorn.
        # The `get_valid_targets` or `_execute_action` logic should prevent this or it shouldn't be a valid target.
        
        from game.action import _get_valid_targets
        from cards.effects import TargetType
        
        # Valid targets for ANY_UNICORN
        valid = _get_valid_targets(self.state, TargetType.ANY_UNICORN, 1)
        
        # P1's unicorn should NOT be in valid list because it's a Panda
        self.assertNotIn(p1_unicorn, valid)
        
    def test_queen_bee_blocking(self):
        """Test: Queen Bee prevents Basic Unicorns from entering other stables."""
        # P1 has Queen Bee
        bee = self.get_card("queen_bee_unicorn")
        self.state.add_to_stable(bee, 0)
        
        # P2 tries to play Basic Unicorn
        basic = self.get_card("basic_red")
        self.state.players[1].hand.append(basic)
        
        # Check legality
        from game.action import get_legal_actions
        
        # Since Queen Bee effect is continuous, check `_can_play_card` logic
        actions = get_legal_actions(self.state)
        play_actions = [a for a in actions if a.action_type == ActionType.PLAY_CARD and a.card == basic]
        
        # Should be empty/blocked
        self.assertEqual(len(play_actions), 0)
        
    def test_conditional_effect_shark(self):
        """Test: Shark With A Horn only works if you have a downgrade."""
        # P1 plays Shark
        shark = self.get_card("shark_with_a_horn")
        self.state.players[0].hand.append(shark)
        
        # Case 1: No Downgrade -> Effect should not trigger or condition fail
        self.state = apply_action(self.state, Action(ActionType.PLAY_CARD, 0, card=shark))
        
        # Shark enters. Effect added to stack.
        # Processing stack... 
        # Action 1: Destroy Unicorn. Condition: "if_downgrade_in_stable".
        
        # Stack should process and finish immediately because condition fails
        self.assertEqual(len(self.state.resolution_stack), 0)
        
        # Case 2: With Downgrade
        downgrade = self.get_card("barbed_wire") # any downgrade
        self.state.add_to_stable(downgrade, 0)
        
        # Add another shark
        shark2 = self.get_card("shark_with_a_horn")
        self.state.players[0].hand.append(shark2)
        
        # Add target for destruction
        target = self.get_card("basic_blue")
        self.state.add_to_stable(target, 1)
        
        self.state = apply_action(self.state, Action(ActionType.PLAY_CARD, 0, card=shark2))
        
        # Now stack should have tasks. Barbed Wire triggers too because Shark is a unicorn.
        # Stack order: [Shark, Barbed Wire] (LIFO processing)
        
        self.assertTrue(len(self.state.resolution_stack) > 0)
        
        # Check that Shark effect is in the stack
        effect_ids = [t.effect.effect_id for t in self.state.resolution_stack]
        self.assertIn("shark_with_a_horn", effect_ids)

if __name__ == '__main__':
    unittest.main()
