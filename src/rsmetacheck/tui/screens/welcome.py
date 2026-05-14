"""Welcome / mode selection screen."""

import importlib.metadata

from pyfiglet import Figlet

from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Static, Button
from textual.containers import Vertical, Center, Horizontal


VERSION = importlib.metadata.version("rsmetacheck")
TITLE_ART = Figlet(font="standard", width=80).renderText("RSMetaCheck")


def _color_text(words: list[str], first_color: str = "#EF2818", rest_color: str = "#3974B4") -> str:
    """Color the first letter of each word in first_color, the rest in rest_color."""
    parts = []
    for w in words:
        parts.append(f"[{first_color}]{w[0]}[/][{rest_color}]{w[1:]}[/]")
    return "\n".join(parts)


PROVIDER_TEXT = _color_text(["Ontology", "Engineering", "Group"])


class WelcomeScreen(Screen):
    """Welcome screen with mode selection."""

    CSS = """
    WelcomeScreen {
        align: center middle;
    }

    #welcome-title {
        color: #3974B4;
        content-align: center middle;
        padding: 1 2 0 2;
    }

    #welcome-subtitle {
        content-align: center middle;
        color: gray;
        padding: 0 2 3 2;
    }

    #bottom {
        dock: bottom;
        height: auto;
    }

    #version-bar {
        height: 1;
        padding: 0 1;
        align-horizontal: right;
    }

    #version-text {
        color: gray;
    }

    #provided-by {
        height: auto;
        padding: 0 1;
    }

    #provided-by-label {
        color: white;
        padding: 0 0 1 0;
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
        background: #3974B4;
    }

    Center Button:hover {
        color: black;
        background: #3974B4;
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
        with Vertical(id="bottom"):
            with Vertical(id="provided-by"):
                yield Static("Provided by:", id="provided-by-label")
                yield Static(PROVIDER_TEXT, id="provided-by-art")
            with Horizontal(id="version-bar"):
                yield Static(f"[#7FD88F]\u25cf[/] RSMetaCheck v{VERSION}", id="version-text")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-quit":
            self.app.exit()
