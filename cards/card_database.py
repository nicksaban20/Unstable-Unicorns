"""Card database for Unstable Unicorns Base Game 2nd Edition.

Contains all 127 cards from the base game.
"""

from typing import Dict, List
from cards.card import Card, CardType, CardInstance


# =============================================================================
# BABY UNICORNS (13 cards, 1 copy each)
# =============================================================================

BABY_UNICORNS: List[Card] = [
    Card(id="baby_red", name="Baby Unicorn (Red)", card_type=CardType.BABY_UNICORN),
    Card(id="baby_pink", name="Baby Unicorn (Pink)", card_type=CardType.BABY_UNICORN),
    Card(id="baby_orange", name="Baby Unicorn (Orange)", card_type=CardType.BABY_UNICORN),
    Card(id="baby_yellow", name="Baby Unicorn (Yellow)", card_type=CardType.BABY_UNICORN),
    Card(id="baby_green", name="Baby Unicorn (Green)", card_type=CardType.BABY_UNICORN),
    Card(id="baby_blue", name="Baby Unicorn (Blue)", card_type=CardType.BABY_UNICORN),
    Card(id="baby_purple", name="Baby Unicorn (Purple)", card_type=CardType.BABY_UNICORN),
    Card(id="baby_black", name="Baby Unicorn (Black)", card_type=CardType.BABY_UNICORN),
    Card(id="baby_white", name="Baby Unicorn (White)", card_type=CardType.BABY_UNICORN),
    Card(id="baby_brown", name="Baby Unicorn (Brown)", card_type=CardType.BABY_UNICORN),
    Card(id="baby_rainbow", name="Baby Unicorn (Rainbow)", card_type=CardType.BABY_UNICORN),
    Card(id="baby_death", name="Baby Unicorn (Death)", card_type=CardType.BABY_UNICORN),
    Card(id="baby_narwhal", name="Baby Narwhal", card_type=CardType.BABY_UNICORN),
]


# =============================================================================
# BASIC UNICORNS (8 unique, 22 total cards)
# =============================================================================

BASIC_UNICORNS: List[Card] = [
    # Red (3 copies)
    Card(id="basic_red", name="Basic Unicorn (Red)", card_type=CardType.BASIC_UNICORN),
    # Orange (3 copies)
    Card(id="basic_orange", name="Basic Unicorn (Orange)", card_type=CardType.BASIC_UNICORN),
    # Yellow (3 copies)
    Card(id="basic_yellow", name="Basic Unicorn (Yellow)", card_type=CardType.BASIC_UNICORN),
    # Green (3 copies)
    Card(id="basic_green", name="Basic Unicorn (Green)", card_type=CardType.BASIC_UNICORN),
    # Blue (3 copies)
    Card(id="basic_blue", name="Basic Unicorn (Blue)", card_type=CardType.BASIC_UNICORN),
    # Indigo (3 copies)
    Card(id="basic_indigo", name="Basic Unicorn (Indigo)", card_type=CardType.BASIC_UNICORN),
    # Purple (3 copies)
    Card(id="basic_purple", name="Basic Unicorn (Purple)", card_type=CardType.BASIC_UNICORN),
    # Narwhal (1 copy)
    Card(id="basic_narwhal", name="Narwhal", card_type=CardType.BASIC_UNICORN),
]

# Card copies for deck building
BASIC_UNICORN_COPIES = {
    "basic_red": 3,
    "basic_orange": 3,
    "basic_yellow": 3,
    "basic_green": 3,
    "basic_blue": 3,
    "basic_indigo": 3,
    "basic_purple": 3,
    "basic_narwhal": 1,
}


# =============================================================================
# MAGICAL UNICORNS (33 cards, 1 copy each)
# =============================================================================

MAGICAL_UNICORNS: List[Card] = [
    Card(
        id="alluring_narwhal",
        name="Alluring Narwhal",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, you may STEAL an Upgrade card.",
        effect_id="alluring_narwhal"
    ),
    Card(
        id="americorn",
        name="Americorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="If this card is in your Stable at the beginning of your turn, you may pull a card at random from another player's hand. If you do, skip your Draw phase.",
        effect_id="americorn"
    ),
    Card(
        id="annoying_flying_unicorn",
        name="Annoying Flying Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, you may choose any player. That player must DISCARD a card.",
        effect_id="annoying_flying_unicorn"
    ),
    Card(
        id="black_knight_unicorn",
        name="Black Knight Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="If 1 of your Unicorns would be destroyed, you may SACRIFICE this card instead.",
        effect_id="black_knight_unicorn"
    ),
    Card(
        id="chainsaw_unicorn",
        name="Chainsaw Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, you may DESTROY an Upgrade card or SACRIFICE a Downgrade card.",
        effect_id="chainsaw_unicorn"
    ),
    Card(
        id="classy_narwhal",
        name="Classy Narwhal",
        card_type=CardType.MAGICAL_UNICORN,
        description="Your hand must be visible to all players at all times.",
        effect_id="classy_narwhal"
    ),
    Card(
        id="dark_angel_unicorn",
        name="Dark Angel Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, you may choose a Unicorn card from the discard pile and add it to your hand.",
        effect_id="dark_angel_unicorn"
    ),
    Card(
        id="extremely_destructive_unicorn",
        name="Extremely Destructive Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, each player must DESTROY an Upgrade card in their Stable.",
        effect_id="extremely_destructive_unicorn"
    ),
    Card(
        id="ginormous_unicorn",
        name="Ginormous Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="This card counts as 2 Unicorns.",
        effect_id="ginormous_unicorn"
    ),
    Card(
        id="greedy_flying_unicorn",
        name="Greedy Flying Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, DRAW a card.",
        effect_id="greedy_flying_unicorn"
    ),
    Card(
        id="llamacorn",
        name="Llamacorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="If this card is in your Stable at the beginning of your turn, you may DISCARD a card. If you do, DESTROY a card in another player's Stable.",
        effect_id="llamacorn"
    ),
    Card(
        id="magical_flying_unicorn",
        name="Magical Flying Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, you may search the deck for a Magic card and add it to your hand. Shuffle the deck.",
        effect_id="magical_flying_unicorn"
    ),
    Card(
        id="magical_kittencorn",
        name="Magical Kittencorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="This card cannot be destroyed.",
        effect_id="magical_kittencorn"
    ),
    Card(
        id="majestic_flying_unicorn",
        name="Majestic Flying Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, you may search the deck for a Unicorn card and add it to your hand. Shuffle the deck.",
        effect_id="majestic_flying_unicorn"
    ),
    Card(
        id="mermaid_unicorn",
        name="Mermaid Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, return a card in your Stable to your hand. If this card is sacrificed or destroyed, return it to your hand instead of the discard pile.",
        effect_id="mermaid_unicorn"
    ),
    Card(
        id="mother_goose_unicorn",
        name="Mother Goose Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="If this card is in your Stable at the beginning of your turn, and you have no Baby Unicorns in your Stable, bring a Baby Unicorn from the Nursery directly to your Stable.",
        effect_id="mother_goose_unicorn"
    ),
    Card(
        id="narwhal_torpedo",
        name="Narwhal Torpedo",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, you may SACRIFICE this card. If you do, DESTROY a Unicorn card.",
        effect_id="narwhal_torpedo"
    ),
    Card(
        id="necromancer_unicorn",
        name="Necromancer Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, you may SACRIFICE 2 Unicorn cards. If you do, choose a Unicorn card from the discard pile and bring it directly into your Stable.",
        effect_id="necromancer_unicorn"
    ),
    Card(
        id="queen_bee_unicorn",
        name="Queen Bee Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="Basic Unicorn cards cannot enter any other player's Stable.",
        effect_id="queen_bee_unicorn"
    ),
    Card(
        id="rainbow_unicorn",
        name="Rainbow Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, bring a Baby Unicorn from the Nursery directly to your Stable.",
        effect_id="rainbow_unicorn"
    ),
    Card(
        id="rhinocorn",
        name="Rhinocorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="If this card is in your Stable at the beginning of your turn, you may DESTROY a Unicorn card. If you do, immediately end your turn.",
        effect_id="rhinocorn"
    ),
    Card(
        id="seductive_unicorn",
        name="Seductive Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, SACRIFICE a Unicorn card, then STEAL a Unicorn card.",
        effect_id="seductive_unicorn"
    ),
    Card(
        id="shabby_the_narwhal",
        name="Shabby the Narwhal",
        card_type=CardType.MAGICAL_UNICORN,
        description="This card cannot be affected by Downgrade cards.",
        effect_id="shabby_the_narwhal"
    ),
    Card(
        id="shark_with_a_horn",
        name="Shark With a Horn",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, you may DESTROY a Unicorn card. This power only works if you have a Downgrade card in your Stable.",
        effect_id="shark_with_a_horn"
    ),
    Card(
        id="stabby_the_unicorn",
        name="Stabby the Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, you must SACRIFICE a card, then DESTROY a Unicorn card.",
        effect_id="stabby_the_unicorn"
    ),
    Card(
        id="swift_flying_unicorn",
        name="Swift Flying Unicorn",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, you may choose a card in any Stable and return it to that player's hand.",
        effect_id="swift_flying_unicorn"
    ),
    Card(
        id="the_great_narwhal",
        name="The Great Narwhal",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, you may search the deck for a card with 'Narwhal' in its name and add it to your hand. Shuffle the deck.",
        effect_id="the_great_narwhal"
    ),
    Card(
        id="unicorn_on_the_cob",
        name="Unicorn on the Cob",
        card_type=CardType.MAGICAL_UNICORN,
        description="When this card enters your Stable, DRAW 2 cards and DISCARD a card.",
        effect_id="unicorn_on_the_cob"
    ),
    Card(
        id="unicorn_oracle",
        name="Unicorn Oracle",
        card_type=CardType.MAGICAL_UNICORN,
        description="If this card is in your Stable at the beginning of your turn, you may look at the top 3 cards of the deck. Put those cards back on the top or bottom of the deck in any order.",
        effect_id="unicorn_oracle"
    ),
    Card(
        id="unicorn_phoenix",
        name="Unicorn Phoenix",
        card_type=CardType.MAGICAL_UNICORN,
        description="If this card would be sacrificed or destroyed, you may DISCARD a card instead. If you do, this card returns to your Stable.",
        effect_id="unicorn_phoenix"
    ),
]


# =============================================================================
# MAGIC CARDS (16 unique types, varying copies)
# =============================================================================

MAGIC_CARDS: List[Card] = [
    Card(
        id="back_kick",
        name="Back Kick",
        card_type=CardType.MAGIC,
        description="Return a card in another player's Stable to their hand.",
        effect_id="back_kick"
    ),
    Card(
        id="blatant_thievery",
        name="Blatant Thievery",
        card_type=CardType.MAGIC,
        description="Look at another player's hand. Choose a card and add it to your hand.",
        effect_id="blatant_thievery"
    ),
    Card(
        id="change_of_luck",
        name="Change of Luck",
        card_type=CardType.MAGIC,
        description="DISCARD your hand, then DRAW 5 cards. Then DISCARD 1 card for each card you discarded.",
        effect_id="change_of_luck"
    ),
    Card(
        id="glitter_tornado",
        name="Glitter Tornado",
        card_type=CardType.MAGIC,
        description="Shuffle a card in each player's Stable into the deck.",
        effect_id="glitter_tornado"
    ),
    Card(
        id="good_deal",
        name="Good Deal",
        card_type=CardType.MAGIC,
        description="DRAW 3 cards and DISCARD a card.",
        effect_id="good_deal"
    ),
    Card(
        id="kiss_of_life",
        name="Kiss of Life",
        card_type=CardType.MAGIC,
        description="Choose a Unicorn card from the discard pile and bring it directly into your Stable. You must SACRIFICE a Unicorn card.",
        effect_id="kiss_of_life"
    ),
    Card(
        id="mystical_vortex",
        name="Mystical Vortex",
        card_type=CardType.MAGIC,
        description="DISCARD a card, then SACRIFICE a card.",
        effect_id="mystical_vortex"
    ),
    Card(
        id="re_target",
        name="Re-Target",
        card_type=CardType.MAGIC,
        description="Move an Upgrade or Downgrade card from any Stable to any other Stable.",
        effect_id="re_target"
    ),
    Card(
        id="reset_button",
        name="Reset Button",
        card_type=CardType.MAGIC,
        description="Each player must SACRIFICE all Upgrade, Downgrade, and Magic cards. Then, each player shuffles their hand into the deck and DRAWS 5 cards.",
        effect_id="reset_button"
    ),
    Card(
        id="shake_up",
        name="Shake Up",
        card_type=CardType.MAGIC,
        description="Shuffle this card into the deck, then each player passes their hand to the player on their left.",
        effect_id="shake_up"
    ),
    Card(
        id="targeted_destruction",
        name="Targeted Destruction",
        card_type=CardType.MAGIC,
        description="DESTROY an Upgrade card or SACRIFICE a Downgrade card.",
        effect_id="targeted_destruction"
    ),
    Card(
        id="two_for_one",
        name="Two-For-One",
        card_type=CardType.MAGIC,
        description="SACRIFICE a card, then DESTROY 2 cards.",
        effect_id="two_for_one"
    ),
    Card(
        id="unfair_bargain",
        name="Unfair Bargain",
        card_type=CardType.MAGIC,
        description="Trade hands with another player.",
        effect_id="unfair_bargain"
    ),
    Card(
        id="unicorn_poison",
        name="Unicorn Poison",
        card_type=CardType.MAGIC,
        description="DESTROY a Unicorn card.",
        effect_id="unicorn_poison"
    ),
    Card(
        id="unicorn_swap",
        name="Unicorn Swap",
        card_type=CardType.MAGIC,
        description="Swap a Unicorn card in your Stable with a Unicorn card in any other Stable. This does not trigger any effects.",
        effect_id="unicorn_swap"
    ),
]

# Card copies for magic cards
MAGIC_CARD_COPIES = {
    "back_kick": 3,
    "blatant_thievery": 1,
    "change_of_luck": 2,
    "glitter_tornado": 2,
    "good_deal": 1,
    "kiss_of_life": 1,
    "mystical_vortex": 1,
    "re_target": 2,
    "reset_button": 1,
    "shake_up": 1,
    "targeted_destruction": 1,
    "two_for_one": 2,
    "unfair_bargain": 2,
    "unicorn_poison": 3,
    "unicorn_swap": 2,
}


# =============================================================================
# UPGRADE CARDS (8 unique types, varying copies)
# =============================================================================

UPGRADE_CARDS: List[Card] = [
    Card(
        id="caffeine_overload",
        name="Caffeine Overload",
        card_type=CardType.UPGRADE,
        description="If this card is in your Stable at the beginning of your turn, you may play 2 cards during your Action phase.",
        effect_id="caffeine_overload"
    ),
    Card(
        id="claw_machine",
        name="Claw Machine",
        card_type=CardType.UPGRADE,
        description="If this card is in your Stable at the beginning of your turn, you may take a card from the discard pile and add it to your hand.",
        effect_id="claw_machine"
    ),
    Card(
        id="double_dutch",
        name="Double Dutch",
        card_type=CardType.UPGRADE,
        description="If this card is in your Stable at the beginning of your turn, you may DRAW an extra card during your Draw phase.",
        effect_id="double_dutch"
    ),
    Card(
        id="glitter_bomb",
        name="Glitter Bomb",
        card_type=CardType.UPGRADE,
        description="If this card is in your Stable at the end of your turn, you may SACRIFICE a card. If you do, DESTROY a card.",
        effect_id="glitter_bomb"
    ),
    Card(
        id="rainbow_aura",
        name="Rainbow Aura",
        card_type=CardType.UPGRADE,
        description="Your Unicorn cards cannot be destroyed.",
        effect_id="rainbow_aura"
    ),
    Card(
        id="rainbow_lasso",
        name="Rainbow Lasso",
        card_type=CardType.UPGRADE,
        description="If this card is in your Stable at the beginning of your turn, STEAL a Unicorn card, then SACRIFICE this card.",
        effect_id="rainbow_lasso"
    ),
    Card(
        id="stable_artillery",
        name="Stable Artillery",
        card_type=CardType.UPGRADE,
        description="You may SACRIFICE a Unicorn card. If you do, DESTROY a Unicorn card.",
        effect_id="stable_artillery"
    ),
    Card(
        id="yay",
        name="Yay",
        card_type=CardType.UPGRADE,
        description="Cards you play cannot be Neigh'd.",
        effect_id="yay"
    ),
]

# Card copies for upgrade cards
UPGRADE_CARD_COPIES = {
    "caffeine_overload": 1,
    "claw_machine": 3,
    "double_dutch": 1,
    "glitter_bomb": 2,
    "rainbow_aura": 1,
    "rainbow_lasso": 1,
    "stable_artillery": 3,
    "yay": 2,
}


# =============================================================================
# DOWNGRADE CARDS (8 unique types, 1 copy each)
# =============================================================================

DOWNGRADE_CARDS: List[Card] = [
    Card(
        id="barbed_wire",
        name="Barbed Wire",
        card_type=CardType.DOWNGRADE,
        description="Each time a Unicorn card enters or leaves your Stable, DESTROY a Unicorn card.",
        effect_id="barbed_wire"
    ),
    Card(
        id="blinding_light",
        name="Blinding Light",
        card_type=CardType.DOWNGRADE,
        description="All of your Unicorn cards are considered Basic Unicorns with no effects.",
        effect_id="blinding_light"
    ),
    Card(
        id="broken_stable",
        name="Broken Stable",
        card_type=CardType.DOWNGRADE,
        description="You cannot play Upgrade cards.",
        effect_id="broken_stable"
    ),
    Card(
        id="nanny_cam",
        name="Nanny Cam",
        card_type=CardType.DOWNGRADE,
        description="Your hand must be visible to all players at all times.",
        effect_id="nanny_cam"
    ),
    Card(
        id="pandamonium",
        name="Pandamonium",
        card_type=CardType.DOWNGRADE,
        description="All of your Unicorns are considered Pandas. Cards that affect Unicorn cards do not affect your Pandas.",
        effect_id="pandamonium"
    ),
    Card(
        id="sadistic_ritual",
        name="Sadistic Ritual",
        card_type=CardType.DOWNGRADE,
        description="At the beginning of your turn, SACRIFICE a Unicorn card, then DRAW a card.",
        effect_id="sadistic_ritual"
    ),
    Card(
        id="slowdown",
        name="Slowdown",
        card_type=CardType.DOWNGRADE,
        description="You cannot play Instant cards.",
        effect_id="slowdown"
    ),
    Card(
        id="tiny_stable",
        name="Tiny Stable",
        card_type=CardType.DOWNGRADE,
        description="If at any time you have more than 5 Unicorns in your Stable, SACRIFICE a Unicorn card.",
        effect_id="tiny_stable"
    ),
]


# =============================================================================
# INSTANT CARDS (2 unique types, varying copies)
# =============================================================================

INSTANT_CARDS: List[Card] = [
    Card(
        id="neigh",
        name="Neigh",
        card_type=CardType.INSTANT,
        description="Play this card when another player tries to play a card. Stop their card from being played and send it to the discard pile.",
        effect_id="neigh"
    ),
    Card(
        id="super_neigh",
        name="Super Neigh",
        card_type=CardType.INSTANT,
        description="Play this card when another player tries to play a card. Stop their card from being played and send it to the discard pile. This card cannot be Neigh'd.",
        effect_id="super_neigh"
    ),
]

# Card copies for instant cards
INSTANT_CARD_COPIES = {
    "neigh": 14,
    "super_neigh": 1,
}


# =============================================================================
# CARD DATABASE CLASS
# =============================================================================

class CardDatabase:
    """Database of all cards in the game."""

    def __init__(self):
        self._cards: Dict[str, Card] = {}
        self._instance_counter = 0
        self._load_cards()

    def _load_cards(self) -> None:
        """Load all cards into the database."""
        for card in BABY_UNICORNS:
            self._cards[card.id] = card
        for card in BASIC_UNICORNS:
            self._cards[card.id] = card
        for card in MAGICAL_UNICORNS:
            self._cards[card.id] = card
        for card in MAGIC_CARDS:
            self._cards[card.id] = card
        for card in UPGRADE_CARDS:
            self._cards[card.id] = card
        for card in DOWNGRADE_CARDS:
            self._cards[card.id] = card
        for card in INSTANT_CARDS:
            self._cards[card.id] = card

    def get_card(self, card_id: str) -> Card:
        """Get a card by ID."""
        if card_id not in self._cards:
            raise ValueError(f"Unknown card ID: {card_id}")
        return self._cards[card_id]

    def create_instance(self, card_id: str) -> CardInstance:
        """Create a new instance of a card."""
        card = self.get_card(card_id)
        self._instance_counter += 1
        return CardInstance(card=card, instance_id=self._instance_counter)

    def create_deck(self) -> List[CardInstance]:
        """Create a full deck of cards (excluding baby unicorns)."""
        deck: List[CardInstance] = []

        # Add basic unicorns
        for card_id, copies in BASIC_UNICORN_COPIES.items():
            for _ in range(copies):
                deck.append(self.create_instance(card_id))

        # Add magical unicorns (1 copy each)
        for card in MAGICAL_UNICORNS:
            deck.append(self.create_instance(card.id))

        # Add magic cards
        for card_id, copies in MAGIC_CARD_COPIES.items():
            for _ in range(copies):
                deck.append(self.create_instance(card_id))

        # Add upgrade cards
        for card_id, copies in UPGRADE_CARD_COPIES.items():
            for _ in range(copies):
                deck.append(self.create_instance(card_id))

        # Add downgrade cards (1 copy each)
        for card in DOWNGRADE_CARDS:
            deck.append(self.create_instance(card.id))

        # Add instant cards
        for card_id, copies in INSTANT_CARD_COPIES.items():
            for _ in range(copies):
                deck.append(self.create_instance(card_id))

        return deck

    def create_nursery(self) -> List[CardInstance]:
        """Create the nursery with all baby unicorns."""
        nursery: List[CardInstance] = []
        for card in BABY_UNICORNS:
            nursery.append(self.create_instance(card.id))
        return nursery

    def get_all_cards(self) -> List[Card]:
        """Get all unique cards."""
        return list(self._cards.values())

    def get_cards_by_type(self, card_type: CardType) -> List[Card]:
        """Get all cards of a specific type."""
        return [c for c in self._cards.values() if c.card_type == card_type]


# Global card database instance
CARD_DATABASE = CardDatabase()
