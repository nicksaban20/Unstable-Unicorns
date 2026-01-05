"""Tests for complex game mechanics and effects."""

import unittest
from unittest.mock import MagicMock

from game.game_state import GameState, PlayerState, GamePhase, EffectTask
from game.action import Action, ActionType, apply_action
from game.effect_handler import EffectHandler
from cards.card_database import CARD_DATABASE
from cards.card import CardType
from cards.effects import EFFECT_REGISTRY, EffectTrigger

class TestComplexMechanics(unittest.TestCase):
    def setUp(self):
        # Setup a 2-player game
        players = [
            PlayerState(player_idx=0, name="Player 1"),
            PlayerState(player_idx=1, name="Player 2"),
        ]
        self.state = GameState(players=players, num_players=2)
        self.state.draw_pile = CARD_DATABASE.create_deck()
        self.state.phase = GamePhase.ACTION
        self.state.actions_remaining = 1

    def test_sacrifice_and_destroy(self):
        """Test 'Sacrifice X then Destroy Y' mechanics."""
        # Setup: P1 has a Unicorn, P2 has a Unicorn
        p1_unicorn = CARD_DATABASE.create_instance("basic_red")
        self.state.add_to_stable(p1_unicorn, 0)
        
        p2_unicorn = CARD_DATABASE.create_instance("basic_blue")
        self.state.add_to_stable(p2_unicorn, 1)

        # Effect: Sacrifice a card, then destroy a card (e.g., Two-For-One style, but simplified manual test)
        # We'll use "Narwhal Torpedo": Sacrifice self, destroy unicorn.
        torpedo = CARD_DATABASE.create_instance("narwhal_torpedo")
        self.state.add_to_stable(torpedo, 0)
        
        # Trigger effect manually for testing logic
        effect = EFFECT_REGISTRY.get("narwhal_torpedo")
        self.state.resolution_stack.append(EffectTask(effect, 0, torpedo))
        
        # Step 1: Processing should stop for Target (Sacrifice self)
        # Actually Narwhal Torpedo: "Sacrifice THIS card".
        # TargetType.SELF is automatic in my implementation? 
        # Let's check logic: if target needed (SELF is skipped in check), it executes immediately.
        EffectHandler.process_stack(self.state)
        
        # Check if it auto-executed the sacrifice (TargetType.SELF)
        # Action 1: Sacrifice Self.
        # Action 2: Destroy Unicorn (TargetType.OTHER_UNICORN or ANY_UNICORN)
        
        # Verify Torpedo is sacrificed
        self.assertNotIn(torpedo, self.state.players[0].stable)
        self.assertIn(torpedo, self.state.discard_pile)
        
        # Step 2: Now stack should be waiting for Target (Destroy Unicorn)
        self.assertTrue(len(self.state.resolution_stack) > 0)
        task = self.state.resolution_stack[-1]
        self.assertEqual(task.current_action_idx, 1) # Waiting on Action 2
        
        # Provide Target: P2's Unicorn
        action = Action(
            action_type=ActionType.CHOOSE_TARGET,
            player_idx=0,
            target_card=p2_unicorn
        )
        self.state = apply_action(self.state, action)
        
        # Verify P2 unicorn destroyed
        self.assertNotIn(p2_unicorn, self.state.players[1].stable)
        self.assertIn(p2_unicorn, self.state.discard_pile)
        
        # Verify stack empty
        self.assertEqual(len(self.state.resolution_stack), 0)

    def test_search_deck(self):
        """Test searching the deck for a card."""
        # Use "Magical Flying Unicorn": Search deck for Magic card
        card = CARD_DATABASE.create_instance("magical_flying_unicorn")
        self.state.add_to_stable(card, 0)
        
        effect = EFFECT_REGISTRY.get("magical_flying_unicorn")
        self.state.resolution_stack.append(EffectTask(effect, 0, card))
        
        EffectHandler.process_stack(self.state)
        
        # Should wait for target (Card in Deck)
        self.assertTrue(len(self.state.resolution_stack) > 0)
        
        # Find a magic card in deck
        target_card = next(c for c in self.state.draw_pile if c.card_type == CardType.MAGIC)
        
        action = Action(
            action_type=ActionType.CHOOSE_TARGET,
            player_idx=0,
            target_card=target_card
        )
        self.state = apply_action(self.state, action)
        
        # Verify card moved to hand
        self.assertIn(target_card, self.state.players[0].hand)
        self.assertNotIn(target_card, self.state.draw_pile)

    def test_steal_card(self):
        """Test stealing a card from another stable."""
        # P2 has an upgrade
        upgrade = CARD_DATABASE.create_instance("rainbow_aura")
        self.state.add_to_stable(upgrade, 1)
        
        # P1 plays "Alluring Narwhal": Steal an upgrade
        narwhal = CARD_DATABASE.create_instance("alluring_narwhal")
        self.state.add_to_stable(narwhal, 0)
        
        effect = EFFECT_REGISTRY.get("alluring_narwhal")
        self.state.resolution_stack.append(EffectTask(effect, 0, narwhal))
        
        EffectHandler.process_stack(self.state)
        
        # Should wait for target
        self.assertTrue(len(self.state.resolution_stack) > 0)
        
        # Target the upgrade
        action = Action(
            action_type=ActionType.CHOOSE_TARGET,
            player_idx=0,
            target_card=upgrade
        )
        self.state = apply_action(self.state, action)
        
        # Verify stolen
        self.assertNotIn(upgrade, self.state.players[1].upgrades)
        self.assertIn(upgrade, self.state.players[0].upgrades)

    def test_listener_triggers(self):
        """Test that events trigger other cards (Barbed Wire)."""
        # P1 has Barbed Wire: "Each time a Unicorn enters/leaves YOUR stable, DESTROY a Unicorn"
        wire = CARD_DATABASE.create_instance("barbed_wire")
        self.state.add_to_stable(wire, 0) # P1 has it
        
        # P2 has a unicorn (target fodder)
        p2_unicorn = CARD_DATABASE.create_instance("basic_blue")
        self.state.add_to_stable(p2_unicorn, 1)
        
        # P1 plays a unicorn -> Should trigger Barbed Wire
        p1_unicorn = CARD_DATABASE.create_instance("basic_red")
        
        # Use apply_action to simulate full flow
        self.state.players[0].hand.append(p1_unicorn)
        play_action = Action(ActionType.PLAY_CARD, 0, card=p1_unicorn)
        self.state = apply_action(self.state, play_action)
        
        # Logic: 
        # 1. P1 plays unicorn -> Adds to stable.
        # 2. _trigger_enter_events sees Barbed Wire.
        # 3. Barbed Wire effect added to stack.
        # 4. Barbed Wire asks to DESTROY a unicorn.
        
        # Verify stack is waiting for destroy target
        self.assertTrue(len(self.state.resolution_stack) > 0)
        task = self.state.resolution_stack[-1]
        self.assertEqual(task.effect.effect_id, "barbed_wire")
        
        # Execute destroy on P2 unicorn
        target_action = Action(ActionType.CHOOSE_TARGET, 0, target_card=p2_unicorn)
        self.state = apply_action(self.state, target_action)
        
        # Verify P2 unicorn destroyed
        self.assertNotIn(p2_unicorn, self.state.players[1].stable)
        self.assertIn(p2_unicorn, self.state.discard_pile)

if __name__ == '__main__':
    unittest.main()
