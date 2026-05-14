"""Welcome / mode selection screen."""

import importlib.metadata

from pyfiglet import Figlet

from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Static, Button
from textual.containers import Vertical, Center, Horizontal


VERSION = importlib.metadata.version("rsmetacheck")
TITLE_ART = Figlet(font="standard", width=80).renderText("RSMetaCheck")


class WelcomeScreen(Screen):
    """Welcome screen with mode selection."""

    CSS = """
    WelcomeScreen {
        align: center middle;
    }

    #welcome-title {
        color: blue;
        content-align: center middle;
        padding: 1 2 0 2;
    }

    #welcome-subtitle {
        content-align: center middle;
        color: gray;
        padding: 0 2 3 2;
    }

    #version-bar {
        dock: bottom;
        height: 1;
        padding: 0 1;
        align-horizontal: right;
    }

    #version-text {
        color: gray;
        width: auto;
    }

    Center Button {
        width: 34;
        margin: 1 0;
        padding: 0 1;
        border: none;
        background: transparent;
        color: white;
        text-style: bold;
    }

    Center Button:focus {
        color: black;
        background: blue;
    }

    Center Button:hover {
        color: black;
        background: blue;
    }

    #btn-quit {
        color: gray;
    }

    #btn-quit:focus {
        color: black;
        background: gray;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static(TITLE_ART, id="welcome-title")
        yield Static("detect metadata pitfalls in software repositories", id="welcome-subtitle")
        with Vertical():
            with Center():
                yield Button("Run SoMEF + Analyze", id="btn-full", disabled=True)
            with Center():
                yield Button("Skip SoMEF (existing outputs)", id="btn-skip", disabled=True)
            with Center():
                yield Button("Quit", id="btn-quit")
        with Horizontal(id="version-bar"):
            yield Static(f"RSMetaCheck v{VERSION}", id="version-text")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-quit":
            self.app.exit()
