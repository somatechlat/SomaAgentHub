"""
Sample Application: AI Chatbot with SomaAgent

A production-ready chatbot with streaming responses, conversation history,
and beautiful terminal UI.
"""

import os
import asyncio
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.live import Live
from rich.table import Table
from rich.prompt import Prompt

from somaagent import AsyncSomaAgentClient


console = Console()


class ChatbotApp:
    """AI Chatbot application."""
    
    def __init__(self, api_key: str):
        """
        Initialize chatbot.
        
        Args:
            api_key: SomaAgent API key
        """
        self.api_key = api_key
        self.conversation_id = None
        self.client = None
    
    async def start(self):
        """Start the chatbot."""
        async with AsyncSomaAgentClient(api_key=self.api_key) as client:
            self.client = client
            
            # Create conversation
            conversation = await client.create_conversation(
                metadata={
                    "app": "chatbot-sample",
                    "started_at": datetime.utcnow().isoformat()
                }
            )
            self.conversation_id = conversation.id
            
            # Display welcome
            self._display_welcome()
            
            # Chat loop
            while True:
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")
                
                if user_input.lower() in ["exit", "quit", "bye"]:
                    console.print("\n[yellow]Goodbye! 👋[/yellow]")
                    break
                
                if user_input.lower() == "history":
                    await self._show_history()
                    continue
                
                if user_input.lower() == "clear":
                    console.clear()
                    self._display_welcome()
                    continue
                
                # Get response
                await self._get_response(user_input)
    
    def _display_welcome(self):
        """Display welcome message."""
        console.print(Panel.fit(
            "[bold green]🤖 SomaAgent Chatbot[/bold green]\n\n"
            "I'm here to help! Ask me anything.\n\n"
            "[dim]Commands: 'history', 'clear', 'exit'[/dim]",
            border_style="green"
        ))
    
    async def _get_response(self, message: str):
        """
        Get streaming response from assistant.
        
        Args:
            message: User message
        """
        console.print("\n[bold green]Assistant:[/bold green]", end=" ")
        
        # Collect response chunks
        response_text = ""
        
        try:
            async for chunk in self.client.stream_completion(
                self.conversation_id,
                message
            ):
                response_text += chunk
                console.print(chunk, end="", style="white")
            
            console.print()  # New line after response
            
        except Exception as e:
            console.print(f"\n[red]Error: {e}[/red]")
    
    async def _show_history(self):
        """Show conversation history."""
        try:
            conversation = await self.client.get_conversation(self.conversation_id)
            
            # Create table
            table = Table(title="Conversation History")
            table.add_column("Time", style="cyan")
            table.add_column("Role", style="magenta")
            table.add_column("Message", style="white")
            
            for msg in conversation.messages:
                timestamp = msg.created_at.strftime("%H:%M:%S")
                role = "You" if msg.role == "user" else "Assistant"
                content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                
                table.add_row(timestamp, role, content)
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error loading history: {e}[/red]")


async def main():
    """Main entry point."""
    # Get API key from environment
    api_key = os.getenv("SOMAAGENT_API_KEY")
    
    if not api_key:
        console.print("[red]Error: SOMAAGENT_API_KEY not set[/red]")
        console.print("Set your API key:")
        console.print("  export SOMAAGENT_API_KEY='your-key-here'")
        return
    
    # Start chatbot
    app = ChatbotApp(api_key)
    await app.start()


if __name__ == "__main__":
    asyncio.run(main())
