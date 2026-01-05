"""Card classes and types for Unstable Unicorns."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List


class CardType(Enum):
    """Types of cards in Unstable Unicorns."""
    BABY_UNICORN = auto()
    BASIC_UNICORN = auto()
    MAGICAL_UNICORN = auto()
    UPGRADE = auto()
    DOWNGRADE = auto()
    MAGIC = auto()
    INSTANT = auto()


class EffectTrigger(Enum):
    """When a card's effect triggers."""
    NONE = auto()              # No effect (basic cards)
    ON_ENTER = auto()          # When card enters stable
    ON_LEAVE = auto()          # When card leaves stable
    BEGINNING_OF_TURN = auto() # At beginning of owner's turn
    END_OF_TURN = auto()       # At end of owner's turn
    CONTINUOUS = auto()        # Always active while in stable
    ON_PLAY = auto()           # When card is played (Magic cards)
    INSTANT = auto()           # Can be played any time (Neigh cards)


class TargetType(Enum):
    """Types of targets for card effects."""
    NONE = auto()
    SELF = auto()
    ANY_PLAYER = auto()
    OTHER_PLAYER = auto()
    ANY_UNICORN = auto()
    OWN_UNICORN = auto()
    OTHER_UNICORN = auto()
    ANY_CARD_IN_STABLE = auto()
    ANY_UPGRADE = auto()
    ANY_DOWNGRADE = auto()
    ANY_UPGRADE_OR_DOWNGRADE = auto()
    CARD_IN_HAND = auto()
    CARD_IN_DISCARD = auto()
    CARD_IN_DECK = auto()


@dataclass
class Card:
    """Represents a card in Unstable Unicorns.

    Cards are immutable data objects. Effects are handled
    by the effect system using the effect_id.
    """
    id: str                          # Unique identifier
    name: str                        # Display name
    card_type: CardType              # Type of card
    description: str = ""            # Card effect text
    effect_id: Optional[str] = None  # Links to effect in effect registry

    def is_unicorn(self) -> bool:
        """Check if this card is a unicorn (counts toward win condition)."""
        return self.card_type in (
            CardType.BABY_UNICORN,
            CardType.BASIC_UNICORN,
            CardType.MAGICAL_UNICORN
        )

    def is_playable_to_stable(self) -> bool:
        """Check if this card can be played to a stable."""
        return self.card_type in (
            CardType.BASIC_UNICORN,
            CardType.MAGICAL_UNICORN,
            CardType.UPGRADE,
            CardType.DOWNGRADE
        )

    def is_magic(self) -> bool:
        """Check if this is a Magic card (one-time effect)."""
        return self.card_type == CardType.MAGIC

    def is_instant(self) -> bool:
        """Check if this is an Instant card (can be played any time)."""
        return self.card_type == CardType.INSTANT

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Card):
            return False
        return self.id == other.id


@dataclass
class CardInstance:
    """A specific instance of a card in the game.

    This represents an actual card in play, hand, or deck,
    allowing the same card definition to appear multiple times.
    """
    card: Card
    instance_id: int  # Unique instance identifier

    def __hash__(self) -> int:
        return hash((self.card.id, self.instance_id))

    def __eq__(self, other) -> bool:
        if not isinstance(other, CardInstance):
            return False
        return self.card.id == other.card.id and self.instance_id == other.instance_id

    # Delegate common properties to the underlying card
    @property
    def name(self) -> str:
        return self.card.name

    @property
    def card_type(self) -> CardType:
        return self.card.card_type

    @property
    def description(self) -> str:
        return self.card.description

    @property
    def effect_id(self) -> Optional[str]:
        return self.card.effect_id

    def is_unicorn(self) -> bool:
        return self.card.is_unicorn()

    def is_playable_to_stable(self) -> bool:
        return self.card.is_playable_to_stable()

    def is_magic(self) -> bool:
        return self.card.is_magic()

    def is_instant(self) -> bool:
        return self.card.is_instant()
