"""Action system for Unstable Unicorns.

Defines all possible player actions and how to apply them.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, List, Optional, Union, Tuple

from cards.card import CardInstance, CardType
from cards.effects import EFFECT_REGISTRY, TargetType, EffectAction
from game.game_state import EffectTask
from game.effect_handler import EffectHandler

if TYPE_CHECKING:
    from game.game_state import GameState, GamePhase


class ActionType(Enum):
    """Types of actions a player can take."""
    # Basic turn actions
    DRAW_CARD = auto()           # Draw a card (draw phase)
    PLAY_CARD = auto()           # Play a card from hand
    END_ACTION_PHASE = auto()    # End action phase without playing

    # Instant actions
    NEIGH = auto()               # Counter a card being played
    PASS_NEIGH = auto()          # Pass on opportunity to Neigh

    # Effect-triggered actions
    CHOOSE_TARGET = auto()       # Choose a target for an effect
    SACRIFICE = auto()           # Sacrifice a card (own stable)
    DESTROY = auto()             # Destroy a card (any stable)
    DISCARD = auto()             # Discard from hand
    STEAL = auto()               # Steal a card
    SEARCH_DECK = auto()         # Search deck for a card
    BRING_FROM_DISCARD = auto()  # Bring card from discard
    RETURN_TO_HAND = auto()      # Return card to hand
    BRING_BABY = auto()          # Bring baby unicorn from nursery


@dataclass
class Action:
    """Represents a player action."""
    action_type: ActionType
    player_idx: int

    # Card involved (for PLAY_CARD, NEIGH, etc.)
    card: Optional[CardInstance] = None

    # Target(s) for effects
    target_card: Optional[CardInstance] = None
    target_player_idx: Optional[int] = None

    # For multi-target effects
    target_cards: Optional[List[CardInstance]] = None

    def __repr__(self) -> str:
        if self.action_type == ActionType.PLAY_CARD:
            return f"Play({self.card.name})"
        elif self.action_type == ActionType.NEIGH:
            return f"Neigh({self.card.name})"
        elif self.action_type == ActionType.DRAW_CARD:
            return "Draw"
        elif self.action_type == ActionType.END_ACTION_PHASE:
            return "EndAction"
        elif self.action_type == ActionType.PASS_NEIGH:
            return "PassNeigh"
        elif self.action_type == ActionType.CHOOSE_TARGET:
            target_name = self.target_card.name if self.target_card else "None"
            return f"ChooseTarget({target_name})"
        else:
            return f"{self.action_type.name}"


def get_legal_actions(state: 'GameState') -> List[Action]:
    """Get all legal actions for the current player in the current state."""
    from game.game_state import GamePhase

    actions: List[Action] = []
    player_idx = state.current_player_idx
    player = state.current_player

    # Handle Neigh chain
    if state.neigh_chain_active:
        return _get_neigh_actions(state)

    # Handle pending effect choices (Resolution Stack)
    if state.resolution_stack:
        return _get_effect_choice_actions(state)

    # Normal turn phases
    if state.phase == GamePhase.DRAW:
        # Draw phase: must draw a card (or skip if deck is empty)
        if state.draw_pile or state.discard_pile:
            actions.append(Action(
                action_type=ActionType.DRAW_CARD,
                player_idx=player_idx
            ))
        else:
            # No cards to draw, move to action phase
            actions.append(Action(
                action_type=ActionType.END_ACTION_PHASE,
                player_idx=player_idx
            ))

    elif state.phase == GamePhase.ACTION:
        # Action phase: can play cards or end phase

        # Can always end action phase
        actions.append(Action(
            action_type=ActionType.END_ACTION_PHASE,
            player_idx=player_idx
        ))

        # Check if player has actions remaining
        if state.actions_remaining > 0:
            # Add playable cards from hand
            for card in player.hand:
                if card.card_type == CardType.DOWNGRADE:
                    # Downgrades require choosing a target player
                    other_players = state.get_other_players(player_idx)
                    for target_p in other_players:
                        actions.append(Action(
                            action_type=ActionType.PLAY_CARD,
                            player_idx=player_idx,
                            card=card,
                            target_player_idx=target_p.player_idx
                        ))
                elif _can_play_card(state, player_idx, card):
                    actions.append(Action(
                        action_type=ActionType.PLAY_CARD,
                        player_idx=player_idx,
                        card=card
                    ))

    elif state.phase == GamePhase.DISCARD_TO_LIMIT:
        # Must discard down to 7
        player = state.current_player
        if len(player.hand) > 7:
            for card in player.hand:
                actions.append(Action(
                    action_type=ActionType.DISCARD,
                    player_idx=player_idx,
                    target_card=card
                ))
        else:
            # Done discarding, proceed to End
            # This case shouldn't be hit if phase is managed correctly, but as failsafe:
            # We need an action to "confirm" or auto-transition.
            # But get_legal_actions is for USER input.
            # If logic handles auto-transition, we return empty?
            pass

    elif state.phase == GamePhase.BEGINNING:
        # Beginning of turn effects are handled automatically by processing loop
        # If we are here, it means we are waiting for triggers or moving phase
        # But usually processing happens in apply_action loop.
        pass

    elif state.phase == GamePhase.END:
        pass

    return actions


def _can_play_card(state: 'GameState', player_idx: int, card: CardInstance) -> bool:
    """Check if a player can legally play a card."""
    player = state.players[player_idx]

    # Check card type restrictions
    if card.card_type == CardType.UPGRADE:
        if player.cannot_play_upgrades:
            return False

    if card.card_type == CardType.INSTANT:
        # Instants can only be played in response to other cards
        return False  # Handled separately in neigh chain

    if card.card_type == CardType.DOWNGRADE:
        # Need a valid target (other player) to play downgrade
        other_players = state.get_other_players(player_idx)
        return len(other_players) > 0

    # Check if basic unicorns are blocked by Queen Bee
    if card.card_type == CardType.BASIC_UNICORN:
        for p in state.players:
            for c in p.stable:
                if c.card.effect_id == "queen_bee_unicorn" and p.player_idx != player_idx:
                    return False

    return True


def _get_neigh_actions(state: 'GameState') -> List[Action]:
    """Get Neigh-related actions when a card is being played."""
    actions: List[Action] = []

    # Find the next player who can respond
    for i in range(state.num_players):
        responder_idx = (state.current_player_idx + 1 + i) % state.num_players

        # Skip players who already passed
        if responder_idx in state.players_passed_on_neigh:
            continue

        # Skip the player who played the card
        if responder_idx == state.current_player_idx:
            continue

        responder = state.players[responder_idx]

        # Check if player can't play instants (Slowdown)
        if responder.cannot_play_instants:
            continue

        # Add pass option
        actions.append(Action(
            action_type=ActionType.PASS_NEIGH,
            player_idx=responder_idx
        ))

        # Add Neigh options for cards in hand
        for card in responder.hand:
            if card.card_type == CardType.INSTANT:
                actions.append(Action(
                    action_type=ActionType.NEIGH,
                    player_idx=responder_idx,
                    card=card
                ))

        # Only get actions for the first eligible responder
        break

    return actions


def _get_effect_choice_actions(state: 'GameState', action: Action) -> List[Action]:
    """Get actions for choosing targets for pending effects."""
    # ... (existing logic to setup) ...
    # This replacement replaces the whole function to handle player targets
    actions: List[Action] = []

    if not state.resolution_stack:
        return actions

    task = state.resolution_stack[-1]
    
    # Ensure we are within bounds
    if task.current_action_idx >= len(task.effect.actions):
        return actions # Should have been popped
        
    action_def = task.effect.actions[task.current_action_idx]
    
    # We are here because we need a target for this action
    target_type = action_def.target.target_type
    controller_idx = task.controller_idx
    
    # Get valid targets based on type
    valid_targets = _get_valid_targets(state, target_type, controller_idx)
    
    # If optional, add "None" action (Skip)
    if action_def.target.optional:
        actions.append(Action(
            action_type=ActionType.CHOOSE_TARGET,
            player_idx=controller_idx,
            target_card=None
        ))
        
    # Add action for each valid target
    for target in valid_targets:
        if isinstance(target, CardInstance):
            actions.append(Action(
                action_type=ActionType.CHOOSE_TARGET,
                player_idx=controller_idx,
                target_card=target
            ))
        elif hasattr(target, 'player_idx'): # PlayerState
            actions.append(Action(
                action_type=ActionType.CHOOSE_TARGET,
                player_idx=controller_idx,
                target_player_idx=target.player_idx
            ))
        
    # If mandatory but no targets, we must still allow resolving (as "failed to find target")
    if not actions and not action_def.target.optional:
         # Auto-fail / Skip
         actions.append(Action(
            action_type=ActionType.CHOOSE_TARGET,
            player_idx=controller_idx,
            target_card=None
        ))

    return actions


def _get_valid_targets(state: 'GameState', target_type: TargetType, controller_idx: int) -> List[Union[CardInstance, Any]]:
    """Helper to find all valid card or player targets for a given type."""
    valid = []
    player = state.players[controller_idx]
    
    if target_type == TargetType.OTHER_PLAYER:
        valid.extend(state.get_other_players(controller_idx))
    
    elif target_type == TargetType.ANY_PLAYER:
        valid.extend(state.players)
    
    elif target_type == TargetType.ANY_UNICORN:
        for p in state.players:
            # Check for protection (Pandamonium, etc)
            if p.unicorns_are_pandas:
                continue # Skip this player, their unicorns are pandas
            
            # Generally iterate stable
            for card in p.stable:
                 valid.append(card)
                 
    elif target_type == TargetType.OWN_UNICORN:
        for card in player.stable:
            valid.append(card)
            
    elif target_type == TargetType.OTHER_UNICORN:
        for p in state.get_other_players(controller_idx):
             for card in p.stable:
                 valid.append(card)
                 
    elif target_type == TargetType.ANY_UPGRADE:
        for p in state.players:
            valid.extend(p.upgrades)
            
    elif target_type == TargetType.OWN_UPGRADE:
        valid.extend(player.upgrades)
        
    elif target_type == TargetType.OTHER_UPGRADE:
        for p in state.get_other_players(controller_idx):
            valid.extend(p.upgrades)
            
    elif target_type == TargetType.ANY_DOWNGRADE:
        for p in state.players:
            valid.extend(p.downgrades)
            
    elif target_type == TargetType.OWN_DOWNGRADE:
        valid.extend(player.downgrades)
            
    elif target_type == TargetType.ANY_UPGRADE_OR_DOWNGRADE:
        for p in state.players:
            valid.extend(p.upgrades)
            valid.extend(p.downgrades)
            
    elif target_type == TargetType.OWN_CARD_IN_STABLE:
        valid.extend(player.get_all_stable_cards())
        
    elif target_type == TargetType.OTHER_CARD_IN_STABLE:
        for p in state.get_other_players(controller_idx):
            valid.extend(p.get_all_stable_cards())
            
    elif target_type == TargetType.ANY_CARD_IN_STABLE:
        for p in state.players:
            valid.extend(p.get_all_stable_cards())

    elif target_type == TargetType.CARD_IN_DISCARD:
        valid.extend(state.discard_pile)
        
    elif target_type == TargetType.BABY_UNICORN:
        # Usually from Nursery
        valid.extend(state.nursery)
        
    elif target_type == TargetType.OWN_HAND:
        valid.extend(player.hand)

    # TODO: Implement others as needed
    return valid


def apply_action(state: 'GameState', action: Action) -> 'GameState':
    """Apply an action to the game state and return the new state."""
    from game.game_state import GamePhase

    if action.action_type == ActionType.DRAW_CARD:
        num_cards = 1
        # Check for Double Dutch upgrade
        for upgrade in state.current_player.upgrades:
            if upgrade.card.effect_id == "double_dutch":
                num_cards = 2
                break

        state.draw_card(action.player_idx, num_cards)
        state.phase = GamePhase.ACTION
        # Check for Caffeine Overload
        state.actions_remaining = 1
        for upgrade in state.current_player.upgrades:
            if upgrade.card.effect_id == "caffeine_overload":
                state.actions_remaining = 2
                break

    elif action.action_type == ActionType.PLAY_CARD:
        _apply_play_card(state, action)

    elif action.action_type == ActionType.END_ACTION_PHASE:
        state.phase = GamePhase.END
        _process_end_of_turn(state)

    elif action.action_type == ActionType.NEIGH:
        _apply_neigh(state, action)

    elif action.action_type == ActionType.PASS_NEIGH:
        _apply_pass_neigh(state, action)

    elif action.action_type == ActionType.CHOOSE_TARGET:
        # User has chosen a target for the top stack item
        if state.resolution_stack:
            task = state.resolution_stack[-1]
            # Store the chosen target
            # Use append to match the index of the action
            # Wait, targets_chosen needs to correspond to action indices.
            # But the stack processing loop only asks for target if it hasn't one.
            # So we append this choice.
            task.targets_chosen.append(action.target_card)
            
            # Resume processing
            EffectHandler.process_stack(state)

    elif action.action_type == ActionType.DISCARD:
        if action.target_card:
            state.discard_card(action.target_card, action.player_idx)
            
        # Check if we need to discard more (Hand Limit Phase)
        if state.phase == GamePhase.DISCARD_TO_LIMIT:
            if len(state.current_player.hand) <= 7:
                state.phase = GamePhase.END
                _process_end_of_turn(state)
            
    # For standalone mechanics (if any are left that aren't effects)
    # Most mechanics are now handled via EffectHandler logic
    elif action.action_type == ActionType.BRING_BABY:
        # Legacy or manual action
        baby = state.get_baby_unicorn_from_nursery()
        if baby:
            state.add_to_stable(baby, action.player_idx)

    # Check win condition
    winner = state.check_win_condition()
    if winner is not None:
        state.winner = winner
        state.phase = GamePhase.GAME_OVER

    return state


def _apply_play_card(state: 'GameState', action: Action) -> None:
    """Apply playing a card from hand."""
    from game.game_state import GamePhase

    card = action.card
    player = state.players[action.player_idx]

    # Remove card from hand
    if card in player.hand:
        player.hand.remove(card)
    else:
        return  # Card not in hand, invalid action

    # Check if card can be Neigh'd
    if not player.cards_cannot_be_neighd:
        # Check if any player can Neigh
        any_can_neigh = False
        for p in state.players:
            if p.player_idx != action.player_idx and not p.cannot_play_instants:
                if any(c.card_type == CardType.INSTANT for c in p.hand):
                    any_can_neigh = True
                    break

        if any_can_neigh:
            # Start Neigh chain
            state.card_being_played = card
            state.neigh_chain_active = True
            state.players_passed_on_neigh = set()
            return

    # No Neigh possible, resolve the card
    _resolve_card(state, card, action.player_idx)
    state.actions_remaining -= 1


def _apply_neigh(state: 'GameState', action: Action) -> None:
    """Apply a Neigh card."""
    neigh_card = action.card
    player = state.players[action.player_idx]

    # Remove Neigh from hand
    if neigh_card in player.hand:
        player.hand.remove(neigh_card)

    # Check if it's Super Neigh (cannot be countered)
    if neigh_card.card.effect_id == "super_neigh":
        # Card is negated, goes to discard
        if state.card_being_played:
            state.discard_pile.append(state.card_being_played)
        state.discard_pile.append(neigh_card)
        state.card_being_played = None
        state.neigh_chain_active = False
        state.players_passed_on_neigh = set()
    else:
        # Regular Neigh - can be counter-Neigh'd
        original_card = state.card_being_played
        state.card_being_played = neigh_card
        state.players_passed_on_neigh = set()

        # Store the original card for resolution
        if not hasattr(state, 'neigh_stack'):
            state.neigh_stack = []
        state.neigh_stack.append(original_card)


def _apply_pass_neigh(state: 'GameState', action: Action) -> None:
    """Apply passing on Neigh opportunity."""
    state.players_passed_on_neigh.add(action.player_idx)

    # Check if all players have passed
    all_passed = True
    for p in state.players:
        if p.player_idx == state.current_player_idx:
            continue
        if p.player_idx not in state.players_passed_on_neigh:
            if not p.cannot_play_instants:
                if any(c.card_type == CardType.INSTANT for c in p.hand):
                    all_passed = False
                    break

    if all_passed:
        # Resolve the Neigh chain
        card = state.card_being_played

        # Check if there's a Neigh stack
        if hasattr(state, 'neigh_stack') and state.neigh_stack:
            if len(state.neigh_stack) % 2 == 0:
                original_card = state.neigh_stack[0]
                _resolve_card(state, original_card, state.current_player_idx)
            else:
                original_card = state.neigh_stack[0]
                state.discard_pile.append(original_card)

            for neigh in state.neigh_stack[1:]:
                state.discard_pile.append(neigh)
            if card:
                state.discard_pile.append(card)
            state.neigh_stack = []
        else:
            if card and card.card_type != CardType.INSTANT:
                _resolve_card(state, card, state.current_player_idx)
            elif card:
                pass

        state.card_being_played = None
        state.neigh_chain_active = False
        state.players_passed_on_neigh = set()
        # Only decrease actions if it was a PLAY_CARD that succeeded or failed
        # If it was a Neigh battle, actions_remaining was already decremented when play started? 
        # No, usually actions are decremented after resolution. 
        # But if countered, action is still used.
        state.actions_remaining -= 1


def _resolve_card(state: 'GameState', card: CardInstance, player_idx: int) -> None:
    """Resolve a card that has successfully been played."""
    if card.card_type == CardType.MAGIC:
        _trigger_effect(state, card, player_idx)
        state.discard_pile.append(card)

    elif card.card_type == CardType.UPGRADE:
        state.add_to_stable(card, player_idx)
        _update_player_flags(state, player_idx)

    elif card.card_type == CardType.DOWNGRADE:
        if action.target_player_idx is not None:
            target_idx = action.target_player_idx
            state.add_to_stable(card, target_idx)
            _update_player_flags(state, target_idx)
        else:
            # Fallback for legacy logic or if target not provided
            other_players = state.get_other_players(player_idx)
            if other_players:
                target_idx = other_players[0].player_idx
                state.add_to_stable(card, target_idx)
                _update_player_flags(state, target_idx)

    elif card.is_unicorn():
        state.add_to_stable(card, player_idx)
        _trigger_enter_events(state, card, player_idx)


def _trigger_effect(state: 'GameState', card: CardInstance, controller_idx: int) -> None:
    """Trigger a card's effect."""
    effect = EFFECT_REGISTRY.get(card.card.effect_id)
    if effect:
        state.resolution_stack.append(EffectTask(effect, controller_idx, card))
        EffectHandler.process_stack(state)


def _trigger_enter_events(state: 'GameState', card: CardInstance, controller_idx: int) -> None:
    """Trigger events when a card enters a stable."""
    from cards.effects import EffectTrigger
    
    # 1. Trigger the entering card's own ON_ENTER effect
    effect = EFFECT_REGISTRY.get(card.card.effect_id)
    if effect and effect.trigger == EffectTrigger.ON_ENTER:
        # Check for Blinding Light (negates effects of unicorns)
        if not (card.is_unicorn() and state.players[controller_idx].unicorns_are_basic):
            state.resolution_stack.append(EffectTask(effect, controller_idx, card))

    # 2. Trigger other cards that listen for entering cards (e.g., Barbed Wire)
    # Scan all players and their stables
    for player in state.players:
        for stable_card in player.get_all_stable_cards():
            listener_effect = EFFECT_REGISTRY.get(stable_card.card.effect_id)
            if listener_effect and listener_effect.trigger == EffectTrigger.ON_ENTER:
                # We need to distinguish between "Self Enter" (handled above) and "Other Enter"
                # The Effect definition usually implies "When THIS card enters" vs "When A card enters"
                # Our current Effect definition in cards/effects.py is slightly ambiguous on this.
                # Most listeners are "When a Unicorn enters..."
                
                # Hack: Skip if it's the card itself (already handled)
                if stable_card == card:
                    continue
                    
                # Check condition (e.g. "unicorn_enters")
                # For now, we manually check known listeners like Barbed Wire
                if stable_card.card.effect_id == "barbed_wire":
                    if card.is_unicorn() and player.player_idx == controller_idx:
                         state.resolution_stack.append(EffectTask(listener_effect, player.player_idx, stable_card))
                
                # Add other global listeners here as they are implemented

    EffectHandler.process_stack(state)


def _trigger_leave_events(state: 'GameState', card: CardInstance, previous_owner_idx: int) -> None:
    """Trigger events when a card leaves a stable."""
    from cards.effects import EffectTrigger
    
    # 1. Trigger the leaving card's own ON_LEAVE effect (e.g. Phoenix)
    effect = EFFECT_REGISTRY.get(card.card.effect_id)
    if effect and effect.trigger == EffectTrigger.ON_LEAVE:
        state.resolution_stack.append(EffectTask(effect, previous_owner_idx, card))

    # 2. Trigger listeners (Barbed Wire)
    player = state.players[previous_owner_idx]
    for stable_card in player.get_all_stable_cards():
        if stable_card == card: continue # Should be gone already but just in case
        
        listener_effect = EFFECT_REGISTRY.get(stable_card.card.effect_id)
        if listener_effect and stable_card.card.effect_id == "barbed_wire":
             if card.is_unicorn():
                 state.resolution_stack.append(EffectTask(listener_effect, previous_owner_idx, stable_card))
                 
    EffectHandler.process_stack(state)



def _process_end_of_turn(state: 'GameState') -> None:
    """Process end of turn effects and move to next player."""
    from game.game_state import GamePhase
    from cards.effects import EffectTrigger
    
    player = state.current_player
    player_idx = state.current_player_idx

    # Scan stable for END_OF_TURN triggers (e.g. Glitter Bomb)
    for card in player.get_all_stable_cards():
        effect = EFFECT_REGISTRY.get(card.card.effect_id)
        if effect and effect.trigger == EffectTrigger.END_OF_TURN:
             state.resolution_stack.append(EffectTask(effect, player_idx, card))

    # Process stack if any triggers found
    if state.resolution_stack:
        EffectHandler.process_stack(state)
        # Note: If stack requires interaction (e.g. Choose target to sacrifice),
        # the game loop will pause here and return to allow user to input action.
        # But we also need to handle the state transition AFTER resolution.
        # This is tricky: if we return, we are still in current player's turn?
        # We need a generic way to say "After stack empty, Advance Turn".
        # For now, we assume simple resolution or we might need a "PendingPhaseChange" state.
        
    # If stack is empty (or became empty), advance turn
    if not state.resolution_stack:
        state.current_player_idx = state.get_next_player_idx()
        state.turn_number += 1
        state.phase = GamePhase.BEGINNING
        state.actions_remaining = 1
        _process_beginning_of_turn(state)
    else:
        # We have pending interactions. We stay in END phase?
        # GameState needs to support this.
        # If we return, get_legal_actions will see resolution_stack and ask for targets.
        # But we need to know that AFTER that, we advance turn.
        pass


def _process_beginning_of_turn(state: 'GameState') -> None:
    """Process beginning of turn effects."""
    from game.game_state import GamePhase
    from cards.effects import EffectTrigger

    player = state.current_player
    player_idx = state.current_player_idx

    if player.unicorns_are_basic:
        state.phase = GamePhase.DRAW
        return

    # Scan stable for BEGINNING_OF_TURN triggers
    for card in player.get_all_stable_cards():
        effect = EFFECT_REGISTRY.get(card.card.effect_id)
        if effect and effect.trigger == EffectTrigger.BEGINNING_OF_TURN:
             state.resolution_stack.append(EffectTask(effect, player_idx, card))

    EffectHandler.process_stack(state)
    state.phase = GamePhase.DRAW


def _update_player_flags(state: 'GameState', player_idx: int) -> None:
    """Update player flags based on cards in their stable."""
    player = state.players[player_idx]

    player.hand_visible = False
    player.cannot_play_upgrades = False
    player.cannot_play_instants = False
    player.cards_cannot_be_neighd = False
    player.unicorns_cannot_be_destroyed = False
    player.unicorns_are_basic = False
    player.unicorns_are_pandas = False

    for card in player.upgrades:
        effect_id = card.card.effect_id
        if effect_id == "yay":
            player.cards_cannot_be_neighd = True
        elif effect_id == "rainbow_aura":
            player.unicorns_cannot_be_destroyed = True

    for card in player.downgrades:
        effect_id = card.card.effect_id
        if effect_id == "blinding_light":
            player.unicorns_are_basic = True
        elif effect_id == "broken_stable":
            player.cannot_play_upgrades = True
        elif effect_id == "slowdown":
            player.cannot_play_instants = True
        elif effect_id == "nanny_cam":
            player.hand_visible = True
        elif effect_id == "pandamonium":
            player.unicorns_are_pandas = True

    for card in player.stable:
        effect_id = card.card.effect_id
        if effect_id == "classy_narwhal":
            player.hand_visible = True