#!/usr/bin/env python3
"""Unstable Unicorns - Command Line Game with AI Opponents.

A digital implementation of the Unstable Unicorns card game
featuring multiple AI opponents including MCTS, Evolutionary, and Hybrid AI.
"""

import argparse
import sys
from typing import List, Optional

from game.game_engine import GameEngine
from game.statistics import STATS_TRACKER
from game.save_load import SAVE_MANAGER, quick_save, quick_load, autosave
from game.tournament import Tournament, TournamentFormat, run_quick_tournament
from players.player import Player
from players.human_player import HumanPlayer
from players.ai_player import RandomPlayer, RuleBasedPlayer
from ai.mcts import MCTSPlayer
from ai.evolutionary import EvolutionaryPlayer, TRAINED_WEIGHTS
from ai.hybrid import HybridPlayer
from ai.ismcts import ISMCTSPlayer
from ai.difficulty import (
    DifficultyLevel, create_ai_player, list_difficulties, parse_difficulty
)
from cli.colors import Color, colorize, bold, success, error, warning


def create_player(player_type: str, name: str, difficulty: str = "medium") -> Player:
    """Create a player based on type specification.

    Args:
        player_type: One of "human", "random", "rule", "mcts", "evo", "hybrid", "ismcts"
        name: Player name
        difficulty: AI difficulty level

    Returns:
        Configured player instance
    """
    if player_type == "human":
        return HumanPlayer(name)

    # Try to parse as difficulty level
    diff_level = parse_difficulty(player_type)
    if diff_level:
        return create_ai_player(name, diff_level)

    # Legacy player types
    if player_type == "random":
        return RandomPlayer(name)
    elif player_type == "rule":
        return RuleBasedPlayer(name)
    elif player_type == "mcts":
        iterations = {"easy": 100, "medium": 300, "hard": 800}.get(difficulty, 300)
        return MCTSPlayer(name, iterations=iterations, determinizations=3)
    elif player_type == "evo":
        return EvolutionaryPlayer(name, weights=TRAINED_WEIGHTS)
    elif player_type == "hybrid":
        return HybridPlayer(name, iterations=500, determinizations=5)
    elif player_type == "ismcts":
        return ISMCTSPlayer(name, iterations=500, determinizations=5)
    else:
        raise ValueError(f"Unknown player type: {player_type}")


def get_player_type_string(player_type: str) -> str:
    """Get a string representation of player type for statistics."""
    diff_level = parse_difficulty(player_type)
    if diff_level:
        return diff_level.value
    return player_type


def play_game(
    player_configs: List[tuple],
    verbose: bool = True,
    track_stats: bool = True
) -> int:
    """Play a single game.

    Args:
        player_configs: List of (player_type, name) tuples
        verbose: Whether to print game progress
        track_stats: Whether to track game statistics

    Returns:
        Index of winning player
    """
    # Create players
    player_names = [config[1] for config in player_configs]
    player_types = [get_player_type_string(config[0]) for config in player_configs]
    players = [create_player(config[0], config[1]) for config in player_configs]

    # Create and run game
    engine = GameEngine(player_names, verbose=verbose)
    engine.set_players(players)

    if track_stats:
        STATS_TRACKER.start_game(player_names, player_types)

    winner = engine.run_game()

    if track_stats:
        final_scores = [p.unicorn_count() for p in engine.state.players]
        STATS_TRACKER.end_game(winner, final_scores)

    return winner


def interactive_mode():
    """Run interactive game setup."""
    print("\n" + "=" * 60)
    print(colorize("  UNSTABLE UNICORNS", Color.MAGENTA, bold=True))
    print(colorize("  Digital Edition with AI Opponents", Color.CYAN))
    print("=" * 60)

    print("\nMain Menu:")
    print("  1. New Game")
    print("  2. Load Game")
    print("  3. Tournament Mode")
    print("  4. View Statistics")
    print("  5. AI Benchmark")
    print("  6. Train AI")
    print("  7. Quit")

    while True:
        try:
            choice = int(input("\nChoice: "))
            if 1 <= choice <= 7:
                break
            print("Please enter 1-7.")
        except ValueError:
            print("Please enter a valid number.")

    if choice == 1:
        new_game_menu()
    elif choice == 2:
        load_game_menu()
    elif choice == 3:
        tournament_menu()
    elif choice == 4:
        statistics_menu()
    elif choice == 5:
        benchmark_mode()
    elif choice == 6:
        train_evolutionary()
    elif choice == 7:
        print("Goodbye!")
        sys.exit(0)


def new_game_menu():
    """Set up a new game."""
    print("\n" + "-" * 40)
    print("  NEW GAME SETUP")
    print("-" * 40)

    # Get number of players
    while True:
        try:
            num_players = int(input("\nNumber of players (2-6): "))
            if 2 <= num_players <= 6:
                break
            print("Please enter a number between 2 and 6.")
        except ValueError:
            print("Please enter a valid number.")

    # Show difficulty options
    print("\n" + list_difficulties())

    # Configure each player
    player_configs = []

    print("\nConfigure players (enter 'h' for human, or difficulty: e/m/h/x/n):")

    for i in range(num_players):
        print(f"\n--- Player {i + 1} ---")
        name = input(f"Name: ").strip() or f"Player {i + 1}"

        while True:
            type_input = input("Type (h=human, e/m/h/x/n=AI difficulty): ").strip().lower()

            if type_input == 'h':
                player_configs.append(("human", name))
                break
            elif type_input in ['e', 'm', 'h', 'x', 'n']:
                diff_map = {'e': 'easy', 'm': 'medium', 'h': 'hard', 'x': 'expert', 'n': 'nightmare'}
                player_configs.append((diff_map[type_input], name))
                break
            else:
                print("Invalid type. Use h for human, e/m/h/x/n for AI difficulties.")

    # Play the game
    print("\n" + "=" * 60)
    print(success("Starting game..."))
    print("=" * 60)

    winner = play_game(player_configs, verbose=True)

    print(f"\n{success('Game over!')} {bold(player_configs[winner][1])} wins!")

    # Ask to play again
    again = input("\nPlay again? (y/n): ").strip().lower()
    if again == 'y':
        new_game_menu()
    else:
        interactive_mode()


def load_game_menu():
    """Load a saved game."""
    print("\n" + "-" * 40)
    print("  LOAD GAME")
    print("-" * 40)

    saves = SAVE_MANAGER.list_saves()

    if not saves:
        print(warning("\nNo saved games found."))
        input("Press Enter to continue...")
        interactive_mode()
        return

    print(SAVE_MANAGER.format_save_list())

    print("\nEnter save number to load (0 to cancel): ")
    while True:
        try:
            choice = int(input("Choice: "))
            if choice == 0:
                interactive_mode()
                return
            if 1 <= choice <= len(saves):
                break
            print(f"Please enter 0-{len(saves)}.")
        except ValueError:
            print("Please enter a valid number.")

    save = saves[choice - 1]
    try:
        state, metadata = SAVE_MANAGER.load_game(save["name"])
        print(success(f"\nLoaded: {save['name']}"))

        # Resume game
        player_types = metadata.get("player_types", ["unknown"] * state.num_players)
        player_configs = list(zip(player_types, [p.name for p in state.players]))

        players = [create_player(config[0], config[1]) for config in player_configs]

        engine = GameEngine([p.name for p in state.players], verbose=True)
        engine.state = state
        engine.set_players(players)

        winner = engine.run_game()
        print(f"\n{success('Game over!')} {bold(state.players[winner].name)} wins!")

    except Exception as e:
        print(error(f"Failed to load game: {e}"))

    input("\nPress Enter to continue...")
    interactive_mode()


def tournament_menu():
    """Set up and run a tournament."""
    print("\n" + "-" * 40)
    print("  TOURNAMENT MODE")
    print("-" * 40)

    print("\nTournament Formats:")
    print("  1. Round Robin (everyone plays everyone)")
    print("  2. Swiss (matched by score)")
    print("  3. Single Elimination")
    print("  4. Double Elimination")
    print("  5. Quick AI Tournament")
    print("  6. Back to main menu")

    while True:
        try:
            choice = int(input("\nChoice: "))
            if 1 <= choice <= 6:
                break
        except ValueError:
            pass
        print("Please enter 1-6.")

    if choice == 6:
        interactive_mode()
        return

    if choice == 5:
        # Quick AI tournament
        result = run_quick_tournament()
        input("\nPress Enter to continue...")
        interactive_mode()
        return

    formats = [
        TournamentFormat.ROUND_ROBIN,
        TournamentFormat.SWISS,
        TournamentFormat.ELIMINATION,
        TournamentFormat.DOUBLE_ELIMINATION,
    ]
    tournament_format = formats[choice - 1]

    # Get players
    while True:
        try:
            num_players = int(input("\nNumber of players (3-8): "))
            if 3 <= num_players <= 8:
                break
        except ValueError:
            pass
        print("Please enter 3-8.")

    players = []
    for i in range(num_players):
        print(f"\n--- Player {i + 1} ---")
        name = input("Name: ").strip() or f"Player {i + 1}"

        while True:
            type_input = input("Type (h=human, e/m/h/x/n=AI): ").strip().lower()

            if type_input == 'h':
                players.append((name, "human"))
                break
            elif type_input in ['e', 'm', 'h', 'x', 'n']:
                diff_map = {'e': 'easy', 'm': 'medium', 'h': 'hard', 'x': 'expert', 'n': 'nightmare'}
                players.append((name, diff_map[type_input]))
                break

    # Run tournament
    tournament = Tournament(players, tournament_format)
    result = tournament.run()

    input("\nPress Enter to continue...")
    interactive_mode()


def statistics_menu():
    """View game statistics."""
    print("\n" + "-" * 40)
    print("  STATISTICS")
    print("-" * 40)

    print("\nOptions:")
    print("  1. Overall Summary")
    print("  2. Player Statistics")
    print("  3. Leaderboard")
    print("  4. Recent Games")
    print("  5. Back to main menu")

    while True:
        try:
            choice = int(input("\nChoice: "))
            if 1 <= choice <= 5:
                break
        except ValueError:
            pass
        print("Please enter 1-5.")

    if choice == 1:
        print("\n" + STATS_TRACKER.format_summary())
    elif choice == 2:
        name = input("\nEnter player name: ").strip()
        print("\n" + STATS_TRACKER.format_player_stats(name))
    elif choice == 3:
        print("\n" + "-" * 40)
        print("  LEADERBOARD (by ELO)")
        print("-" * 40)
        for i, player in enumerate(STATS_TRACKER.get_leaderboard("elo")[:10], 1):
            print(f"  {i}. {player.name}: {player.elo_rating:.0f} "
                  f"({player.win_rate * 100:.1f}% win rate)")
    elif choice == 4:
        print("\n" + "-" * 40)
        print("  RECENT GAMES")
        print("-" * 40)
        for game in STATS_TRACKER.get_recent_games(10):
            print(f"  {game.timestamp[:10]} - Winner: {game.winner_name} "
                  f"({game.num_players} players, {game.total_turns} turns)")
    elif choice == 5:
        interactive_mode()
        return

    input("\nPress Enter to continue...")
    statistics_menu()


def benchmark_mode(games: int = 50):
    """Run AI benchmark comparisons."""
    print("\n" + "=" * 60)
    print(colorize("  AI BENCHMARK MODE", Color.CYAN, bold=True))
    print(f"  Running {games} games per matchup...")
    print("=" * 60)

    ai_types = [
        ("random", "Random"),
        ("rule", "RuleBased"),
        ("evo", "Evolutionary"),
        ("mcts", "MCTS"),
        ("hybrid", "Hybrid"),
    ]

    results = {}

    for i, (type1, name1) in enumerate(ai_types):
        for type2, name2 in ai_types[i + 1:]:
            print(f"\n{name1} vs {name2}...")

            wins1, wins2 = 0, 0
            for game_num in range(games):
                winner = play_game(
                    [(type1, name1), (type2, name2)],
                    verbose=False,
                    track_stats=False
                )
                if winner == 0:
                    wins1 += 1
                else:
                    wins2 += 1

                if (game_num + 1) % 10 == 0:
                    print(f"  Games: {game_num + 1}, {name1}: {wins1}, {name2}: {wins2}")

            results[f"{name1} vs {name2}"] = (wins1, wins2)
            print(f"  Final: {name1}: {wins1} ({wins1 / games * 100:.1f}%), "
                  f"{name2}: {wins2} ({wins2 / games * 100:.1f}%)")

    # Print summary
    print("\n" + "=" * 60)
    print(colorize("  BENCHMARK RESULTS", Color.GREEN, bold=True))
    print("=" * 60)
    for matchup, (w1, w2) in results.items():
        print(f"  {matchup}: {w1} - {w2}")


def train_evolutionary(generations: int = 50):
    """Train evolutionary AI weights."""
    from ai.evolutionary import EvolutionaryTrainer

    print("\n" + "=" * 60)
    print(colorize("  EVOLUTIONARY AI TRAINING", Color.YELLOW, bold=True))
    print(f"  Running {generations} generations...")
    print("=" * 60)

    trainer = EvolutionaryTrainer(
        population_size=20,
        games_per_evaluation=10,
        mutation_rate=0.15,
        elite_count=4
    )

    best_weights = trainer.train(generations=generations, verbose=True)

    print("\nBest weights found:")
    print(f"  basic_unicorn: {best_weights.basic_unicorn:.3f}")
    print(f"  magical_unicorn: {best_weights.magical_unicorn:.3f}")
    print(f"  unicorn_count: {best_weights.unicorn_count:.3f}")
    print(f"  close_to_win: {best_weights.close_to_win:.3f}")
    print(f"  neigh_value: {best_weights.neigh_value:.3f}")

    return best_weights


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Unstable Unicorns - Card Game with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                     # Interactive mode
  python main.py --quick             # Quick game vs Expert AI
  python main.py --quick -d hard     # Quick game vs Hard AI
  python main.py --benchmark         # Run AI benchmarks
  python main.py --train             # Train evolutionary AI
  python main.py --tournament        # Quick AI tournament
  python main.py --stats             # View statistics

Difficulty Levels:
  easy       - Random AI
  medium     - Rule-based heuristic AI
  hard       - Evolutionary AI
  expert     - MCTS AI (500 iterations)
  nightmare  - Hybrid MCTS + Evolutionary AI

Player Types (legacy):
  human  - Human player (interactive)
  random - Random move AI
  rule   - Rule-based heuristic AI
  mcts   - Monte Carlo Tree Search AI
  evo    - Evolutionary trained AI
  hybrid - Hybrid MCTS + Evolutionary AI
        """
    )

    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Quick game: You vs AI"
    )
    parser.add_argument(
        "--difficulty", "-d",
        type=str,
        default="expert",
        help="AI difficulty for quick game (easy/medium/hard/expert/nightmare)"
    )
    parser.add_argument(
        "--benchmark", "-b",
        action="store_true",
        help="Run AI benchmark comparisons"
    )
    parser.add_argument(
        "--train", "-t",
        action="store_true",
        help="Train evolutionary AI"
    )
    parser.add_argument(
        "--tournament",
        action="store_true",
        help="Run quick AI tournament"
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="View statistics"
    )
    parser.add_argument(
        "--games", "-g",
        type=int,
        default=50,
        help="Number of games for benchmark (default: 50)"
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=50,
        help="Generations for training (default: 50)"
    )
    parser.add_argument(
        "--players", "-p",
        nargs="+",
        help="Player specs: type:name (e.g., human:You expert:Bot)"
    )

    args = parser.parse_args()

    if args.benchmark:
        benchmark_mode(args.games)
    elif args.train:
        train_evolutionary(args.generations)
    elif args.tournament:
        result = run_quick_tournament()
    elif args.stats:
        print(STATS_TRACKER.format_summary())
    elif args.quick:
        difficulty = args.difficulty.lower()
        print(f"\nQuick Game: You vs {difficulty.capitalize()} AI")
        play_game([("human", "You"), (difficulty, f"{difficulty.capitalize()} AI")], verbose=True)
    elif args.players:
        # Parse player specs
        player_configs = []
        for spec in args.players:
            if ":" in spec:
                ptype, name = spec.split(":", 1)
            else:
                ptype, name = spec, spec.title()
            player_configs.append((ptype, name))
        play_game(player_configs, verbose=True)
    else:
        interactive_mode()


if __name__ == "__main__":
    main()
