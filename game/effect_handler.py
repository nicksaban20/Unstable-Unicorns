"""Effect handler for Unstable Unicorns.

Processes the resolution stack, executing effect actions and managing targeting.
"""

from typing import List, Optional, Any, TYPE_CHECKING
import random

from cards.card import CardInstance, CardType
from cards.effects import Effect, EffectAction, ActionType, TargetType, EFFECT_REGISTRY, EffectTrigger
from game.game_state import GameState, EffectTask

if TYPE_CHECKING:
    from game.action import Action


class EffectHandler:
    """Handles the resolution of card effects."""

    @staticmethod
    def process_stack(state: GameState) -> None:
        """Process the top item on the resolution stack.
        
        This continues until:
        1. The stack is empty
        2. User input is required (targeting)
        """
        while state.resolution_stack:
            task = state.resolution_stack[-1]
            
            # Check effect-level condition
            if task.current_action_idx == 0 and task.effect.condition:
                if not EffectHandler._check_condition(state, task, task.effect.condition):
                    state.resolution_stack.pop()
                    continue

            # Check if we finished all actions in this effect
            if task.current_action_idx >= len(task.effect.actions):
                state.resolution_stack.pop()
                continue
                
            action_def = task.effect.actions[task.current_action_idx]
            
            # Check condition BEFORE asking for target
            if action_def.condition:
                if not EffectHandler._check_condition(state, task, action_def.condition):
                    # Condition failed, skip this action
                    if len(task.targets_chosen) <= task.current_action_idx:
                        task.targets_chosen.append(None)
                    task.current_action_idx += 1
                    continue

            # Check if we need a target for this specific action
            if len(task.targets_chosen) <= task.current_action_idx:
                needs_target = True
                
                # Check for auto-resolvable types
                if action_def.target.target_type == TargetType.NONE or \
                   action_def.target.target_type == TargetType.SELF or \
                   action_def.target.target_type == TargetType.CONTROLLER:
                    needs_target = False
                    
                # Check for "All" value which implies auto-resolution for some types
                if action_def.value == -1:
                    needs_target = False
                
                if needs_target:
                    # We need a target. Stop processing and wait for ActionType.CHOOSE_TARGET
                    return
                
                # If no target needed (SELF, NONE, CONTROLLER, or AUTO), perform action immediately
                EffectHandler._execute_action(state, task, action_def, None)
                # Store placeholder target to keep index alignment
                task.targets_chosen.append(None) 
                task.current_action_idx += 1
            else:
                # We have a target (provided by user previously)
                target = task.targets_chosen[task.current_action_idx]
                EffectHandler._execute_action(state, task, action_def, target)
                task.current_action_idx += 1

    @staticmethod
    def _execute_action(state: GameState, task: EffectTask, action_def: EffectAction, target: Any) -> None:
        """Execute a single effect action."""
        
        # Resolve target if SELF or CONTROLLER
        if target is None:
            if action_def.target.target_type == TargetType.SELF:
                target = task.source_card
            elif action_def.target.target_type == TargetType.CONTROLLER:
                pass

        act_type = action_def.action_type
        
        if act_type == ActionType.DRAW:
            count = action_def.value
            state.draw_card(task.controller_idx, count)
            
        elif act_type == ActionType.DISCARD:
            if action_def.value == -1:
                player = state.players[task.controller_idx]
                cards_to_discard = list(player.hand)
                for card in cards_to_discard:
                    state.discard_card(card, task.controller_idx)
                setattr(task, 'last_action_was_discard', True)
            elif target and isinstance(target, CardInstance):
                state.discard_card(target, state.find_card_owner(target))
                setattr(task, 'last_action_was_discard', True)
            elif action_def.target.target_type == TargetType.CONTROLLER:
                pass
                
        elif act_type == ActionType.DESTROY:
            if target and isinstance(target, CardInstance):
                owner = state.find_card_owner(target)
                if owner is not None:
                    # Check immunities
                    target_player = state.players[owner]
                    if target_player.unicorns_cannot_be_destroyed and target.is_unicorn():
                        pass # Protected
                    elif target.card.effect_id == "magical_kittencorn":
                        pass # Protected
                    else:
                        state.remove_from_stable(target, owner)
                        task.last_action_was_destroy = True
                        EffectHandler.trigger_leave_events(state, target, owner)

        elif act_type == ActionType.SACRIFICE:
            if target and isinstance(target, CardInstance):
                state.remove_from_stable(target, task.controller_idx)
                setattr(task, 'last_action_was_sacrifice', True)
                EffectHandler.trigger_leave_events(state, target, task.controller_idx)

        elif act_type == ActionType.STEAL:
            if target and isinstance(target, CardInstance):
                owner = state.find_card_owner(target)
                if owner is not None:
                    state.remove_from_stable(target, owner)
                    if state.discard_pile and state.discard_pile[-1] == target:
                        state.discard_pile.pop() 
                    state.add_to_stable(target, task.controller_idx)
                    EffectHandler.trigger_enter_events(state, target, task.controller_idx)

        elif act_type == ActionType.RETURN_TO_HAND:
            if target and isinstance(target, CardInstance):
                owner = state.find_card_owner(target)
                if owner is not None:
                    state.remove_from_stable(target, owner)
                    if state.discard_pile and state.discard_pile[-1] == target:
                        state.discard_pile.pop() 
                    state.players[owner].hand.append(target)
                    EffectHandler.trigger_leave_events(state, target, owner)
                    
        elif act_type == ActionType.BRING_TO_STABLE:
            if target and isinstance(target, CardInstance):
                if target in state.discard_pile:
                    state.discard_pile.remove(target)
                elif target in state.nursery:
                    state.nursery.remove(target)
                
                state.add_to_stable(target, task.controller_idx)
                EffectHandler.trigger_enter_events(state, target, task.controller_idx)


        elif act_type == ActionType.SEARCH_DECK:
            if target and isinstance(target, CardInstance):
                if target in state.draw_pile:
                    state.draw_pile.remove(target)
                    state.players[task.controller_idx].hand.append(target)
                    random.shuffle(state.draw_pile)

        elif act_type == ActionType.SWAP:
            if len(task.targets_chosen) >= 2:
                card1 = task.targets_chosen[-2]
                card2 = task.targets_chosen[-1]
                
                if isinstance(card1, CardInstance) and isinstance(card2, CardInstance):
                    owner1 = state.find_card_owner(card1)
                    owner2 = state.find_card_owner(card2)
                    
                    if owner1 is not None and owner2 is not None:
                        # Perform Swap
                        state.remove_from_stable(card1, owner1)
                        if state.discard_pile and state.discard_pile[-1] == card1: state.discard_pile.pop()
                        
                        state.remove_from_stable(card2, owner2)
                        if state.discard_pile and state.discard_pile[-1] == card2: state.discard_pile.pop()
                        
                        state.add_to_stable(card1, owner2)
                        state.add_to_stable(card2, owner1)

        elif act_type == ActionType.SHUFFLE_INTO_DECK:
            if target and isinstance(target, CardInstance):
                owner = state.find_card_owner(target)
                if owner is not None:
                    if target in state.players[owner].hand:
                        state.players[owner].hand.remove(target)
                    else:
                        state.remove_from_stable(target, owner)
                        if state.discard_pile and state.discard_pile[-1] == target:
                            state.discard_pile.pop()
                    
                    state.draw_pile.append(target)
                    random.shuffle(state.draw_pile)

        elif act_type == ActionType.PULL_FROM_HAND:
            if target and isinstance(target, CardInstance):
                 owner = state.find_card_owner(target)
                 if owner is not None:
                     state.players[owner].hand.remove(target)
                     state.players[task.controller_idx].hand.append(target)
            elif isinstance(target, int):
                target_player = state.players[target]
                if target_player.hand:
                    card = random.choice(target_player.hand)
                    target_player.hand.remove(card)
                    state.players[task.controller_idx].hand.append(card)

        elif act_type == ActionType.LOOK_AT_HAND:
            pass
            
        elif act_type == ActionType.ADD_TO_HAND:
            if target and isinstance(target, CardInstance):
                # Remove from source (Discard, Stable, etc)
                if target in state.discard_pile:
                    state.discard_pile.remove(target)
                elif target in state.nursery:
                    # Should be BRING_TO_STABLE usually, but if hand...
                    state.nursery.remove(target)
                # Note: If stealing from stable, use STEAL/RETURN_TO_HAND.
                
                state.players[task.controller_idx].hand.append(target)

        elif act_type == ActionType.SELECT:
            pass


    @staticmethod
    def _check_condition(state: GameState, task: EffectTask, condition: str) -> bool:
        """Check if a condition is met."""
        if condition == "if_sacrificed":
            return getattr(task, 'last_action_was_sacrifice', False)

        if condition == "if_discarded":
             return getattr(task, 'last_action_was_discard', False)

        if condition == "unicorn_card":
             return True

        if condition == "if_downgrade_in_stable":
             player = state.players[task.controller_idx]
             return len(player.downgrades) > 0

        if condition == "if_no_baby_unicorns":
            player = state.players[task.controller_idx]
            # Check if player has any baby unicorns in stable
            from cards.card import CardType
            for card in player.stable:
                if card.card_type == CardType.BABY_UNICORN:
                    return False
            return True

        if condition == "magic_card":
            # For search conditions - handled at search time
            return True

        if condition == "narwhal_card":
            # For search conditions - handled at search time
            return True

        return True

    @staticmethod
    def trigger_enter_events(state: GameState, card: CardInstance, controller_idx: int) -> None:
        """Trigger events when a card enters a stable."""
        
        # 1. Trigger the entering card's own ON_ENTER effect
        effect = EFFECT_REGISTRY.get(card.card.effect_id)
        if effect and effect.trigger == EffectTrigger.ON_ENTER:
            # Check for Blinding Light (negates effects of unicorns)
            if not (card.is_unicorn() and state.players[controller_idx].unicorns_are_basic):
                state.resolution_stack.append(EffectTask(effect, controller_idx, card))

        # 2. Trigger other cards that listen for entering cards (e.g., Barbed Wire)
        for player in state.players:
            for stable_card in player.get_all_stable_cards():
                listener_effect = EFFECT_REGISTRY.get(stable_card.card.effect_id)
                if listener_effect and listener_effect.trigger == EffectTrigger.ON_ENTER:
                    if stable_card == card:
                        continue
                        
                    # Hack: Manual check for Barbed Wire for now
                    if stable_card.card.effect_id == "barbed_wire":
                        if card.is_unicorn() and player.player_idx == controller_idx:
                             state.resolution_stack.append(EffectTask(listener_effect, player.player_idx, stable_card))

    @staticmethod
    def trigger_leave_events(state: GameState, card: CardInstance, previous_owner_idx: int) -> None:
        """Trigger events when a card leaves a stable."""
        
        # 1. Trigger the leaving card's own ON_LEAVE effect (e.g. Phoenix)
        effect = EFFECT_REGISTRY.get(card.card.effect_id)
        if effect and effect.trigger == EffectTrigger.ON_LEAVE:
            state.resolution_stack.append(EffectTask(effect, previous_owner_idx, card))

        # 2. Trigger listeners (Barbed Wire)
        player = state.players[previous_owner_idx]
        for stable_card in player.get_all_stable_cards():
            if stable_card == card: continue
            
            listener_effect = EFFECT_REGISTRY.get(stable_card.card.effect_id)
            if listener_effect and stable_card.card.effect_id == "barbed_wire":
                 if card.is_unicorn():
                     state.resolution_stack.append(EffectTask(listener_effect, previous_owner_idx, stable_card))
