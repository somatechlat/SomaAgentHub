"""
Sample Application: Data Analysis Agent

An AI-powered data analyst that helps with exploratory data analysis,
visualization suggestions, and statistical insights.
"""

import os
import asyncio
import pandas as pd
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt

from somaagent import AsyncSomaAgentClient


console = Console()


class DataAnalysisAgent:
    """AI data analysis agent."""
    
    def __init__(self, api_key: str):
        """Initialize data analysis agent."""
        self.api_key = api_key
        self.client = None
        self.agent_id = None
        self.dataframe = None
    
    async def start(self):
        """Start the data analysis agent."""
        async with AsyncSomaAgentClient(api_key=self.api_key) as client:
            self.client = client
            
            # Create specialized data analysis agent
            agent = await client.create_agent(
                name="Data Analyst",
                instructions="""
                You are an expert data analyst. You help with:
                - Exploratory data analysis (EDA)
                - Statistical analysis and insights
                - Data visualization recommendations
                - Data quality assessment
                - Feature engineering suggestions
                
                Always provide clear, actionable insights with examples.
                When suggesting visualizations, explain why they're appropriate.
                """,
                model="gpt-4",
                tools=[]
            )
            
            self.agent_id = agent.id
            
            # Display welcome
            self._display_welcome()
            
            # Main loop
            await self._main_loop()
    
    def _display_welcome(self):
        """Display welcome message."""
        console.print(Panel.fit(
            "[bold magenta]📊 SomaAgent Data Analysis Assistant[/bold magenta]\n\n"
            "I can help you analyze your data and generate insights.\n",
            border_style="magenta"
        ))
    
    async def _main_loop(self):
        """Main application loop."""
        while True:
            console.print("\n[bold cyan]Choose an action:[/bold cyan]")
            console.print("1. Load dataset")
            console.print("2. Show data summary")
            console.print("3. Analyze specific column")
            console.print("4. Get visualization suggestions")
            console.print("5. Ask data question")
            console.print("6. Exit")
            
            choice = Prompt.ask("Select", choices=["1", "2", "3", "4", "5", "6"])
            
            if choice == "1":
                await self._load_dataset()
            elif choice == "2":
                await self._show_summary()
            elif choice == "3":
                await self._analyze_column()
            elif choice == "4":
                await self._get_viz_suggestions()
            elif choice == "5":
                await self._ask_question()
            elif choice == "6":
                console.print("\n[yellow]Goodbye! 👋[/yellow]")
                break
    
    async def _load_dataset(self):
        """Load a dataset from file."""
        file_path = Prompt.ask("\n[cyan]Enter CSV file path[/cyan]")
        
        try:
            self.dataframe = pd.read_csv(file_path)
            
            console.print(f"\n[green]✓ Loaded dataset: {len(self.dataframe)} rows, {len(self.dataframe.columns)} columns[/green]")
            
            # Show preview
            table = Table(title="Data Preview (first 5 rows)")
            for col in self.dataframe.columns[:10]:  # Limit to 10 columns
                table.add_column(col, style="cyan")
            
            for _, row in self.dataframe.head().iterrows():
                table.add_row(*[str(val)[:50] for val in row.values[:10]])
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error loading dataset: {e}[/red]")
    
    async def _show_summary(self):
        """Show dataset summary and get AI analysis."""
        if self.dataframe is None:
            console.print("[yellow]Please load a dataset first![/yellow]")
            return
        
        # Generate summary
        summary_stats = self.dataframe.describe().to_string()
        data_types = self.dataframe.dtypes.to_string()
        missing_values = self.dataframe.isnull().sum().to_string()
        
        # Display summary
        console.print(Panel(
            f"[bold]Shape:[/bold] {self.dataframe.shape}\n\n"
            f"[bold]Data Types:[/bold]\n{data_types}\n\n"
            f"[bold]Missing Values:[/bold]\n{missing_values}",
            title="Dataset Summary"
        ))
        
        # Get AI insights
        console.print("\n[cyan]Generating insights...[/cyan]")
        
        prompt = f"""
        Analyze this dataset summary and provide:
        1. Initial observations about the data
        2. Potential data quality issues
        3. Interesting patterns or anomalies
        4. Recommendations for further analysis
        
        Dataset shape: {self.dataframe.shape}
        
        Summary statistics:
        {summary_stats}
        
        Data types:
        {data_types}
        
        Missing values:
        {missing_values}
        """
        
        result = await self.client.run_agent(self.agent_id, prompt)
        
        console.print(Panel(
            result.get("output", ""),
            title="AI Insights",
            border_style="green"
        ))
    
    async def _analyze_column(self):
        """Analyze a specific column."""
        if self.dataframe is None:
            console.print("[yellow]Please load a dataset first![/yellow]")
            return
        
        # Show available columns
        console.print("\n[cyan]Available columns:[/cyan]")
        for i, col in enumerate(self.dataframe.columns, 1):
            console.print(f"  {i}. {col} ({self.dataframe[col].dtype})")
        
        column = Prompt.ask("\n[cyan]Enter column name[/cyan]")
        
        if column not in self.dataframe.columns:
            console.print("[red]Column not found![/red]")
            return
        
        # Get column statistics
        col_data = self.dataframe[column]
        
        if pd.api.types.is_numeric_dtype(col_data):
            stats = {
                "count": col_data.count(),
                "mean": col_data.mean(),
                "std": col_data.std(),
                "min": col_data.min(),
                "25%": col_data.quantile(0.25),
                "50%": col_data.quantile(0.50),
                "75%": col_data.quantile(0.75),
                "max": col_data.max()
            }
            stats_str = "\n".join([f"{k}: {v}" for k, v in stats.items()])
        else:
            stats = {
                "count": col_data.count(),
                "unique": col_data.nunique(),
                "top": col_data.mode()[0] if len(col_data.mode()) > 0 else "N/A",
                "freq": col_data.value_counts().iloc[0] if len(col_data) > 0 else 0
            }
            stats_str = "\n".join([f"{k}: {v}" for k, v in stats.items()])
        
        # Display stats
        console.print(Panel(stats_str, title=f"Column: {column}"))
        
        # Get AI analysis
        console.print("\n[cyan]Analyzing column...[/cyan]")
        
        prompt = f"""
        Analyze this data column and provide insights:
        
        Column name: {column}
        Data type: {col_data.dtype}
        Statistics:
        {stats_str}
        
        Sample values: {col_data.head(10).tolist()}
        
        Please provide:
        1. Distribution characteristics
        2. Potential outliers or anomalies
        3. Relationship insights
        4. Recommendations for use in analysis
        """
        
        result = await self.client.run_agent(self.agent_id, prompt)
        
        console.print(Panel(
            result.get("output", ""),
            title="Column Analysis",
            border_style="green"
        ))
    
    async def _get_viz_suggestions(self):
        """Get visualization suggestions."""
        if self.dataframe is None:
            console.print("[yellow]Please load a dataset first![/yellow]")
            return
        
        # Get dataset info
        column_types = {
            "numeric": [col for col in self.dataframe.columns if pd.api.types.is_numeric_dtype(self.dataframe[col])],
            "categorical": [col for col in self.dataframe.columns if pd.api.types.is_object_dtype(self.dataframe[col])],
            "datetime": [col for col in self.dataframe.columns if pd.api.types.is_datetime64_any_dtype(self.dataframe[col])]
        }
        
        prompt = f"""
        Based on this dataset structure, suggest appropriate visualizations:
        
        Dataset shape: {self.dataframe.shape}
        
        Numeric columns: {column_types['numeric']}
        Categorical columns: {column_types['categorical']}
        Datetime columns: {column_types['datetime']}
        
        Sample data:
        {self.dataframe.head(5).to_string()}
        
        Please suggest:
        1. Best visualizations for initial exploration
        2. Specific chart types for key insights
        3. Python code snippets (using matplotlib/seaborn)
        4. Explanations of why each visualization is useful
        """
        
        console.print("\n[cyan]Generating visualization suggestions...[/cyan]")
        result = await self.client.run_agent(self.agent_id, prompt)
        
        console.print(Panel(
            result.get("output", ""),
            title="Visualization Suggestions",
            border_style="magenta"
        ))
    
    async def _ask_question(self):
        """Ask a question about the data."""
        if self.dataframe is None:
            console.print("[yellow]Please load a dataset first![/yellow]")
            return
        
        question = Prompt.ask("\n[cyan]What would you like to know about the data?[/cyan]")
        
        # Include data context
        context = f"""
        Dataset shape: {self.dataframe.shape}
        Columns: {self.dataframe.columns.tolist()}
        
        Sample data:
        {self.dataframe.head(3).to_string()}
        
        Question: {question}
        """
        
        console.print("\n[cyan]Analyzing...[/cyan]")
        result = await self.client.run_agent(self.agent_id, context)
        
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
    
    agent = DataAnalysisAgent(api_key)
    await agent.start()


if __name__ == "__main__":
    asyncio.run(main())
