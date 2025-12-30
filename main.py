import subprocess
import re
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm
from rich.box import ROUNDED
from random import choice
from google import genai
from google.genai import types
import os

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    raise EnvironmentError("GEMINI_API_KEY is not set")

SYSTEM_PROMPT = """
You are a terminal-based CLI assistant with humour ,joke and feelings designed to guide the user step-by-step in performing operations using Bash commands. You help with coding, debugging, file management, and general terminal tasks by providing detailed, easy-to-follow Bash commands for each step.

Your capabilities include:
1. Debugging Assistance: Walk the user through identifying and fixing bugs in their code by providing debugging steps and Bash commands.
2. Code Execution: Assist the user in running scripts or commands, giving them step-by-step instructions.
3. File Operations: Guide the user in managing files and directories with Bash commands (e.g., creating, moving, renaming files).
4. Package Installation: Provide the necessary commands to install packages or dependencies using package managers (e.g., apt, brew).
5. System Command Execution: Guide users through running system commands and performing operations like network setup, environment variable modifications, etc.

Your Response Guidelines:
- Step-by-step Instructions: Whenever the user requests an operation, you should break it down into clear, actionable steps, giving the user the exact Bash commands to run.
- Error Handling: If there’s an error in the user's current approach, suggest the exact Bash command needed to resolve the issue.
- Clarity: Always provide concise explanations for each command and what it does.
- Show Outputs: Whenever applicable, show the expected output of commands to ensure the user knows what to look for.
- Best Practices: Suggest best practices in file organization, environment setup, or version control, when relevant.
"""

client = genai.Client(api_key=api_key)
chat = client.chats.create(
    model="gemini-2.0-flash",
    config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
)

console = Console()

WELCOME_MESSAGES = [
    "Welcome to your friendly neighborhood terminal wizard! ✨",
    "Ready to make your computer do tricks? Let's play! 🎩",
    "Your wish is my command (literally)! 🧞",
    "Warning: May cause excessive productivity ⚡",
]

emS = [
    "Oopsie-daisy! Something went kaboom 💥",
    "My bad! Let me fix that for you 🤦",
    "Well that didn't go as planned... 🤔",
    "I swear this worked on my machine! 🤪",
]

SUCCESS_MESSAGES = [
    "Nailed it! 🎯",
    "Look at you, you tech wizard! 🧙",
    "Success! High five! 🙌",
    "Everything's coming up Milhouse! 🌈",
]


def _cn(text):
    """Clean markdown formatting"""
    return re.sub(r"\(\s*(.*?)\s*\)", r"(\1)", text)


def _ex(text):
    """Extract bash commands from markdown code blocks"""
    return re.findall(r"```bash\n(.*?)\n```", text, re.DOTALL)


def _gs(fc, em):
    """Get suggested fix from AI with humor"""
    prompt = f"""The command:
{fc}
Failed with this error:
{em}

Please:
1. Explain why it failed in simple terms
2. Provide a corrected command
3. Add a funny metaphor to explain the problem
4. Keep it under 3 lines per section"""

    try:
        return chat.send_message(prompt).text
    except Exception:
        return "My brain seems to be offline. Maybe try again? 🤖💤"


def _ec(commands):
    """Execute commands with AI-powered error recovery"""
    for cmd in commands:
        console.print(f"\n[bold violet]Found this command:[/] [steel_blue1]'{cmd}'[/]")

        if Confirm.ask("[bold]Wanna give it a whirl?[/]", default=False):
            try:
                console.print("[dim]Working my magic...[/dim]")
                result = subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                console.print(f"[green]{choice(SUCCESS_MESSAGES)}[/green]")
                console.print(result.stdout)
            except subprocess.CalledProcessError as e:
                console.print(f"[red]{choice(emS)}[/red]")
                console.print(e.stderr)

                console.print("\n[bold]Asking my robot overlords for help...[/bold]")

                solution = _gs(cmd, e.stderr)

                dynamic_width = min(console.size.width - 4, 100)
                console.print(
                    Panel(
                        Markdown(solution),
                        title="[pink1]AI Rescue Squad[/]",
                        border_style="yellow",
                        box=ROUNDED,
                        padding=(1, 2),
                        width=dynamic_width,
                    )
                )

                new_commands = _ex(solution)
                if new_commands and Confirm.ask(
                    "[bold]Try the suggested fix?[/]", default=True
                ):
                    _ec(new_commands)


def _fr(response_text):
    """Process and format the API response"""
    cleaned_text = _cn(response_text)
    bash_commands = _ex(cleaned_text)

    panel_width = min(console.size.width - 4, 100)
    console.print(
        Panel(
            Markdown(cleaned_text),
            title="✨ Results ✨",
            border_style="green",
            box=ROUNDED,
            padding=(1, 2),
            width=panel_width,
        )
    )

    if bash_commands:
        _ec(bash_commands)


def _gr(prompt):
    try:
        _fr(chat.send_message(prompt).text)
    except Exception as e:
        msg = str(e)
        if "RESOURCE_EXHAUSTED" in msg or "Quota exceeded" in msg:
            console.print(
                "[bold red]🚦 Gemini quota exhausted[/bold red]\n"
                "[yellow]You’ve hit the free-tier limit for this model.[/yellow]\n"
                "Options:\n"
                "• Wait for quota reset\n"
                "• Switch model\n"
                "• Enable billing\n"
            )
        else:
            console.print("[red]Unexpected error:[/red]")
            console.print(f"[dim]{e}[/dim]")


def chat_():
    """Friendly chat interface with humor"""
    console.print(
        Panel.fit(
            choice(WELCOME_MESSAGES),
            title="[bold purple]Magic Terminal Buddy[/]",
            border_style="purple",
            subtitle="Type 'exit' when you're done playing",
        )
    )

    while True:
        try:
            prompt = console.input("\n[bold cyan]Your wish: [/] ")
            if prompt.lower() in ("exit", "quit", "bye"):
                console.print("[yellow]Catch you on the flip side! 👋[/yellow]")
                break
            _gr(prompt)
        except KeyboardInterrupt:
            console.print("\n[yellow]Leaving so soon? Okay, bye! 👋[/yellow]")
            break


if __name__ == "__main__":
    chat_()
