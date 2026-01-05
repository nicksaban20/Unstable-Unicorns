"""AI difficulty levels for Unstable Unicorns."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from players.ai_player import RandomPlayer, RuleBasedPlayer
from ai.mcts import MCTSPlayer
from ai.evolutionary import EvolutionaryPlayer, TRAINED_WEIGHTS
from ai.hybrid import HybridPlayer
from ai.ismcts import ISMCTSPlayer


class DifficultyLevel(Enum):
    """AI difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"
    NIGHTMARE = "nightmare"


@dataclass
class DifficultyConfig:
    """Configuration for a difficulty level."""
    name: str
    description: str
    ai_type: str  # 'random', 'rule_based', 'mcts', 'evolutionary', 'hybrid', 'ismcts'
    mcts_iterations: int = 100
    mcts_determinizations: int = 3
    thinking_time_display: str = "instant"


# Difficulty configurations
DIFFICULTY_CONFIGS = {
    DifficultyLevel.EASY: DifficultyConfig(
        name="Easy",
        description="Random AI - makes completely random decisions",
        ai_type="random",
        thinking_time_display="instant"
    ),
    DifficultyLevel.MEDIUM: DifficultyConfig(
        name="Medium",
        description="Rule-based AI - follows basic strategy heuristics",
        ai_type="rule_based",
        thinking_time_display="instant"
    ),
    DifficultyLevel.HARD: DifficultyConfig(
        name="Hard",
        description="Evolutionary AI - uses evolved weights for decision-making",
        ai_type="evolutionary",
        mcts_iterations=200,
        mcts_determinizations=3,
        thinking_time_display="~0.5s"
    ),
    DifficultyLevel.EXPERT: DifficultyConfig(
        name="Expert",
        description="MCTS AI - uses Monte Carlo Tree Search with deeper exploration",
        ai_type="mcts",
        mcts_iterations=500,
        mcts_determinizations=5,
        thinking_time_display="~1s"
    ),
    DifficultyLevel.NIGHTMARE: DifficultyConfig(
        name="Nightmare",
        description="Hybrid AI - combines MCTS with evolutionary heuristics for optimal play",
        ai_type="hybrid",
        mcts_iterations=1000,
        mcts_determinizations=8,
        thinking_time_display="~2s"
    ),
}


def create_ai_player(name: str, difficulty: DifficultyLevel) -> object:
    """Create an AI player with the specified difficulty level."""
    config = DIFFICULTY_CONFIGS[difficulty]

    if config.ai_type == "random":
        return RandomPlayer(name)

    elif config.ai_type == "rule_based":
        return RuleBasedPlayer(name)

    elif config.ai_type == "evolutionary":
        return EvolutionaryPlayer(name, weights=TRAINED_WEIGHTS)

    elif config.ai_type == "mcts":
        return MCTSPlayer(
            name,
            iterations=config.mcts_iterations,
            determinizations=config.mcts_determinizations
        )

    elif config.ai_type == "hybrid":
        return HybridPlayer(
            name,
            iterations=config.mcts_iterations,
            determinizations=config.mcts_determinizations,
            weights=TRAINED_WEIGHTS
        )

    elif config.ai_type == "ismcts":
        return ISMCTSPlayer(
            name,
            iterations=config.mcts_iterations,
            determinizations=config.mcts_determinizations
        )

    else:
        raise ValueError(f"Unknown AI type: {config.ai_type}")


def get_difficulty_info(difficulty: DifficultyLevel) -> str:
    """Get a description of the difficulty level."""
    config = DIFFICULTY_CONFIGS[difficulty]
    return f"{config.name}: {config.description} (think time: {config.thinking_time_display})"


def list_difficulties() -> str:
    """List all available difficulties."""
    lines = ["Available Difficulty Levels:", ""]
    for level in DifficultyLevel:
        config = DIFFICULTY_CONFIGS[level]
        lines.append(f"  {level.value.upper():10} - {config.name}")
        lines.append(f"              {config.description}")
        lines.append(f"              Thinking time: {config.thinking_time_display}")
        lines.append("")
    return "\n".join(lines)


def parse_difficulty(difficulty_str: str) -> Optional[DifficultyLevel]:
    """Parse a difficulty string to a DifficultyLevel."""
    difficulty_str = difficulty_str.lower().strip()

    for level in DifficultyLevel:
        if level.value == difficulty_str:
            return level

    # Also accept short forms
    short_forms = {
        "e": DifficultyLevel.EASY,
        "m": DifficultyLevel.MEDIUM,
        "h": DifficultyLevel.HARD,
        "x": DifficultyLevel.EXPERT,
        "n": DifficultyLevel.NIGHTMARE,
    }

    return short_forms.get(difficulty_str)
