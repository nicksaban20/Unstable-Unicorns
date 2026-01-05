"""CLI display system for Unstable Unicorns with color support."""

from typing import TYPE_CHECKING

from cli.colors import (
    colorize, Color, bold, dim, success, error, warning, info, highlight,
    colorize_card, symbol, Box, print_header, print_subheader, progress_bar
)

if TYPE_CHECKING:
    from game.game_state import GameState
    from cards.card import CardInstance


class Display:
    """Handles CLI display of game state and information."""

    @staticmethod
    def show_game_state(state: 'GameState') -> None:
        """Display the full game state (for debugging/spectating)."""
        print_header(f"GAME STATE - Turn {state.turn_number}", 60)
        print(f"  Phase: {colorize(state.phase.name, Color.BRIGHT_YELLOW)}")
        print()
        print(f"  {symbol('diamond')} Draw pile: {colorize(str(len(state.draw_pile)), Color.BRIGHT_WHITE)} cards")
        print(f"  {symbol('diamond')} Discard pile: {colorize(str(len(state.discard_pile)), Color.BRIGHT_WHITE)} cards")
        print(f"  {symbol('unicorn', 'U')} Nursery: {colorize(str(len(state.nursery)), Color.BRIGHT_WHITE)} baby unicorns")

        for player in state.players:
            is_current = player.player_idx == state.current_player_idx
            marker = colorize(" ◀ CURRENT", Color.BRIGHT_GREEN) if is_current else ""

            print()
            name_color = Color.BRIGHT_GREEN if is_current else Color.WHITE
            print(colorize(f"  {player.name}", name_color, Color.BOLD) + marker)
            print(colorize("  " + Box.line(38), Color.DIM))

            # Stable with progress bar
            unicorns = player.unicorn_count()
            target = state.unicorns_to_win
            print(f"    {progress_bar(unicorns, target, 20, 'Unicorns')}")

            for card in player.stable:
                card_str = colorize_card(card.name, card.card_type.name)
                print(f"      {symbol('bullet')} {card_str}")

            # Upgrades
            if player.upgrades:
                print(f"    {success('Upgrades:')}")
                for card in player.upgrades:
                    print(f"      {colorize('+', Color.BRIGHT_GREEN)} {card.name}")

            # Downgrades
            if player.downgrades:
                print(f"    {error('Downgrades:')}")
                for card in player.downgrades:
                    print(f"      {colorize('-', Color.BRIGHT_RED)} {card.name}")

            # Hand
            hand_color = Color.BRIGHT_WHITE if player.hand_visible else Color.DIM
            print(f"    Hand: {colorize(f'{len(player.hand)} cards', hand_color)}")
            if player.hand_visible:
                for card in player.hand:
                    card_str = colorize_card(card.name, card.card_type.name)
                    print(f"      {symbol('bullet')} {card_str}")

        print()
        print(colorize(Box.line(60), Color.DIM))

    @staticmethod
    def show_player_view(state: 'GameState', player_idx: int) -> None:
        """Display the game from a specific player's perspective."""
        player = state.players[player_idx]

        print_header(f"YOUR TURN - {player.name}", 50)
        print(f"  Turn {colorize(str(state.turn_number), Color.BRIGHT_WHITE)} | "
              f"Phase: {colorize(state.phase.name, Color.BRIGHT_YELLOW)}")

        # Your stable with progress
        print()
        print_subheader("YOUR STABLE", 50)
        print(f"  {progress_bar(player.unicorn_count(), state.unicorns_to_win, 25, 'Progress')}")

        if player.stable:
            for card in player.stable:
                card_str = colorize_card(card.name, card.card_type.name)
                effect = ""
                if card.description:
                    short_desc = card.description[:45] + "..." if len(card.description) > 45 else card.description
                    effect = dim(f" - {short_desc}")
                print(f"    {symbol('unicorn', '*')} {card_str}{effect}")
        else:
            print(dim("    (no unicorns yet)"))

        # Your upgrades/downgrades
        if player.upgrades:
            print()
            print(success("  UPGRADES:"))
            for card in player.upgrades:
                print(f"    {colorize('+', Color.BRIGHT_GREEN)} {colorize_card(card.name, 'UPGRADE')}")

        if player.downgrades:
            print()
            print(error("  DOWNGRADES:"))
            for card in player.downgrades:
                print(f"    {colorize('-', Color.BRIGHT_RED)} {colorize_card(card.name, 'DOWNGRADE')}")

        # Other players' stables (public info)
        print()
        print_subheader("OPPONENTS", 50)
        for other in state.players:
            if other.player_idx != player_idx:
                unicorn_str = colorize(str(other.unicorn_count()), Color.BRIGHT_MAGENTA)
                extras = []
                if other.upgrades:
                    extras.append(success(f"{len(other.upgrades)} upgrades"))
                if other.downgrades:
                    extras.append(error(f"{len(other.downgrades)} downgrades"))
                extra_str = ", ".join(extras)
                if extra_str:
                    extra_str = f" ({extra_str})"
                print(f"    {other.name}: {unicorn_str} unicorns{extra_str}")

        # Your hand
        print()
        print_subheader(f"YOUR HAND ({len(player.hand)} cards)", 50)
        for i, card in enumerate(player.hand):
            card_type = card.card_type.name.replace("_", " ").title()
            type_color = {
                "Magical Unicorn": Color.BRIGHT_MAGENTA,
                "Basic Unicorn": Color.WHITE,
                "Baby Unicorn": Color.BRIGHT_WHITE,
                "Upgrade": Color.BRIGHT_GREEN,
                "Downgrade": Color.BRIGHT_RED,
                "Magic": Color.BRIGHT_BLUE,
                "Instant": Color.BRIGHT_YELLOW,
            }.get(card_type, Color.WHITE)

            num = colorize(f"{i + 1}.", Color.BRIGHT_WHITE)
            type_str = colorize(f"[{card_type}]", type_color)
            name_str = colorize(card.name, Color.BOLD)
            print(f"    {num} {type_str} {name_str}")

            if card.description:
                desc = card.description
                if len(desc) > 55:
                    desc = desc[:52] + "..."
                print(f"       {dim(desc)}")

        print()
        print(colorize(Box.line(50), Color.DIM))

    @staticmethod
    def show_card(card: 'CardInstance') -> None:
        """Display detailed information about a card."""
        card_type = card.card_type.name.replace("_", " ").title()

        print()
        print(colorize(Box.box_top(45), Color.BRIGHT_CYAN))

        name_centered = card.name.center(43)
        print(colorize(Box.VERTICAL, Color.BRIGHT_CYAN) +
              colorize(name_centered, Color.BOLD) +
              colorize(Box.VERTICAL, Color.BRIGHT_CYAN))

        type_centered = f"[{card_type}]".center(43)
        type_color = {
            "Magical Unicorn": Color.BRIGHT_MAGENTA,
            "Basic Unicorn": Color.WHITE,
            "Upgrade": Color.BRIGHT_GREEN,
            "Downgrade": Color.BRIGHT_RED,
            "Magic": Color.BRIGHT_BLUE,
            "Instant": Color.BRIGHT_YELLOW,
        }.get(card_type, Color.WHITE)
        print(colorize(Box.VERTICAL, Color.BRIGHT_CYAN) +
              colorize(type_centered, type_color) +
              colorize(Box.VERTICAL, Color.BRIGHT_CYAN))

        if card.description:
            # Word wrap description
            words = card.description.split()
            lines = []
            current_line = []
            current_len = 0
            for word in words:
                if current_len + len(word) + 1 <= 41:
                    current_line.append(word)
                    current_len += len(word) + 1
                else:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_len = len(word)
            if current_line:
                lines.append(" ".join(current_line))

            print(colorize(Box.VERTICAL + " " * 43 + Box.VERTICAL, Color.BRIGHT_CYAN))
            for line in lines:
                padded = f" {line}".ljust(43)
                print(colorize(Box.VERTICAL, Color.BRIGHT_CYAN) +
                      dim(padded) +
                      colorize(Box.VERTICAL, Color.BRIGHT_CYAN))

        print(colorize(Box.box_bottom(45), Color.BRIGHT_CYAN))

    @staticmethod
    def show_hand(state: 'GameState', player_idx: int) -> None:
        """Display a player's hand."""
        player = state.players[player_idx]

        print()
        print(bold(f"{player.name}'s Hand:"))
        for i, card in enumerate(player.hand):
            card_str = colorize_card(card.name, card.card_type.name)
            print(f"  {i + 1}. {card_str}")

    @staticmethod
    def show_stable(state: 'GameState', player_idx: int) -> None:
        """Display a player's stable."""
        player = state.players[player_idx]

        print()
        print(bold(f"{player.name}'s Stable") +
              dim(f" ({player.unicorn_count()}/{state.unicorns_to_win} unicorns)"))

        if player.stable:
            print(info("  Unicorns:"))
            for card in player.stable:
                card_str = colorize_card(card.name, card.card_type.name)
                print(f"    {symbol('unicorn', '*')} {card_str}")

        if player.upgrades:
            print(success("  Upgrades:"))
            for card in player.upgrades:
                print(f"    {colorize('+', Color.BRIGHT_GREEN)} {card.name}")

        if player.downgrades:
            print(error("  Downgrades:"))
            for card in player.downgrades:
                print(f"    {colorize('-', Color.BRIGHT_RED)} {card.name}")

    @staticmethod
    def show_action_result(action_desc: str) -> None:
        """Display the result of an action."""
        print(f"  {colorize('▶', Color.BRIGHT_GREEN)} {action_desc}")

    @staticmethod
    def show_neigh_opportunity(card_name: str, player_name: str) -> None:
        """Display a Neigh opportunity."""
        print()
        print(colorize(f"  ⚡ {player_name} is trying to play ", Color.BRIGHT_YELLOW) +
              colorize(card_name, Color.BOLD, Color.BRIGHT_WHITE) +
              colorize(" ⚡", Color.BRIGHT_YELLOW))
        print(dim("     (Other players may Neigh)"))

    @staticmethod
    def show_winner(state: 'GameState') -> None:
        """Display the game winner."""
        if state.winner is not None:
            winner = state.players[state.winner]

            print()
            print_header("GAME OVER!", 60)
            print()
            print(f"  {symbol('star')} " +
                  colorize("WINNER: ", Color.BRIGHT_YELLOW) +
                  colorize(winner.name, Color.BOLD, Color.BRIGHT_GREEN) +
                  f" {symbol('star')}")
            print(f"     with {colorize(str(winner.unicorn_count()), Color.BRIGHT_MAGENTA)} unicorns!")
            print()

            print(info("  Final Standings:"))
            sorted_players = sorted(
                state.players,
                key=lambda p: p.unicorn_count(),
                reverse=True
            )
            medals = ["🥇", "🥈", "🥉"]
            for i, player in enumerate(sorted_players):
                medal = medals[i] if i < 3 else f" {i + 1}."
                player_color = Color.BRIGHT_GREEN if player == winner else Color.WHITE
                print(f"    {medal} {colorize(player.name, player_color)}: "
                      f"{player.unicorn_count()} unicorns")

            print()
            print(colorize(Box.line(60), Color.DIM))

    @staticmethod
    def show_action_menu(actions: list, prompt: str = "Choose an action:") -> None:
        """Display an action selection menu."""
        print()
        print(bold(prompt))
        for i, action in enumerate(actions):
            num = colorize(f"{i + 1}.", Color.BRIGHT_WHITE)
            print(f"  {num} {action}")
        print()
