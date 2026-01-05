"""Save and load game state functionality."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import asdict

from game.game_state import GameState, PlayerState, GamePhase
from cards.card_database import CARD_DATABASE


class SaveLoadManager:
    """Manages saving and loading game states."""

    def __init__(self, saves_dir: Optional[str] = None):
        self.saves_dir = saves_dir or str(Path.home() / ".unstable_unicorns" / "saves")
        os.makedirs(self.saves_dir, exist_ok=True)

    def save_game(self, state: GameState, name: Optional[str] = None,
                  player_types: Optional[List[str]] = None) -> str:
        """
        Save the current game state to a file.

        Returns the save file path.
        """
        if name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name = f"save_{timestamp}"

        # Serialize the game state
        save_data = self._serialize_state(state)
        save_data["save_name"] = name
        save_data["timestamp"] = datetime.now().isoformat()
        save_data["player_types"] = player_types or ["unknown"] * state.num_players

        # Write to file
        filepath = os.path.join(self.saves_dir, f"{name}.json")
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)

        return filepath

    def load_game(self, name_or_path: str) -> Tuple[GameState, Dict]:
        """
        Load a game state from a file.

        Returns (GameState, metadata_dict).
        """
        # Handle both filename and full path
        if os.path.exists(name_or_path):
            filepath = name_or_path
        else:
            filepath = os.path.join(self.saves_dir, f"{name_or_path}.json")

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Save file not found: {filepath}")

        with open(filepath, 'r') as f:
            save_data = json.load(f)

        state = self._deserialize_state(save_data)
        metadata = {
            "save_name": save_data.get("save_name", "unknown"),
            "timestamp": save_data.get("timestamp", "unknown"),
            "player_types": save_data.get("player_types", []),
        }

        return state, metadata

    def list_saves(self) -> List[Dict]:
        """List all available save files with metadata."""
        saves = []

        for filename in os.listdir(self.saves_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.saves_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)

                    saves.append({
                        "filename": filename,
                        "name": data.get("save_name", filename[:-5]),
                        "timestamp": data.get("timestamp", "unknown"),
                        "num_players": data.get("num_players", 0),
                        "current_player": data.get("current_player_idx", 0),
                        "phase": data.get("phase", "unknown"),
                        "player_names": [p.get("name", "Unknown") for p in data.get("players", [])],
                    })
                except (json.JSONDecodeError, KeyError):
                    continue

        # Sort by timestamp, newest first
        saves.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return saves

    def delete_save(self, name_or_path: str) -> bool:
        """Delete a save file."""
        if os.path.exists(name_or_path):
            filepath = name_or_path
        else:
            filepath = os.path.join(self.saves_dir, f"{name_or_path}.json")

        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    def _serialize_state(self, state: GameState) -> Dict:
        """Serialize GameState to a dictionary."""
        return {
            "num_players": state.num_players,
            "current_player_idx": state.current_player_idx,
            "phase": state.phase.name,
            "turn_number": state.turn_number,
            "actions_remaining": state.actions_remaining,
            "unicorns_to_win": state.unicorns_to_win,
            "winner": state.winner,
            "neigh_chain_active": state.neigh_chain_active,
            "card_being_played": self._serialize_card(state.card_being_played),
            "players": [self._serialize_player(p) for p in state.players],
            "draw_pile": [self._serialize_card(c) for c in state.draw_pile],
            "discard_pile": [self._serialize_card(c) for c in state.discard_pile],
            "nursery": [self._serialize_card(c) for c in state.nursery],
        }

    def _deserialize_state(self, data: Dict) -> GameState:
        """Deserialize a dictionary to GameState."""
        players = [self._deserialize_player(p) for p in data["players"]]

        state = GameState(
            players=players,
            num_players=data["num_players"]
        )

        state.current_player_idx = data["current_player_idx"]
        state.phase = GamePhase[data["phase"]]
        state.turn_number = data.get("turn_number", 1)
        state.actions_remaining = data.get("actions_remaining", 1)
        state.winner = data.get("winner")
        state.neigh_chain_active = data.get("neigh_chain_active", False)
        state.card_being_played = self._deserialize_card(data.get("card_being_played"))
        state.draw_pile = [self._deserialize_card(c) for c in data.get("draw_pile", [])]
        state.discard_pile = [self._deserialize_card(c) for c in data.get("discard_pile", [])]
        state.nursery = [self._deserialize_card(c) for c in data.get("nursery", [])]

        return state

    def _serialize_player(self, player: PlayerState) -> Dict:
        """Serialize PlayerState to a dictionary."""
        return {
            "player_idx": player.player_idx,
            "name": player.name,
            "hand": [self._serialize_card(c) for c in player.hand],
            "stable": [self._serialize_card(c) for c in player.stable],
            "upgrades": [self._serialize_card(c) for c in player.upgrades],
            "downgrades": [self._serialize_card(c) for c in player.downgrades],
            # Player flags
            "cards_cannot_be_neighd": player.cards_cannot_be_neighd,
            "unicorns_cannot_be_destroyed": player.unicorns_cannot_be_destroyed,
            "cannot_play_instant": getattr(player, 'cannot_play_instant', False),
            "cannot_play_upgrades": player.cannot_play_upgrades,
            "cannot_play_downgrades": getattr(player, 'cannot_play_downgrades', False),
            "unicorns_are_pandas": player.unicorns_are_pandas,
            "hand_limit_modifier": getattr(player, 'hand_limit_modifier', 0),
            "extra_cards_per_turn": getattr(player, 'extra_cards_per_turn', 0),
        }

    def _deserialize_player(self, data: Dict) -> PlayerState:
        """Deserialize a dictionary to PlayerState."""
        player = PlayerState(
            player_idx=data["player_idx"],
            name=data["name"]
        )

        player.hand = [self._deserialize_card(c) for c in data.get("hand", [])]
        player.stable = [self._deserialize_card(c) for c in data.get("stable", [])]
        player.upgrades = [self._deserialize_card(c) for c in data.get("upgrades", [])]
        player.downgrades = [self._deserialize_card(c) for c in data.get("downgrades", [])]

        # Restore player flags
        player.cards_cannot_be_neighd = data.get("cards_cannot_be_neighd", False)
        player.unicorns_cannot_be_destroyed = data.get("unicorns_cannot_be_destroyed", False)
        player.cannot_play_upgrades = data.get("cannot_play_upgrades", False)
        player.unicorns_are_pandas = data.get("unicorns_are_pandas", False)

        return player

    def _serialize_card(self, card) -> Optional[Dict]:
        """Serialize a card instance to a dictionary."""
        if card is None:
            return None

        return {
            "card_id": card.card.id,
            "instance_id": card.instance_id,
        }

    def _deserialize_card(self, data: Optional[Dict]):
        """Deserialize a dictionary to a card instance."""
        if data is None:
            return None

        card_id = data["card_id"]
        instance_id = data["instance_id"]

        # Recreate the card instance with the same instance_id
        card_instance = CARD_DATABASE.create_instance(card_id)
        card_instance.instance_id = instance_id

        return card_instance

    def format_save_list(self) -> str:
        """Format a list of saves for display."""
        saves = self.list_saves()

        if not saves:
            return "No saved games found."

        lines = [
            "=" * 60,
            "                    SAVED GAMES",
            "=" * 60,
            "",
        ]

        for i, save in enumerate(saves, 1):
            timestamp = save["timestamp"]
            if timestamp != "unknown":
                try:
                    dt = datetime.fromisoformat(timestamp)
                    timestamp = dt.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    pass

            players = ", ".join(save["player_names"][:3])
            if len(save["player_names"]) > 3:
                players += f" +{len(save['player_names']) - 3} more"

            lines.extend([
                f"{i}. {save['name']}",
                f"   Date: {timestamp}",
                f"   Players: {players}",
                f"   Phase: {save['phase']}, Turn of: {save['player_names'][save['current_player']] if save['player_names'] else 'Unknown'}",
                "",
            ])

        lines.append("=" * 60)
        return "\n".join(lines)


# Global save/load manager instance
SAVE_MANAGER = SaveLoadManager()


def quick_save(state: GameState, player_types: Optional[List[str]] = None) -> str:
    """Quick save the current game state."""
    return SAVE_MANAGER.save_game(state, player_types=player_types)


def quick_load(name: str) -> Tuple[GameState, Dict]:
    """Quick load a saved game."""
    return SAVE_MANAGER.load_game(name)


def autosave(state: GameState, player_types: Optional[List[str]] = None) -> str:
    """Autosave the current game state (overwrites previous autosave)."""
    return SAVE_MANAGER.save_game(state, name="autosave", player_types=player_types)
