"""Game statistics tracking for Unstable Unicorns."""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


@dataclass
class GameStats:
    """Statistics for a single game."""
    game_id: str
    timestamp: str
    duration_seconds: float
    num_players: int
    player_names: List[str]
    player_types: List[str]  # 'human', 'random', 'mcts', etc.
    winner_idx: int
    winner_name: str
    total_turns: int
    final_unicorn_counts: List[int]
    cards_played: Dict[str, int]  # player_name -> cards played count
    cards_drawn: Dict[str, int]
    neighs_played: Dict[str, int]
    unicorns_destroyed: Dict[str, int]
    unicorns_sacrificed: Dict[str, int]
    unicorns_stolen: Dict[str, int]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'GameStats':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class PlayerProfile:
    """Statistics for a player across multiple games."""
    name: str
    player_type: str
    games_played: int = 0
    games_won: int = 0
    total_unicorns: int = 0
    total_cards_played: int = 0
    total_cards_drawn: int = 0
    total_neighs: int = 0
    total_unicorns_destroyed: int = 0
    total_unicorns_stolen: int = 0
    elo_rating: float = 1000.0
    highest_elo: float = 1000.0
    win_streak: int = 0
    best_win_streak: int = 0
    avg_game_turns: float = 0.0

    @property
    def win_rate(self) -> float:
        """Calculate win rate."""
        if self.games_played == 0:
            return 0.0
        return self.games_won / self.games_played

    @property
    def avg_unicorns_per_game(self) -> float:
        """Calculate average unicorns per game."""
        if self.games_played == 0:
            return 0.0
        return self.total_unicorns / self.games_played

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'PlayerProfile':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class StatisticsTracker:
    """Tracks game statistics across sessions."""
    stats_dir: str = field(default_factory=lambda: str(Path.home() / ".unstable_unicorns"))
    games: List[GameStats] = field(default_factory=list)
    player_profiles: Dict[str, PlayerProfile] = field(default_factory=dict)
    _current_game: Optional[Dict] = field(default=None, repr=False)

    def __post_init__(self):
        """Initialize and load existing stats."""
        os.makedirs(self.stats_dir, exist_ok=True)
        self.load()

    def start_game(self, player_names: List[str], player_types: List[str]):
        """Start tracking a new game."""
        import uuid
        self._current_game = {
            "game_id": str(uuid.uuid4())[:8],
            "start_time": datetime.now(),
            "player_names": player_names,
            "player_types": player_types,
            "num_players": len(player_names),
            "turns": 0,
            "cards_played": {name: 0 for name in player_names},
            "cards_drawn": {name: 0 for name in player_names},
            "neighs_played": {name: 0 for name in player_names},
            "unicorns_destroyed": {name: 0 for name in player_names},
            "unicorns_sacrificed": {name: 0 for name in player_names},
            "unicorns_stolen": {name: 0 for name in player_names},
        }

    def record_turn(self):
        """Record a turn."""
        if self._current_game:
            self._current_game["turns"] += 1

    def record_card_played(self, player_name: str):
        """Record a card played."""
        if self._current_game and player_name in self._current_game["cards_played"]:
            self._current_game["cards_played"][player_name] += 1

    def record_card_drawn(self, player_name: str):
        """Record a card drawn."""
        if self._current_game and player_name in self._current_game["cards_drawn"]:
            self._current_game["cards_drawn"][player_name] += 1

    def record_neigh(self, player_name: str):
        """Record a Neigh played."""
        if self._current_game and player_name in self._current_game["neighs_played"]:
            self._current_game["neighs_played"][player_name] += 1

    def record_destroy(self, player_name: str):
        """Record a unicorn destroyed."""
        if self._current_game and player_name in self._current_game["unicorns_destroyed"]:
            self._current_game["unicorns_destroyed"][player_name] += 1

    def record_sacrifice(self, player_name: str):
        """Record a unicorn sacrificed."""
        if self._current_game and player_name in self._current_game["unicorns_sacrificed"]:
            self._current_game["unicorns_sacrificed"][player_name] += 1

    def record_steal(self, player_name: str):
        """Record a unicorn stolen."""
        if self._current_game and player_name in self._current_game["unicorns_stolen"]:
            self._current_game["unicorns_stolen"][player_name] += 1

    def end_game(self, winner_idx: int, final_unicorn_counts: List[int]):
        """End the current game and record final stats."""
        if not self._current_game:
            return None

        end_time = datetime.now()
        duration = (end_time - self._current_game["start_time"]).total_seconds()

        game_stats = GameStats(
            game_id=self._current_game["game_id"],
            timestamp=self._current_game["start_time"].isoformat(),
            duration_seconds=duration,
            num_players=self._current_game["num_players"],
            player_names=self._current_game["player_names"],
            player_types=self._current_game["player_types"],
            winner_idx=winner_idx,
            winner_name=self._current_game["player_names"][winner_idx],
            total_turns=self._current_game["turns"],
            final_unicorn_counts=final_unicorn_counts,
            cards_played=self._current_game["cards_played"],
            cards_drawn=self._current_game["cards_drawn"],
            neighs_played=self._current_game["neighs_played"],
            unicorns_destroyed=self._current_game["unicorns_destroyed"],
            unicorns_sacrificed=self._current_game["unicorns_sacrificed"],
            unicorns_stolen=self._current_game["unicorns_stolen"],
        )

        self.games.append(game_stats)
        self._update_player_profiles(game_stats)
        self._current_game = None

        self.save()
        return game_stats

    def _update_player_profiles(self, game_stats: GameStats):
        """Update player profiles after a game."""
        # First ensure all players have profiles
        for i, name in enumerate(game_stats.player_names):
            if name not in self.player_profiles:
                self.player_profiles[name] = PlayerProfile(
                    name=name,
                    player_type=game_stats.player_types[i]
                )

        # Update stats for each player
        for i, name in enumerate(game_stats.player_names):
            profile = self.player_profiles[name]
            profile.games_played += 1
            profile.total_unicorns += game_stats.final_unicorn_counts[i]
            profile.total_cards_played += game_stats.cards_played.get(name, 0)
            profile.total_cards_drawn += game_stats.cards_drawn.get(name, 0)
            profile.total_neighs += game_stats.neighs_played.get(name, 0)
            profile.total_unicorns_destroyed += game_stats.unicorns_destroyed.get(name, 0)
            profile.total_unicorns_stolen += game_stats.unicorns_stolen.get(name, 0)

            # Update average turns
            total_turns = profile.avg_game_turns * (profile.games_played - 1)
            profile.avg_game_turns = (total_turns + game_stats.total_turns) / profile.games_played

            # Update win stats
            if i == game_stats.winner_idx:
                profile.games_won += 1
                profile.win_streak += 1
                if profile.win_streak > profile.best_win_streak:
                    profile.best_win_streak = profile.win_streak
            else:
                profile.win_streak = 0

        # Update ELO ratings (after all profiles exist)
        self._update_elo(game_stats)

    def _update_elo(self, game_stats: GameStats):
        """Update ELO ratings for all players."""
        K = 32  # ELO K-factor

        # Get all player ratings
        ratings = []
        for name in game_stats.player_names:
            ratings.append(self.player_profiles[name].elo_rating)

        # Calculate expected scores
        num_players = len(ratings)
        expected = []
        for i in range(num_players):
            exp_score = 0.0
            for j in range(num_players):
                if i != j:
                    exp_score += 1.0 / (1.0 + 10 ** ((ratings[j] - ratings[i]) / 400))
            expected.append(exp_score / (num_players - 1))

        # Calculate actual scores (winner gets 1, others get 0)
        actual = [0.0] * num_players
        actual[game_stats.winner_idx] = 1.0

        # Update ratings
        for i, name in enumerate(game_stats.player_names):
            profile = self.player_profiles[name]
            old_elo = profile.elo_rating
            profile.elo_rating += K * (actual[i] - expected[i])

            if profile.elo_rating > profile.highest_elo:
                profile.highest_elo = profile.elo_rating

    def get_leaderboard(self, sort_by: str = "elo") -> List[PlayerProfile]:
        """Get player profiles sorted by specified criterion."""
        profiles = list(self.player_profiles.values())

        if sort_by == "elo":
            profiles.sort(key=lambda p: p.elo_rating, reverse=True)
        elif sort_by == "wins":
            profiles.sort(key=lambda p: p.games_won, reverse=True)
        elif sort_by == "win_rate":
            profiles.sort(key=lambda p: p.win_rate, reverse=True)
        elif sort_by == "games":
            profiles.sort(key=lambda p: p.games_played, reverse=True)

        return profiles

    def get_recent_games(self, count: int = 10) -> List[GameStats]:
        """Get the most recent games."""
        return self.games[-count:][::-1]

    def get_head_to_head(self, player1: str, player2: str) -> Dict:
        """Get head-to-head statistics between two players."""
        games_together = []
        p1_wins = 0
        p2_wins = 0

        for game in self.games:
            if player1 in game.player_names and player2 in game.player_names:
                games_together.append(game)
                if game.winner_name == player1:
                    p1_wins += 1
                elif game.winner_name == player2:
                    p2_wins += 1

        return {
            "games_played": len(games_together),
            f"{player1}_wins": p1_wins,
            f"{player2}_wins": p2_wins,
            "recent_winner": games_together[-1].winner_name if games_together else None
        }

    def save(self):
        """Save statistics to disk."""
        stats_file = os.path.join(self.stats_dir, "statistics.json")

        data = {
            "games": [g.to_dict() for g in self.games],
            "player_profiles": {k: v.to_dict() for k, v in self.player_profiles.items()},
        }

        with open(stats_file, 'w') as f:
            json.dump(data, f, indent=2)

    def load(self):
        """Load statistics from disk."""
        stats_file = os.path.join(self.stats_dir, "statistics.json")

        if os.path.exists(stats_file):
            try:
                with open(stats_file, 'r') as f:
                    data = json.load(f)

                self.games = [GameStats.from_dict(g) for g in data.get("games", [])]
                self.player_profiles = {
                    k: PlayerProfile.from_dict(v)
                    for k, v in data.get("player_profiles", {}).items()
                }
            except (json.JSONDecodeError, TypeError, KeyError) as e:
                print(f"Warning: Could not load statistics: {e}")
                self.games = []
                self.player_profiles = {}

    def format_summary(self) -> str:
        """Format a summary of overall statistics."""
        lines = [
            "=" * 50,
            "           GAME STATISTICS SUMMARY",
            "=" * 50,
            "",
            f"Total Games Played: {len(self.games)}",
            f"Total Players Tracked: {len(self.player_profiles)}",
            "",
        ]

        if self.games:
            avg_duration = sum(g.duration_seconds for g in self.games) / len(self.games)
            avg_turns = sum(g.total_turns for g in self.games) / len(self.games)
            lines.extend([
                f"Average Game Duration: {avg_duration:.1f} seconds",
                f"Average Turns per Game: {avg_turns:.1f}",
                "",
            ])

        if self.player_profiles:
            lines.append("Top Players by ELO:")
            for i, profile in enumerate(self.get_leaderboard("elo")[:5], 1):
                lines.append(
                    f"  {i}. {profile.name}: {profile.elo_rating:.0f} "
                    f"({profile.games_won}W/{profile.games_played}G)"
                )

        lines.append("=" * 50)
        return "\n".join(lines)

    def format_player_stats(self, player_name: str) -> str:
        """Format detailed statistics for a player."""
        if player_name not in self.player_profiles:
            return f"No statistics found for player: {player_name}"

        p = self.player_profiles[player_name]

        lines = [
            "=" * 50,
            f"         PLAYER STATISTICS: {p.name}",
            "=" * 50,
            "",
            f"Player Type: {p.player_type}",
            f"ELO Rating: {p.elo_rating:.0f} (Peak: {p.highest_elo:.0f})",
            "",
            f"Games Played: {p.games_played}",
            f"Games Won: {p.games_won}",
            f"Win Rate: {p.win_rate * 100:.1f}%",
            f"Current Win Streak: {p.win_streak}",
            f"Best Win Streak: {p.best_win_streak}",
            "",
            f"Total Unicorns: {p.total_unicorns}",
            f"Avg Unicorns/Game: {p.avg_unicorns_per_game:.1f}",
            f"Total Cards Played: {p.total_cards_played}",
            f"Total Cards Drawn: {p.total_cards_drawn}",
            f"Total Neighs: {p.total_neighs}",
            f"Unicorns Destroyed: {p.total_unicorns_destroyed}",
            f"Unicorns Stolen: {p.total_unicorns_stolen}",
            f"Avg Turns/Game: {p.avg_game_turns:.1f}",
            "=" * 50,
        ]

        return "\n".join(lines)


# Global statistics tracker instance
STATS_TRACKER = StatisticsTracker()
