"""Tournament mode for Unstable Unicorns."""

import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum

from game.game_engine import GameEngine
from game.statistics import STATS_TRACKER
from ai.difficulty import DifficultyLevel, create_ai_player, DIFFICULTY_CONFIGS


class TournamentFormat(Enum):
    """Tournament format types."""
    ROUND_ROBIN = "round_robin"
    SWISS = "swiss"
    ELIMINATION = "elimination"
    DOUBLE_ELIMINATION = "double_elimination"


@dataclass
class TournamentPlayer:
    """A player in the tournament."""
    name: str
    player_type: str  # 'human' or AI difficulty level
    elo_rating: float = 1000.0
    wins: int = 0
    losses: int = 0
    games_played: int = 0
    points: float = 0.0
    buchholz: float = 0.0  # Tiebreaker score
    opponents: List[str] = field(default_factory=list)
    is_eliminated: bool = False

    @property
    def win_rate(self) -> float:
        if self.games_played == 0:
            return 0.0
        return self.wins / self.games_played


@dataclass
class TournamentMatch:
    """A match in the tournament."""
    match_id: int
    round_num: int
    player_names: List[str]
    winner_name: Optional[str] = None
    is_bye: bool = False
    final_scores: Optional[List[int]] = None


@dataclass
class TournamentResult:
    """Final tournament results."""
    format: TournamentFormat
    total_rounds: int
    total_matches: int
    standings: List[TournamentPlayer]
    matches: List[TournamentMatch]
    champion: str


class Tournament:
    """
    Tournament manager for running competitive games.

    Supports multiple formats:
    - Round Robin: Every player plays every other player
    - Swiss: Players with similar scores play each other
    - Elimination: Single elimination bracket
    - Double Elimination: Players get a second chance
    """

    def __init__(self, players: List[Tuple[str, str]], format: TournamentFormat,
                 games_per_round: int = 1, verbose: bool = True):
        """
        Initialize tournament.

        Args:
            players: List of (name, type) tuples where type is 'human' or difficulty level
            format: Tournament format
            games_per_round: Number of games per matchup (for averaging)
            verbose: Whether to print progress
        """
        self.players = {
            name: TournamentPlayer(name=name, player_type=player_type)
            for name, player_type in players
        }
        self.format = format
        self.games_per_round = games_per_round
        self.verbose = verbose
        self.matches: List[TournamentMatch] = []
        self.current_round = 0
        self.match_counter = 0

        # For elimination brackets
        self.upper_bracket: List[str] = []
        self.lower_bracket: List[str] = []

    def run(self) -> TournamentResult:
        """Run the tournament and return results."""
        if self.verbose:
            print(self._format_header())

        if self.format == TournamentFormat.ROUND_ROBIN:
            self._run_round_robin()
        elif self.format == TournamentFormat.SWISS:
            self._run_swiss()
        elif self.format == TournamentFormat.ELIMINATION:
            self._run_elimination()
        elif self.format == TournamentFormat.DOUBLE_ELIMINATION:
            self._run_double_elimination()

        # Calculate final standings
        standings = self._calculate_standings()

        if self.verbose:
            print(self._format_results(standings))

        return TournamentResult(
            format=self.format,
            total_rounds=self.current_round,
            total_matches=len(self.matches),
            standings=standings,
            matches=self.matches,
            champion=standings[0].name
        )

    def _run_round_robin(self):
        """Run round robin tournament."""
        player_names = list(self.players.keys())
        n = len(player_names)

        # Generate all pairings using circle method
        if n % 2 == 1:
            player_names.append(None)  # Bye
            n += 1

        rounds = n - 1
        for round_num in range(rounds):
            self.current_round = round_num + 1

            if self.verbose:
                print(f"\n--- Round {self.current_round} ---")

            # Generate pairings for this round
            pairings = []
            for i in range(n // 2):
                p1 = player_names[i]
                p2 = player_names[n - 1 - i]
                if p1 is not None and p2 is not None:
                    pairings.append((p1, p2))

            # Run all matches in this round
            for p1, p2 in pairings:
                self._play_match([p1, p2])

            # Rotate players (keep first player fixed)
            player_names = [player_names[0]] + [player_names[-1]] + player_names[1:-1]

    def _run_swiss(self, num_rounds: Optional[int] = None):
        """Run Swiss system tournament."""
        player_names = list(self.players.keys())
        n = len(player_names)

        # Default number of rounds: log2(n) rounded up
        if num_rounds is None:
            import math
            num_rounds = max(3, int(math.ceil(math.log2(n))))

        for round_num in range(num_rounds):
            self.current_round = round_num + 1

            if self.verbose:
                print(f"\n--- Round {self.current_round} ---")

            # Sort players by score, then by Buchholz
            sorted_players = sorted(
                player_names,
                key=lambda p: (self.players[p].points, self.players[p].buchholz),
                reverse=True
            )

            # Pair players with similar scores
            paired = set()
            pairings = []

            for i, p1 in enumerate(sorted_players):
                if p1 in paired:
                    continue

                # Find best opponent (similar score, haven't played)
                for p2 in sorted_players[i + 1:]:
                    if p2 in paired and p2 not in self.players[p1].opponents:
                        pairings.append((p1, p2))
                        paired.add(p1)
                        paired.add(p2)
                        break
                else:
                    # No available opponent found, pair with next available
                    for p2 in sorted_players[i + 1:]:
                        if p2 not in paired:
                            pairings.append((p1, p2))
                            paired.add(p1)
                            paired.add(p2)
                            break

            # Handle bye if odd number of players
            unpaired = [p for p in sorted_players if p not in paired]
            for p in unpaired:
                # Give bye to lowest-ranked unpaired player
                self.players[p].points += 0.5

            # Run matches
            for p1, p2 in pairings:
                self._play_match([p1, p2])

            # Update Buchholz scores
            self._update_buchholz()

    def _run_elimination(self):
        """Run single elimination tournament."""
        player_names = list(self.players.keys())
        random.shuffle(player_names)

        # Pad to power of 2 with byes
        import math
        bracket_size = 2 ** int(math.ceil(math.log2(len(player_names))))

        bracket = player_names + [None] * (bracket_size - len(player_names))

        round_num = 0
        while len(bracket) > 1:
            round_num += 1
            self.current_round = round_num

            if self.verbose:
                print(f"\n--- Round {round_num} ---")

            next_round = []
            for i in range(0, len(bracket), 2):
                p1, p2 = bracket[i], bracket[i + 1]

                if p1 is None:
                    next_round.append(p2)
                elif p2 is None:
                    next_round.append(p1)
                else:
                    winner = self._play_match([p1, p2])
                    next_round.append(winner)

                    # Mark loser as eliminated
                    loser = p1 if winner == p2 else p2
                    self.players[loser].is_eliminated = True

            bracket = next_round

    def _run_double_elimination(self):
        """Run double elimination tournament."""
        player_names = list(self.players.keys())
        random.shuffle(player_names)

        self.upper_bracket = player_names.copy()
        self.lower_bracket = []

        round_num = 0

        # Upper bracket rounds
        while len(self.upper_bracket) > 1 or len(self.lower_bracket) > 1:
            round_num += 1
            self.current_round = round_num

            if self.verbose:
                print(f"\n--- Round {round_num} ---")

            # Upper bracket matches
            if len(self.upper_bracket) > 1:
                if self.verbose:
                    print("Upper Bracket:")
                new_upper = []
                losers = []

                for i in range(0, len(self.upper_bracket), 2):
                    if i + 1 < len(self.upper_bracket):
                        p1, p2 = self.upper_bracket[i], self.upper_bracket[i + 1]
                        winner = self._play_match([p1, p2])
                        new_upper.append(winner)
                        losers.append(p1 if winner == p2 else p2)
                    else:
                        new_upper.append(self.upper_bracket[i])

                self.upper_bracket = new_upper
                self.lower_bracket.extend(losers)

            # Lower bracket matches
            if len(self.lower_bracket) > 1:
                if self.verbose:
                    print("Lower Bracket:")
                new_lower = []

                for i in range(0, len(self.lower_bracket), 2):
                    if i + 1 < len(self.lower_bracket):
                        p1, p2 = self.lower_bracket[i], self.lower_bracket[i + 1]
                        winner = self._play_match([p1, p2])
                        new_lower.append(winner)
                        loser = p1 if winner == p2 else p2
                        self.players[loser].is_eliminated = True
                    else:
                        new_lower.append(self.lower_bracket[i])

                self.lower_bracket = new_lower

        # Grand finals
        if self.upper_bracket and self.lower_bracket:
            if self.verbose:
                print("\n--- Grand Finals ---")

            p1, p2 = self.upper_bracket[0], self.lower_bracket[0]
            winner = self._play_match([p1, p2])

            # If lower bracket winner wins, play reset match
            if winner == p2:
                if self.verbose:
                    print("\n--- Grand Finals Reset ---")
                winner = self._play_match([p1, p2])

    def _play_match(self, player_names: List[str]) -> str:
        """Play a match between players and return winner name."""
        self.match_counter += 1

        if self.verbose:
            print(f"  Match {self.match_counter}: {' vs '.join(player_names)}")

        # Create players
        players = []
        player_types = []
        for name in player_names:
            p_info = self.players[name]
            if p_info.player_type == "human":
                from players.human_player import HumanPlayer
                players.append(HumanPlayer(name))
                player_types.append("human")
            else:
                difficulty = DifficultyLevel(p_info.player_type.lower())
                players.append(create_ai_player(name, difficulty))
                player_types.append(p_info.player_type)

        # Run game(s)
        wins = {name: 0 for name in player_names}

        for game_num in range(self.games_per_round):
            engine = GameEngine(player_names, verbose=False)
            engine.set_players(players)

            STATS_TRACKER.start_game(player_names, player_types)
            winner_idx = engine.run_game()
            final_scores = [p.unicorn_count() for p in engine.state.players]
            STATS_TRACKER.end_game(winner_idx, final_scores)

            wins[player_names[winner_idx]] += 1

        # Determine match winner
        winner_name = max(wins.keys(), key=lambda k: wins[k])
        loser_names = [n for n in player_names if n != winner_name]

        # Record match
        match = TournamentMatch(
            match_id=self.match_counter,
            round_num=self.current_round,
            player_names=player_names,
            winner_name=winner_name,
            final_scores=list(wins.values())
        )
        self.matches.append(match)

        # Update player stats
        self.players[winner_name].wins += 1
        self.players[winner_name].games_played += 1
        self.players[winner_name].points += 1.0
        self.players[winner_name].opponents.extend(loser_names)

        for loser in loser_names:
            self.players[loser].losses += 1
            self.players[loser].games_played += 1
            self.players[loser].opponents.append(winner_name)

        # Update ELO ratings
        self._update_elo(winner_name, loser_names)

        if self.verbose:
            print(f"    Winner: {winner_name}")

        return winner_name

    def _update_elo(self, winner: str, losers: List[str]):
        """Update ELO ratings after a match."""
        K = 32

        winner_p = self.players[winner]

        for loser in losers:
            loser_p = self.players[loser]

            # Calculate expected scores
            exp_winner = 1.0 / (1.0 + 10 ** ((loser_p.elo_rating - winner_p.elo_rating) / 400))
            exp_loser = 1.0 - exp_winner

            # Update ratings
            winner_p.elo_rating += K * (1.0 - exp_winner)
            loser_p.elo_rating += K * (0.0 - exp_loser)

    def _update_buchholz(self):
        """Update Buchholz scores (sum of opponents' scores)."""
        for player in self.players.values():
            player.buchholz = sum(
                self.players[opp].points
                for opp in player.opponents
                if opp in self.players
            )

    def _calculate_standings(self) -> List[TournamentPlayer]:
        """Calculate final standings."""
        standings = list(self.players.values())

        # Sort by: points, buchholz, elo, wins
        standings.sort(
            key=lambda p: (p.points, p.buchholz, p.elo_rating, p.wins),
            reverse=True
        )

        return standings

    def _format_header(self) -> str:
        """Format tournament header."""
        lines = [
            "=" * 60,
            "              UNSTABLE UNICORNS TOURNAMENT",
            "=" * 60,
            "",
            f"Format: {self.format.value.replace('_', ' ').title()}",
            f"Players: {len(self.players)}",
            f"Games per Match: {self.games_per_round}",
            "",
            "Participants:",
        ]

        for name, player in self.players.items():
            lines.append(f"  - {name} ({player.player_type})")

        lines.extend(["", "=" * 60])
        return "\n".join(lines)

    def _format_results(self, standings: List[TournamentPlayer]) -> str:
        """Format tournament results."""
        lines = [
            "",
            "=" * 60,
            "                 TOURNAMENT RESULTS",
            "=" * 60,
            "",
            "Final Standings:",
            "",
            f"{'Rank':<6}{'Player':<20}{'W-L':<10}{'Points':<10}{'ELO':<10}",
            "-" * 56,
        ]

        for i, player in enumerate(standings, 1):
            lines.append(
                f"{i:<6}{player.name:<20}{player.wins}-{player.losses:<7}"
                f"{player.points:<10.1f}{player.elo_rating:<10.0f}"
            )

        lines.extend([
            "",
            "-" * 56,
            f"Champion: {standings[0].name}",
            f"Total Matches: {len(self.matches)}",
            f"Total Rounds: {self.current_round}",
            "=" * 60,
        ])

        return "\n".join(lines)


def run_quick_tournament(num_ai_players: int = 4,
                         difficulties: Optional[List[str]] = None,
                         format: TournamentFormat = TournamentFormat.ROUND_ROBIN) -> TournamentResult:
    """Run a quick AI tournament."""
    if difficulties is None:
        difficulties = ["easy", "medium", "hard", "expert"]

    # Create player list
    players = []
    for i in range(num_ai_players):
        diff = difficulties[i % len(difficulties)]
        name = f"AI_{diff.capitalize()}_{i + 1}"
        players.append((name, diff))

    tournament = Tournament(players, format)
    return tournament.run()


def run_benchmark_tournament(iterations: int = 5) -> Dict:
    """Run a benchmark tournament to compare AI difficulties."""
    results = {
        "easy": {"wins": 0, "games": 0},
        "medium": {"wins": 0, "games": 0},
        "hard": {"wins": 0, "games": 0},
        "expert": {"wins": 0, "games": 0},
    }

    print("Running benchmark tournament...")
    print(f"Iterations: {iterations}")
    print()

    for i in range(iterations):
        print(f"Iteration {i + 1}/{iterations}")

        players = [
            ("Easy", "easy"),
            ("Medium", "medium"),
            ("Hard", "hard"),
            ("Expert", "expert"),
        ]

        tournament = Tournament(players, TournamentFormat.ROUND_ROBIN, verbose=False)
        result = tournament.run()

        for player in result.standings:
            diff = player.player_type.lower()
            if diff in results:
                results[diff]["wins"] += player.wins
                results[diff]["games"] += player.games_played

    print("\nBenchmark Results:")
    print("=" * 40)
    for diff, data in results.items():
        win_rate = data["wins"] / data["games"] if data["games"] > 0 else 0
        print(f"{diff.capitalize():10}: {win_rate * 100:.1f}% win rate ({data['wins']}/{data['games']})")

    return results
