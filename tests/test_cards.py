"""Unit tests for card system."""

import unittest
from cards.card import Card, CardInstance, CardType
from cards.card_database import CARD_DATABASE, BABY_UNICORNS, MAGICAL_UNICORNS


class TestCard(unittest.TestCase):
    """Tests for Card class."""

    def test_card_creation(self):
        """Test basic card creation."""
        card = Card(
            id="test_card",
            name="Test Card",
            card_type=CardType.BASIC_UNICORN
        )
        self.assertEqual(card.id, "test_card")
        self.assertEqual(card.name, "Test Card")
        self.assertEqual(card.card_type, CardType.BASIC_UNICORN)

    def test_is_unicorn(self):
        """Test unicorn type detection."""
        baby = Card(id="b", name="Baby", card_type=CardType.BABY_UNICORN)
        basic = Card(id="ba", name="Basic", card_type=CardType.BASIC_UNICORN)
        magical = Card(id="m", name="Magical", card_type=CardType.MAGICAL_UNICORN)
        upgrade = Card(id="u", name="Upgrade", card_type=CardType.UPGRADE)
        magic = Card(id="mg", name="Magic", card_type=CardType.MAGIC)

        self.assertTrue(baby.is_unicorn())
        self.assertTrue(basic.is_unicorn())
        self.assertTrue(magical.is_unicorn())
        self.assertFalse(upgrade.is_unicorn())
        self.assertFalse(magic.is_unicorn())

    def test_is_playable_to_stable(self):
        """Test stable-playable detection."""
        basic = Card(id="b", name="Basic", card_type=CardType.BASIC_UNICORN)
        upgrade = Card(id="u", name="Upgrade", card_type=CardType.UPGRADE)
        magic = Card(id="m", name="Magic", card_type=CardType.MAGIC)
        instant = Card(id="i", name="Instant", card_type=CardType.INSTANT)

        self.assertTrue(basic.is_playable_to_stable())
        self.assertTrue(upgrade.is_playable_to_stable())
        self.assertFalse(magic.is_playable_to_stable())
        self.assertFalse(instant.is_playable_to_stable())

    def test_card_equality(self):
        """Test card equality based on ID."""
        card1 = Card(id="same", name="Card 1", card_type=CardType.BASIC_UNICORN)
        card2 = Card(id="same", name="Card 2", card_type=CardType.BASIC_UNICORN)
        card3 = Card(id="different", name="Card 1", card_type=CardType.BASIC_UNICORN)

        self.assertEqual(card1, card2)
        self.assertNotEqual(card1, card3)


class TestCardInstance(unittest.TestCase):
    """Tests for CardInstance class."""

    def test_instance_creation(self):
        """Test card instance creation."""
        card = Card(id="test", name="Test", card_type=CardType.BASIC_UNICORN)
        instance = CardInstance(card=card, instance_id=1)

        self.assertEqual(instance.card, card)
        self.assertEqual(instance.instance_id, 1)
        self.assertEqual(instance.name, "Test")

    def test_instance_uniqueness(self):
        """Test that instances of same card are unique."""
        card = Card(id="test", name="Test", card_type=CardType.BASIC_UNICORN)
        instance1 = CardInstance(card=card, instance_id=1)
        instance2 = CardInstance(card=card, instance_id=2)

        self.assertNotEqual(instance1, instance2)

    def test_delegate_methods(self):
        """Test that instances delegate to underlying card."""
        card = Card(
            id="test",
            name="Test",
            card_type=CardType.MAGICAL_UNICORN,
            description="Test effect"
        )
        instance = CardInstance(card=card, instance_id=1)

        self.assertTrue(instance.is_unicorn())
        self.assertTrue(instance.is_playable_to_stable())
        self.assertFalse(instance.is_magic())
        self.assertEqual(instance.description, "Test effect")


class TestCardDatabase(unittest.TestCase):
    """Tests for CardDatabase."""

    def test_database_loads(self):
        """Test that database loads all cards."""
        all_cards = CARD_DATABASE.get_all_cards()
        self.assertGreater(len(all_cards), 50)  # Base game has ~80 unique cards

    def test_get_card(self):
        """Test getting a card by ID."""
        card = CARD_DATABASE.get_card("rhinocorn")
        self.assertEqual(card.name, "Rhinocorn")
        self.assertEqual(card.card_type, CardType.MAGICAL_UNICORN)

    def test_get_invalid_card(self):
        """Test getting an invalid card raises error."""
        with self.assertRaises(ValueError):
            CARD_DATABASE.get_card("nonexistent_card")

    def test_create_instance(self):
        """Test creating card instances."""
        instance1 = CARD_DATABASE.create_instance("rhinocorn")
        instance2 = CARD_DATABASE.create_instance("rhinocorn")

        self.assertEqual(instance1.name, "Rhinocorn")
        self.assertNotEqual(instance1.instance_id, instance2.instance_id)

    def test_create_deck(self):
        """Test creating a full deck."""
        deck = CARD_DATABASE.create_deck()

        # Deck should have cards but no baby unicorns
        self.assertGreater(len(deck), 80)
        for card in deck:
            self.assertNotEqual(card.card_type, CardType.BABY_UNICORN)

    def test_create_nursery(self):
        """Test creating the nursery."""
        nursery = CARD_DATABASE.create_nursery()

        self.assertEqual(len(nursery), len(BABY_UNICORNS))
        for card in nursery:
            self.assertEqual(card.card_type, CardType.BABY_UNICORN)

    def test_get_cards_by_type(self):
        """Test filtering cards by type."""
        magical = CARD_DATABASE.get_cards_by_type(CardType.MAGICAL_UNICORN)
        instants = CARD_DATABASE.get_cards_by_type(CardType.INSTANT)

        self.assertEqual(len(magical), len(MAGICAL_UNICORNS))
        self.assertEqual(len(instants), 2)  # Neigh and Super Neigh


if __name__ == "__main__":
    unittest.main()
