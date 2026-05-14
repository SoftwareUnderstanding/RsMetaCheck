"""TUI entry: main Textual Application."""

from textual.app import App, ComposeResult
from textual.widgets import Header
from textual.binding import Binding

from rsmetacheck.tui.screens.welcome import WelcomeScreen


class RsMetaCheckTUI(App):
    """Main TUI application."""

    CSS = """
    Screen {
        align: center middle;
        border: solid white;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", key_display="Q"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

    def on_mount(self) -> None:
        self.push_screen(WelcomeScreen())


def launch_tui():
    """Entry point to launch the TUI."""
    app = RsMetaCheckTUI()
    app.run()
