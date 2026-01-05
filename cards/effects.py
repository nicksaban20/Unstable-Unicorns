"""Effect system for Unstable Unicorns card abilities."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from game.game_state import GameState
    from cards.card import CardInstance


class EffectTrigger(Enum):
    """When an effect triggers."""
    NONE = auto()
    ON_ENTER = auto()          # When card enters a stable
    ON_LEAVE = auto()          # When card leaves a stable
    BEGINNING_OF_TURN = auto() # Beginning of turn phase
    END_OF_TURN = auto()       # End of turn phase
    CONTINUOUS = auto()        # Always active while in stable
    ON_PLAY = auto()           # When magic card is played
    INSTANT = auto()           # Can interrupt (Neigh cards)


class TargetType(Enum):
    """Types of valid targets for effects."""
    NONE = auto()
    SELF = auto()                     # The card itself
    CONTROLLER = auto()               # Player who controls this card
    ANY_PLAYER = auto()               # Any player
    OTHER_PLAYER = auto()             # Any player except controller
    ANY_UNICORN = auto()              # Any unicorn in any stable
    OWN_UNICORN = auto()              # Unicorn in controller's stable
    OTHER_UNICORN = auto()            # Unicorn not in controller's stable
    ANY_CARD_IN_STABLE = auto()       # Any card in any stable
    OWN_CARD_IN_STABLE = auto()       # Card in controller's stable
    OTHER_CARD_IN_STABLE = auto()     # Card not in controller's stable
    ANY_UPGRADE = auto()              # Any upgrade card
    OWN_UPGRADE = auto()              # Upgrade in controller's stable
    OTHER_UPGRADE = auto()            # Upgrade not in controller's stable
    ANY_DOWNGRADE = auto()            # Any downgrade card
    OWN_DOWNGRADE = auto()            # Downgrade in controller's stable
    ANY_UPGRADE_OR_DOWNGRADE = auto() # Any upgrade or downgrade
    CARD_IN_HAND = auto()             # Card in a player's hand
    OWN_HAND = auto()                 # Card in controller's hand
    OTHER_HAND = auto()               # Card in another player's hand
    CARD_IN_DISCARD = auto()          # Card in discard pile
    CARD_IN_DECK = auto()             # Card in draw pile
    BABY_UNICORN = auto()             # Baby unicorn in nursery


class ActionType(Enum):
    """Types of actions effects can perform."""
    DESTROY = auto()          # Send card to discard
    SACRIFICE = auto()        # Owner sends own card to discard
    STEAL = auto()            # Take card from another player
    RETURN_TO_HAND = auto()   # Return card to owner's hand
    DISCARD = auto()          # Discard from hand
    DRAW = auto()             # Draw cards
    SEARCH_DECK = auto()      # Search deck for specific card
    BRING_TO_STABLE = auto()  # Bring card to stable (from hand, discard, etc.)
    SWAP = auto()             # Swap cards between players
    LOOK_AT_HAND = auto()     # View another player's hand
    PULL_FROM_HAND = auto()   # Take random card from hand
    SHUFFLE_INTO_DECK = auto() # Shuffle card into deck
    SKIP_TURN = auto()        # Skip current turn
    EXTRA_ACTION = auto()     # Gain extra action
    PROTECT = auto()          # Protect from effects
    NEGATE = auto()           # Negate/counter a card
    SELECT = auto()           # Select a target (for multi-step effects)
    ADD_TO_HAND = auto()      # Add target card to controller's hand


@dataclass
class EffectTarget:
    """Represents a target for an effect."""
    target_type: TargetType
    count: int = 1            # How many targets needed
    optional: bool = False    # Whether targeting is optional ("you may")
    controller_chooses: bool = True  # Who chooses the target


@dataclass
class EffectAction:
    """A single action within an effect."""
    action_type: ActionType
    target: EffectTarget
    value: int = 1            # Amount (cards to draw, etc.)
    condition: Optional[str] = None  # Condition that must be met


@dataclass
class Effect:
    """Represents a card's effect.

    Effects can have multiple triggers and actions.
    """
    effect_id: str
    name: str
    trigger: EffectTrigger
    actions: List[EffectAction] = field(default_factory=list)
    description: str = ""

    # For continuous effects
    modifies_rules: bool = False
    rule_modifier: Optional[str] = None

    # For conditional effects
    condition: Optional[str] = None  # e.g., "if_unicorn_count_gte_3"

    def requires_target(self) -> bool:
        """Check if this effect requires player to choose targets."""
        return any(
            action.target.target_type != TargetType.NONE
            and action.target.target_type != TargetType.SELF
            for action in self.actions
        )


class EffectRegistry:
    """Registry of all card effects.

    Maps effect_id to Effect objects for lookup during gameplay.
    """

    def __init__(self):
        self._effects: Dict[str, Effect] = {}
        self._register_base_effects()

    def register(self, effect: Effect) -> None:
        """Register an effect."""
        self._effects[effect.effect_id] = effect

    def get(self, effect_id: str) -> Optional[Effect]:
        """Get an effect by ID."""
        return self._effects.get(effect_id)

    def _register_base_effects(self) -> None:
        """Register all base game effects."""

        # === INSTANT EFFECTS ===

        self.register(Effect(
            effect_id="neigh",
            name="Neigh",
            trigger=EffectTrigger.INSTANT,
            actions=[
                EffectAction(
                    action_type=ActionType.NEGATE,
                    target=EffectTarget(TargetType.NONE),
                )
            ],
            description="Stop a card from being played and send it to discard."
        ))

        self.register(Effect(
            effect_id="super_neigh",
            name="Super Neigh",
            trigger=EffectTrigger.INSTANT,
            actions=[
                EffectAction(
                    action_type=ActionType.NEGATE,
                    target=EffectTarget(TargetType.NONE),
                )
            ],
            description="Stop a card from being played. Cannot be Neigh'd."
        ))

        # === MAGICAL UNICORN EFFECTS ===

        self.register(Effect(
            effect_id="rhinocorn",
            name="Rhinocorn",
            trigger=EffectTrigger.BEGINNING_OF_TURN,
            actions=[
                EffectAction(
                    action_type=ActionType.DESTROY,
                    target=EffectTarget(
                        TargetType.ANY_UNICORN,
                        optional=True
                    ),
                ),
                EffectAction(
                    action_type=ActionType.SKIP_TURN,
                    target=EffectTarget(TargetType.CONTROLLER),
                    condition="if_destroyed"
                )
            ],
            description="You may DESTROY a Unicorn card. If you do, immediately end your turn."
        ))

        self.register(Effect(
            effect_id="chainsaw_unicorn",
            name="Chainsaw Unicorn",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.DESTROY,
                    target=EffectTarget(
                        TargetType.ANY_UPGRADE,
                        optional=True
                    ),
                ),
            ],
            description="You may DESTROY an Upgrade card or SACRIFICE a Downgrade card."
        ))

        self.register(Effect(
            effect_id="stabby_the_unicorn",
            name="Stabby the Unicorn",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.SACRIFICE,
                    target=EffectTarget(TargetType.OWN_CARD_IN_STABLE),
                ),
                EffectAction(
                    action_type=ActionType.DESTROY,
                    target=EffectTarget(TargetType.ANY_UNICORN),
                )
            ],
            description="When this card enters your Stable, you must SACRIFICE a card, then DESTROY a Unicorn card."
        ))

        self.register(Effect(
            effect_id="unicorn_phoenix",
            name="Unicorn Phoenix",
            trigger=EffectTrigger.ON_LEAVE,
            actions=[
                EffectAction(
                    action_type=ActionType.DISCARD,
                    target=EffectTarget(TargetType.OWN_HAND),
                ),
                EffectAction(
                    action_type=ActionType.BRING_TO_STABLE,
                    target=EffectTarget(TargetType.SELF),
                    condition="if_discarded"
                )
            ],
            description="If this card would be sacrificed or destroyed, you may DISCARD a card instead. If you do, this card returns to your Stable."
        ))

        self.register(Effect(
            effect_id="rainbow_unicorn",
            name="Rainbow Unicorn",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.BRING_TO_STABLE,
                    target=EffectTarget(TargetType.BABY_UNICORN),
                )
            ],
            description="When this card enters your Stable, bring a Baby Unicorn from the Nursery directly to your Stable."
        ))

        self.register(Effect(
            effect_id="queen_bee_unicorn",
            name="Queen Bee Unicorn",
            trigger=EffectTrigger.CONTINUOUS,
            modifies_rules=True,
            rule_modifier="basic_unicorns_cannot_enter_other_stables",
            description="Basic Unicorn cards cannot enter any other player's Stable."
        ))

        self.register(Effect(
            effect_id="seductive_unicorn",
            name="Seductive Unicorn",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.SACRIFICE,
                    target=EffectTarget(TargetType.OWN_UNICORN),
                ),
                EffectAction(
                    action_type=ActionType.STEAL,
                    target=EffectTarget(TargetType.OTHER_UNICORN),
                    condition="if_sacrificed"
                )
            ],
            description="When this card enters your Stable, SACRIFICE a Unicorn card, then STEAL a Unicorn card."
        ))

        self.register(Effect(
            effect_id="greedy_flying_unicorn",
            name="Greedy Flying Unicorn",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.DRAW,
                    target=EffectTarget(TargetType.CONTROLLER),
                    value=1
                )
            ],
            description="When this card enters your Stable, DRAW a card."
        ))

        self.register(Effect(
            effect_id="magical_flying_unicorn",
            name="Magical Flying Unicorn",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.SEARCH_DECK,
                    target=EffectTarget(TargetType.CARD_IN_DECK),
                    condition="magic_card"
                )
            ],
            description="When this card enters your Stable, search the deck for a Magic card. Add it to your hand, then shuffle the deck."
        ))

        self.register(Effect(
            effect_id="swift_flying_unicorn",
            name="Swift Flying Unicorn",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.RETURN_TO_HAND,
                    target=EffectTarget(TargetType.ANY_CARD_IN_STABLE),
                )
            ],
            description="When this card enters your Stable, you may choose a card in any Stable and return it to that player's hand."
        ))

        self.register(Effect(
            effect_id="annoying_flying_unicorn",
            name="Annoying Flying Unicorn",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.DISCARD,
                    target=EffectTarget(TargetType.ANY_PLAYER),
                    value=1
                )
            ],
            description="When this card enters your Stable, choose any player. That player must DISCARD a card."
        ))

        self.register(Effect(
            effect_id="majestic_flying_unicorn",
            name="Majestic Flying Unicorn",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.SEARCH_DECK,
                    target=EffectTarget(TargetType.CARD_IN_DECK),
                    condition="unicorn_card"
                )
            ],
            description="When this card enters your Stable, search the deck for a Unicorn card. Add it to your hand, then shuffle the deck."
        ))

        self.register(Effect(
            effect_id="extremely_destructive_unicorn",
            name="Extremely Destructive Unicorn",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.DESTROY,
                    target=EffectTarget(TargetType.ANY_UPGRADE_OR_DOWNGRADE),
                    value=-1  # All
                )
            ],
            description="When this card enters your Stable, each player must DESTROY an Upgrade card in their Stable."
        ))

        self.register(Effect(
            effect_id="alluring_narwhal",
            name="Alluring Narwhal",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.STEAL,
                    target=EffectTarget(
                        TargetType.OTHER_UPGRADE,
                        optional=True
                    ),
                )
            ],
            description="When this card enters your Stable, you may STEAL an Upgrade card."
        ))

        self.register(Effect(
            effect_id="shark_with_a_horn",
            name="Shark With a Horn",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.DESTROY,
                    target=EffectTarget(TargetType.OTHER_UNICORN),
                )
            ],
            condition="if_downgrade_in_stable",
            description="When this card enters your Stable, you may DESTROY a Unicorn card. This power only works if you have a Downgrade card in your Stable."
        ))

        self.register(Effect(
            effect_id="narwhal_torpedo",
            name="Narwhal Torpedo",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.SACRIFICE,
                    target=EffectTarget(TargetType.SELF),
                ),
                EffectAction(
                    action_type=ActionType.DESTROY,
                    target=EffectTarget(TargetType.OTHER_UNICORN),
                )
            ],
            description="When this card enters your Stable, you may SACRIFICE this card. If you do, DESTROY a Unicorn card."
        ))

        self.register(Effect(
            effect_id="the_great_narwhal",
            name="The Great Narwhal",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.SEARCH_DECK,
                    target=EffectTarget(TargetType.CARD_IN_DECK),
                    condition="narwhal_card"
                )
            ],
            description="When this card enters your Stable, search the deck for a card with 'Narwhal' in its name. Add it to your hand, then shuffle the deck."
        ))

        self.register(Effect(
            effect_id="unicorn_on_the_cob",
            name="Unicorn on the Cob",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.DRAW,
                    target=EffectTarget(TargetType.CONTROLLER),
                    value=2
                ),
                EffectAction(
                    action_type=ActionType.DISCARD,
                    target=EffectTarget(TargetType.OWN_HAND),
                    value=1
                )
            ],
            description="When this card enters your Stable, DRAW 2 cards and DISCARD a card."
        ))

        self.register(Effect(
            effect_id="ginormous_unicorn",
            name="Ginormous Unicorn",
            trigger=EffectTrigger.CONTINUOUS,
            modifies_rules=True,
            rule_modifier="counts_as_two_unicorns",
            description="This card counts as 2 Unicorns."
        ))

        self.register(Effect(
            effect_id="llamacorn",
            name="Llamacorn",
            trigger=EffectTrigger.BEGINNING_OF_TURN,
            actions=[
                EffectAction(
                    action_type=ActionType.DISCARD,
                    target=EffectTarget(TargetType.CONTROLLER),
                    value=1
                ),
                EffectAction(
                    action_type=ActionType.DESTROY,
                    target=EffectTarget(TargetType.OTHER_CARD_IN_STABLE),
                    condition="if_discarded"
                )
            ],
            description="At the beginning of your turn, you may DISCARD a card. If you do, DESTROY a card in another player's Stable."
        ))

        self.register(Effect(
            effect_id="americorn",
            name="Americorn",
            trigger=EffectTrigger.BEGINNING_OF_TURN,
            actions=[
                EffectAction(
                    action_type=ActionType.PULL_FROM_HAND,
                    target=EffectTarget(TargetType.OTHER_PLAYER),
                )
            ],
            description="At the beginning of your turn, you may pull a card at random from another player's hand. If you do, skip your Draw phase."
        ))

        self.register(Effect(
            effect_id="black_knight_unicorn",
            name="Black Knight Unicorn",
            trigger=EffectTrigger.CONTINUOUS,
            modifies_rules=True,
            rule_modifier="sacrifice_instead_of_other_unicorn",
            description="If 1 of your Unicorns would be destroyed, you may SACRIFICE this card instead."
        ))

        self.register(Effect(
            effect_id="dark_angel_unicorn",
            name="Dark Angel Unicorn",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.BRING_TO_STABLE,
                    target=EffectTarget(TargetType.CARD_IN_DISCARD),
                    condition="unicorn_card"
                )
            ],
            description="When this card enters your Stable, choose a Unicorn card from the discard pile and add it to your hand."
        ))

        self.register(Effect(
            effect_id="mermaid_unicorn",
            name="Mermaid Unicorn",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.RETURN_TO_HAND,
                    target=EffectTarget(TargetType.OWN_CARD_IN_STABLE),
                )
            ],
            description="When this card enters your Stable, return a card in your Stable to your hand. If this card is sacrificed or destroyed, return it to your hand instead of moving it to the discard pile."
        ))

        self.register(Effect(
            effect_id="mother_goose_unicorn",
            name="Mother Goose Unicorn",
            trigger=EffectTrigger.BEGINNING_OF_TURN,
            actions=[
                EffectAction(
                    action_type=ActionType.BRING_TO_STABLE,
                    target=EffectTarget(TargetType.BABY_UNICORN),
                )
            ],
            condition="if_no_baby_unicorns",
            description="If this card is in your Stable at the beginning of your turn, and you have no Baby Unicorns in your Stable, bring a Baby Unicorn from the Nursery directly to your Stable."
        ))

        self.register(Effect(
            effect_id="unicorn_oracle",
            name="Unicorn Oracle",
            trigger=EffectTrigger.BEGINNING_OF_TURN,
            actions=[
                EffectAction(
                    action_type=ActionType.LOOK_AT_HAND,
                    target=EffectTarget(TargetType.ANY_PLAYER),
                )
            ],
            description="If this card is in your Stable at the beginning of your turn, look at the top 3 cards of the deck. You may put those cards back on the top or bottom of the deck in any order."
        ))

        self.register(Effect(
            effect_id="necromancer_unicorn",
            name="Necromancer Unicorn",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.SACRIFICE,
                    target=EffectTarget(TargetType.OWN_UNICORN),
                    value=2
                ),
                EffectAction(
                    action_type=ActionType.BRING_TO_STABLE,
                    target=EffectTarget(TargetType.CARD_IN_DISCARD),
                    condition="unicorn_card"
                )
            ],
            description="When this card enters your Stable, you may SACRIFICE 2 Unicorn cards. If you do, choose a Unicorn card from the discard pile and bring it directly into your Stable."
        ))

        self.register(Effect(
            effect_id="magical_kittencorn",
            name="Magical Kittencorn",
            trigger=EffectTrigger.CONTINUOUS,
            modifies_rules=True,
            rule_modifier="cannot_be_destroyed",
            description="This card cannot be destroyed."
        ))

        self.register(Effect(
            effect_id="classy_narwhal",
            name="Classy Narwhal",
            trigger=EffectTrigger.CONTINUOUS,
            modifies_rules=True,
            rule_modifier="hand_visible",
            description="Your hand must be visible to all players at all times."
        ))

        self.register(Effect(
            effect_id="shabby_the_narwhal",
            name="Shabby the Narwhal",
            trigger=EffectTrigger.CONTINUOUS,
            modifies_rules=True,
            rule_modifier="downgrades_immune",
            description="This card cannot be affected by Downgrade cards."
        ))

        # === UPGRADE EFFECTS ===

        self.register(Effect(
            effect_id="rainbow_aura",
            name="Rainbow Aura",
            trigger=EffectTrigger.CONTINUOUS,
            modifies_rules=True,
            rule_modifier="unicorns_cannot_be_destroyed",
            description="Your Unicorn cards cannot be destroyed."
        ))

        self.register(Effect(
            effect_id="yay",
            name="Yay",
            trigger=EffectTrigger.CONTINUOUS,
            modifies_rules=True,
            rule_modifier="cards_cannot_be_neighd",
            description="Cards you play cannot be Neigh'd."
        ))

        self.register(Effect(
            effect_id="double_dutch",
            name="Double Dutch",
            trigger=EffectTrigger.CONTINUOUS,
            modifies_rules=True,
            rule_modifier="draw_extra_card",
            description="If this card is in your Stable at the beginning of your turn, you may DRAW an extra card during your Draw phase."
        ))

        self.register(Effect(
            effect_id="glitter_bomb",
            name="Glitter Bomb",
            trigger=EffectTrigger.END_OF_TURN,
            actions=[
                EffectAction(
                    action_type=ActionType.SACRIFICE,
                    target=EffectTarget(TargetType.OWN_CARD_IN_STABLE),
                ),
                EffectAction(
                    action_type=ActionType.DESTROY,
                    target=EffectTarget(TargetType.OTHER_CARD_IN_STABLE),
                    condition="if_sacrificed"
                )
            ],
            description="At the end of your turn, you may SACRIFICE a card. If you do, DESTROY a card."
        ))

        self.register(Effect(
            effect_id="rainbow_lasso",
            name="Rainbow Lasso",
            trigger=EffectTrigger.BEGINNING_OF_TURN,
            actions=[
                EffectAction(
                    action_type=ActionType.STEAL,
                    target=EffectTarget(TargetType.OTHER_UNICORN),
                ),
                EffectAction(
                    action_type=ActionType.SACRIFICE,
                    target=EffectTarget(TargetType.SELF),
                )
            ],
            description="If this card is in your Stable at the beginning of your turn, STEAL a Unicorn card, then SACRIFICE this card."
        ))

        self.register(Effect(
            effect_id="claw_machine",
            name="Claw Machine",
            trigger=EffectTrigger.BEGINNING_OF_TURN,
            actions=[
                EffectAction(
                    action_type=ActionType.ADD_TO_HAND,
                    target=EffectTarget(
                        TargetType.CARD_IN_DISCARD,
                        optional=True
                    ),
                )
            ],
            description="If this card is in your Stable at the beginning of your turn, you may take a card from the discard pile and add it to your hand."
        ))

        self.register(Effect(
            effect_id="stable_artillery",
            name="Stable Artillery",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(
                    action_type=ActionType.SACRIFICE,
                    target=EffectTarget(TargetType.OWN_UNICORN),
                ),
                EffectAction(
                    action_type=ActionType.DESTROY,
                    target=EffectTarget(TargetType.OTHER_UNICORN),
                    condition="if_sacrificed"
                )
            ],
            description="You may SACRIFICE a Unicorn card. If you do, DESTROY a Unicorn card."
        ))

        self.register(Effect(
            effect_id="caffeine_overload",
            name="Caffeine Overload",
            trigger=EffectTrigger.CONTINUOUS,
            modifies_rules=True,
            rule_modifier="extra_action",
            description="If this card is in your Stable at the beginning of your turn, you may play 2 cards during your Action phase."
        ))

        # === DOWNGRADE EFFECTS ===

        self.register(Effect(
            effect_id="blinding_light",
            name="Blinding Light",
            trigger=EffectTrigger.CONTINUOUS,
            modifies_rules=True,
            rule_modifier="unicorns_considered_basic",
            description="All of your Unicorn cards are considered Basic Unicorns with no effects."
        ))

        self.register(Effect(
            effect_id="barbed_wire",
            name="Barbed Wire",
            trigger=EffectTrigger.ON_ENTER,
            actions=[
                EffectAction(
                    action_type=ActionType.DESTROY,
                    target=EffectTarget(TargetType.OWN_UNICORN),
                )
            ],
            description="Each time a Unicorn card enters or leaves your Stable, DESTROY a Unicorn card."
        ))

        self.register(Effect(
            effect_id="broken_stable",
            name="Broken Stable",
            trigger=EffectTrigger.CONTINUOUS,
            modifies_rules=True,
            rule_modifier="cannot_play_upgrades",
            description="You cannot play Upgrade cards."
        ))

        self.register(Effect(
            effect_id="pandamonium",
            name="Pandamonium",
            trigger=EffectTrigger.CONTINUOUS,
            modifies_rules=True,
            rule_modifier="unicorns_are_pandas",
            description="All of your Unicorns are considered Pandas. Cards that affect Unicorn cards do not affect your Pandas."
        ))

        self.register(Effect(
            effect_id="sadistic_ritual",
            name="Sadistic Ritual",
            trigger=EffectTrigger.BEGINNING_OF_TURN,
            actions=[
                EffectAction(
                    action_type=ActionType.SACRIFICE,
                    target=EffectTarget(TargetType.OWN_UNICORN),
                ),
                EffectAction(
                    action_type=ActionType.DRAW,
                    target=EffectTarget(TargetType.CONTROLLER),
                    value=1,
                    condition="if_sacrificed"
                )
            ],
            description="At the beginning of your turn, SACRIFICE a Unicorn card, then DRAW a card."
        ))

        self.register(Effect(
            effect_id="slowdown",
            name="Slowdown",
            trigger=EffectTrigger.CONTINUOUS,
            modifies_rules=True,
            rule_modifier="cannot_play_instant",
            description="You cannot play Instant cards."
        ))

        self.register(Effect(
            effect_id="nanny_cam",
            name="Nanny Cam",
            trigger=EffectTrigger.CONTINUOUS,
            modifies_rules=True,
            rule_modifier="hand_visible",
            description="Your hand must be visible to all players at all times."
        ))

        self.register(Effect(
            effect_id="tiny_stable",
            name="Tiny Stable",
            trigger=EffectTrigger.CONTINUOUS,
            modifies_rules=True,
            rule_modifier="max_five_unicorns",
            description="If at any time you have more than 5 Unicorns in your Stable, SACRIFICE a Unicorn card."
        ))

        # === MAGIC CARD EFFECTS ===

        self.register(Effect(
            effect_id="back_kick",
            name="Back Kick",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(
                    action_type=ActionType.RETURN_TO_HAND,
                    target=EffectTarget(TargetType.ANY_CARD_IN_STABLE),
                )
            ],
            description="Return a card in another player's Stable to their hand."
        ))

        self.register(Effect(
            effect_id="blatant_thievery",
            name="Blatant Thievery",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(
                    action_type=ActionType.LOOK_AT_HAND,
                    target=EffectTarget(TargetType.OTHER_PLAYER),
                ),
                EffectAction(
                    action_type=ActionType.STEAL,
                    target=EffectTarget(TargetType.OTHER_HAND),
                )
            ],
            description="Look at another player's hand. Choose a card and add it to your hand."
        ))

        self.register(Effect(
            effect_id="change_of_luck",
            name="Change of Luck",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(
                    action_type=ActionType.DISCARD,
                    target=EffectTarget(TargetType.OWN_HAND),
                    value=-1  # All
                ),
                EffectAction(
                    action_type=ActionType.DRAW,
                    target=EffectTarget(TargetType.CONTROLLER),
                    value=5
                ),
                EffectAction(
                    action_type=ActionType.DISCARD,
                    target=EffectTarget(TargetType.OWN_HAND),
                    value=1,
                    condition="per_card_discarded"
                )
            ],
            description="DISCARD your hand, then DRAW 5 cards. Then DISCARD 1 card for each card you discarded."
        ))

        self.register(Effect(
            effect_id="glitter_tornado",
            name="Glitter Tornado",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(
                    action_type=ActionType.SHUFFLE_INTO_DECK,
                    target=EffectTarget(TargetType.OWN_CARD_IN_STABLE),
                ),
                EffectAction(
                    action_type=ActionType.SHUFFLE_INTO_DECK,
                    target=EffectTarget(TargetType.OTHER_CARD_IN_STABLE),
                    condition="for_each_player"
                )
            ],
            description="Shuffle a card in each player's Stable into the deck."
        ))

        self.register(Effect(
            effect_id="good_deal",
            name="Good Deal",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(
                    action_type=ActionType.DRAW,
                    target=EffectTarget(TargetType.CONTROLLER),
                    value=3
                ),
                EffectAction(
                    action_type=ActionType.DISCARD,
                    target=EffectTarget(TargetType.OWN_HAND),
                    value=1
                )
            ],
            description="DRAW 3 cards and DISCARD a card."
        ))

        self.register(Effect(
            effect_id="kiss_of_life",
            name="Kiss of Life",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(
                    action_type=ActionType.BRING_TO_STABLE,
                    target=EffectTarget(TargetType.CARD_IN_DISCARD),
                    condition="unicorn_card"
                ),
                EffectAction(
                    action_type=ActionType.SACRIFICE,
                    target=EffectTarget(TargetType.OWN_UNICORN),
                )
            ],
            description="Choose a Unicorn card from the discard pile and bring it directly into your Stable. You must SACRIFICE a Unicorn card."
        ))

        self.register(Effect(
            effect_id="mystical_vortex",
            name="Mystical Vortex",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(
                    action_type=ActionType.DISCARD,
                    target=EffectTarget(TargetType.OWN_HAND),
                    value=1
                ),
                EffectAction(
                    action_type=ActionType.SACRIFICE,
                    target=EffectTarget(TargetType.ANY_CARD_IN_STABLE),
                )
            ],
            description="DISCARD a card, then SACRIFICE a card."
        ))

        self.register(Effect(
            effect_id="re_target",
            name="Re-Target",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(
                    action_type=ActionType.SWAP,
                    target=EffectTarget(TargetType.ANY_UPGRADE_OR_DOWNGRADE),
                )
            ],
            description="Move an Upgrade or Downgrade from any Stable to any other Stable."
        ))

        self.register(Effect(
            effect_id="reset_button",
            name="Reset Button",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(
                    action_type=ActionType.SACRIFICE,
                    target=EffectTarget(TargetType.ANY_CARD_IN_STABLE),
                    value=-1  # All non-baby unicorns
                )
            ],
            description="Each player must SACRIFICE all Upgrade, Downgrade, and Magic cards. Then, each player shuffles their hand into the deck and DRAWS 5 cards."
        ))

        self.register(Effect(
            effect_id="shake_up",
            name="Shake Up",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(
                    action_type=ActionType.SHUFFLE_INTO_DECK,
                    target=EffectTarget(TargetType.CARD_IN_HAND),
                    value=-1  # All hands
                ),
                EffectAction(
                    action_type=ActionType.DRAW,
                    target=EffectTarget(TargetType.ANY_PLAYER),
                    value=5
                )
            ],
            description="Shuffle this card into the deck, then each player passes their hand to the player on their left."
        ))

        self.register(Effect(
            effect_id="targeted_destruction",
            name="Targeted Destruction",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(
                    action_type=ActionType.DESTROY,
                    target=EffectTarget(TargetType.ANY_UPGRADE_OR_DOWNGRADE),
                )
            ],
            description="DESTROY an Upgrade card or SACRIFICE a Downgrade card."
        ))

        self.register(Effect(
            effect_id="two_for_one",
            name="Two-For-One",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(
                    action_type=ActionType.SACRIFICE,
                    target=EffectTarget(TargetType.OWN_CARD_IN_STABLE),
                ),
                EffectAction(
                    action_type=ActionType.DESTROY,
                    target=EffectTarget(TargetType.OTHER_CARD_IN_STABLE),
                    value=2
                )
            ],
            description="SACRIFICE a card, then DESTROY 2 cards."
        ))

        self.register(Effect(
            effect_id="unfair_bargain",
            name="Unfair Bargain",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(
                    action_type=ActionType.SWAP,
                    target=EffectTarget(TargetType.CARD_IN_HAND),
                )
            ],
            description="Trade hands with another player."
        ))

        self.register(Effect(
            effect_id="unicorn_poison",
            name="Unicorn Poison",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(
                    action_type=ActionType.DESTROY,
                    target=EffectTarget(TargetType.ANY_UNICORN),
                )
            ],
            description="DESTROY a Unicorn card."
        ))

        self.register(Effect(
            effect_id="unicorn_swap",
            name="Unicorn Swap",
            trigger=EffectTrigger.ON_PLAY,
            actions=[
                EffectAction(
                    action_type=ActionType.SWAP,
                    target=EffectTarget(TargetType.ANY_UNICORN),
                )
            ],
            description="Swap a Unicorn card in your Stable with a Unicorn card in any other Stable. This does not trigger any effects."
        ))


# Global effect registry instance
EFFECT_REGISTRY = EffectRegistry()
