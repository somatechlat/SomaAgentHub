"""
Sample Application: Code Assistant

An AI-powered coding assistant that helps with code review, debugging,
and optimization.
"""

import os
import asyncio
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from somaagent import AsyncSomaAgentClient


console = Console()


class CodeAssistant:
    """AI code assistant."""
    
    def __init__(self, api_key: str):
        """Initialize code assistant."""
        self.api_key = api_key
        self.client = None
        self.conversation_id = None
    
    async def start(self):
        """Start the code assistant."""
        async with AsyncSomaAgentClient(api_key=self.api_key) as client:
            self.client = client
            
            # Create specialized agent
            agent = await client.create_agent(
                name="Code Assistant",
                instructions="""
                You are an expert software engineer. You help with:
                - Code review and best practices
                - Debugging and error analysis
                - Performance optimization
                - Security vulnerability detection
                - Documentation and testing
                
                Always provide clear, actionable advice with code examples.
                """,
                model="gpt-4",
                tools=[]
            )
            
            self.agent_id = agent.id
            
            # Display welcome
            self._display_welcome()
            
            # Main loop
            while True:
                console.print("\n[bold cyan]Choose an action:[/bold cyan]")
                console.print("1. Review code file")
                console.print("2. Debug code snippet")
                console.print("3. Optimize performance")
                console.print("4. Ask a question")
                console.print("5. Exit")
                
                choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "5"])
                
                if choice == "1":
                    await self._review_file()
                elif choice == "2":
                    await self._debug_code()
                elif choice == "3":
                    await self._optimize_code()
                elif choice == "4":
                    await self._ask_question()
                elif choice == "5":
                    console.print("\n[yellow]Goodbye! 👋[/yellow]")
                    break
    
    def _display_welcome(self):
        """Display welcome message."""
        console.print(Panel.fit(
            "[bold blue]👨‍💻 SomaAgent Code Assistant[/bold blue]\n\n"
            "I can help you with code review, debugging, and optimization.\n",
            border_style="blue"
        ))
    
    async def _review_file(self):
        """Review a code file."""
        file_path = Prompt.ask("\n[cyan]Enter file path[/cyan]")
        
        if not Path(file_path).exists():
            console.print("[red]File not found![/red]")
            return
        
        # Read file
        with open(file_path, 'r') as f:
            code = f.read()
        
        # Display code
        language = Path(file_path).suffix[1:]  # Remove dot
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title=file_path))
        
        # Get review
        console.print("\n[cyan]Analyzing code...[/cyan]")
        
        prompt = f"""
        Please review this {language} code and provide:
        1. Code quality assessment
        2. Potential bugs or issues
        3. Best practices violations
        4. Suggestions for improvement
        
        ```{language}
        {code}
        ```
        """
        
        result = await self.client.run_agent(self.agent_id, prompt)
        
        console.print(Panel(
            result.get("output", ""),
            title="Code Review",
            border_style="green"
        ))
    
    async def _debug_code(self):
        """Debug code snippet."""
        console.print("\n[cyan]Paste your code (press Enter twice to finish):[/cyan]")
        
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        
        code = "\n".join(lines)
        
        if not code.strip():
            console.print("[red]No code provided![/red]")
            return
        
        error_msg = Prompt.ask("\n[cyan]What error are you seeing? (optional)[/cyan]", default="")
        
        prompt = f"""
        Help me debug this code:
        
        ```
        {code}
        ```
        
        Error message: {error_msg if error_msg else "No error message provided"}
        
        Please:
        1. Identify the problem
        2. Explain why it's happening
        3. Provide a fixed version
        """
        
        console.print("\n[cyan]Analyzing...[/cyan]")
        result = await self.client.run_agent(self.agent_id, prompt)
        
        console.print(Panel(
            result.get("output", ""),
            title="Debug Analysis",
            border_style="yellow"
        ))
    
    async def _optimize_code(self):
        """Optimize code for performance."""
        console.print("\n[cyan]Paste your code (press Enter twice to finish):[/cyan]")
        
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        
        code = "\n".join(lines)
        
        if not code.strip():
            console.print("[red]No code provided![/red]")
            return
        
        prompt = f"""
        Optimize this code for better performance:
        
        ```
        {code}
        ```
        
        Please:
        1. Identify performance bottlenecks
        2. Suggest optimizations
        3. Provide optimized version
        4. Explain the improvements
        """
        
        console.print("\n[cyan]Optimizing...[/cyan]")
        result = await self.client.run_agent(self.agent_id, prompt)
        
        console.print(Panel(
            result.get("output", ""),
            title="Optimization Suggestions",
            border_style="green"
        ))
    
    async def _ask_question(self):
        """Ask a coding question."""
        question = Prompt.ask("\n[cyan]What's your question?[/cyan]")
        
        console.print("\n[cyan]Thinking...[/cyan]")
        result = await self.client.run_agent(self.agent_id, question)
        
        console.print(Panel(
            result.get("output", ""),
            title="Answer",
            border_style="blue"
        ))


async def main():
    """Main entry point."""
    api_key = os.getenv("SOMAAGENT_API_KEY")
    
    if not api_key:
        console.print("[red]Error: SOMAAGENT_API_KEY not set[/red]")
        return
    
    assistant = CodeAssistant(api_key)
    await assistant.start()


if __name__ == "__main__":
    asyncio.run(main())
