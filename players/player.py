"""Base player class for Unstable Unicorns."""

from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from game.game_state import GameState
    from game.action import Action


class Player(ABC):
    """Abstract base class for all player types."""

    def __init__(self, name: str):
        """Initialize a player.

        Args:
            name: Display name for the player
        """
        self.name = name

    @abstractmethod
    def choose_action(self, state: 'GameState', valid_actions: List['Action']) -> 'Action':
        """Choose an action from the list of valid actions.

        Args:
            state: Current game state
            valid_actions: List of legal actions to choose from

        Returns:
            The chosen action
        """
        pass

    @abstractmethod
    def choose_target(
        self,
        state: 'GameState',
        valid_targets: List,
        prompt: str
    ) -> object:
        """Choose a target for an effect.

        Args:
            state: Current game state
            valid_targets: List of valid targets to choose from
            prompt: Description of what's being chosen

        Returns:
            The chosen target
        """
        pass

    def notify(self, message: str) -> None:
        """Receive a notification about game events.

        Override this to handle notifications (e.g., display to human player).
        """
        pass
