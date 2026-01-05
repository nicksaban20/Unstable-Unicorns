"""Human player implementation with CLI input."""

from typing import List, TYPE_CHECKING

from players.player import Player

if TYPE_CHECKING:
    from game.game_state import GameState
    from game.action import Action


class HumanPlayer(Player):
    """Human player that gets input from command line."""

    def choose_action(self, state: 'GameState', valid_actions: List['Action']) -> 'Action':
        """Prompt human to choose an action."""
        from cli.display import Display

        print("\n" + "=" * 40)
        Display.show_player_view(state, state.current_player_idx)
        print("\nAvailable actions:")

        for i, action in enumerate(valid_actions):
            print(f"  {i + 1}. {action}")

        while True:
            try:
                choice = input("\nChoose action (number): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(valid_actions):
                    return valid_actions[idx]
                print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a number.")
            except KeyboardInterrupt:
                print("\nGame interrupted.")
                raise

    def choose_target(
        self,
        state: 'GameState',
        valid_targets: List,
        prompt: str
    ) -> object:
        """Prompt human to choose a target."""
        print(f"\n{prompt}")

        for i, target in enumerate(valid_targets):
            if hasattr(target, 'name'):
                print(f"  {i + 1}. {target.name}")
            else:
                print(f"  {i + 1}. {target}")

        while True:
            try:
                choice = input("\nChoose target (number): ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(valid_targets):
                    return valid_targets[idx]
                print("Invalid choice. Try again.")
            except ValueError:
                print("Please enter a number.")
            except KeyboardInterrupt:
                print("\nGame interrupted.")
                raise

    def notify(self, message: str) -> None:
        """Display notification to human player."""
        print(f"[!] {message}")
