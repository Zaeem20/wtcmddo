"""Terminal UI rendering with rich."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from .config import get_config, save_config
from .explainer import Explanation

console = Console()
_error_console = Console(stderr=True)

# Each risk level maps to a rich style used for the panel border and label.
RISK_STYLES = {
    "LOW": "bold green",
    "MEDIUM": "bold yellow",
    "HIGH": "bold red",
    "CRITICAL": "bold magenta",
}


def _risk_style(risk: str) -> str:
    """Return the rich style for a risk level."""
    return RISK_STYLES.get(risk, "bold white")


def _ask(
    prompt: str,
    *,
    password: bool = False,
    default: str | None = None,
) -> str:
    """Prompt for text input, exiting cleanly on EOF or interrupt."""
    try:
        return Prompt.ask(prompt, password=password, default=default)
    except (EOFError, KeyboardInterrupt):
        raise SystemExit(1)


def _confirm(prompt: str, *, default: bool = False) -> bool:
    """Yes/no prompt, returning *default* on EOF or interrupt."""
    try:
        return Confirm.ask(prompt, default=default)
    except (EOFError, KeyboardInterrupt):
        return default


def analyzing(command: str):
    """Context manager that shows a spinner while the API analyzes a command."""
    return console.status(
        f"[cyan]Analyzing[/cyan] [bold]{command}[/bold] ...",
        spinner="dots",
    )


def display_explanation(command: str, result: Explanation) -> None:
    """Render the explanation inside a risk-colored panel."""
    style = _risk_style(result.risk)
    lines = [
        f"[white]{result.explanation}[/white]",
        "",
        f"[dim]Risk   [/dim][{style}]{result.risk}[/]",
        f"[dim]Reason [/dim][white]{result.reason}[/white]",
    ]
    if result.category:
        lines.append(f"[dim]Type   [/dim][cyan]{result.category}[/cyan]")
    body = "\n".join(lines)
    console.print(
        Panel(
            body,
            title=f"[bold]$ {command}[/bold]",
            title_align="left",
            border_style=style,
            expand=False,
            padding=(1, 2),
        )
    )
    console.print()


def confirm_execution() -> bool:
    """Ask the user whether to execute the command."""
    return _confirm("Execute this command", default=False)


def display_aborted() -> None:
    """Show the aborted message."""
    console.print("[yellow]Aborted.[/yellow]")


def echo_command(command: str) -> None:
    """Print the command about to be executed."""
    console.print()
    console.print(f"[bold green]$[/bold green] {command}")
    console.print()


def display_error(message: str) -> None:
    """Print an error message to stderr."""
    _error_console.print(f"[bold red]Error:[/bold red] {message}")


def run_setup() -> None:
    """Interactive setup wizard using rich prompts."""
    console.rule("[bold cyan] wtcmddo Setup [/bold cyan]")
    console.print()

    config = get_config()
    has_key = config["api_key"] != "(not set)"

    if has_key:
        console.print("[dim]An API key is already configured.[/dim]")
        api_key = _ask("OpenRouter API key (Enter to keep current)", password=True)
        if not api_key:
            api_key = config["api_key"]
    else:
        api_key = _ask("OpenRouter API key", password=True)
        if not api_key:
            console.print("[red]No API key provided. Setup cancelled.[/red]")
            return

    base_url = _ask("API base URL", default=config["base_url"])
    model = _ask("Model name", default=config["model"])

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[dim]API key[/dim]", "[green]configured[/green]")
    table.add_row("[dim]Base URL[/dim]", base_url)
    table.add_row("[dim]Model[/dim]", model)

    console.print()
    console.print(
        Panel(
            table,
            title="Configuration Summary",
            border_style="cyan",
            expand=False,
        )
    )

    if _confirm("Save this configuration?", default=True):
        save_config(api_key, base_url, model)
        console.print("[green]Configuration saved to ~/.wtcmddo/config.json[/green]")
    else:
        console.print("[yellow]Configuration not saved.[/yellow]")
