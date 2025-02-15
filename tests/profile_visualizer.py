"""Visualization tools for profiling data."""

import os
import json
import pstats
from datetime import datetime
from typing import Dict, List, Any

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

class ProfileVisualizer:
    def __init__(self, profile_dir: str = "tests/profiling"):
        """Initialize profile visualizer."""
        self.profile_dir = profile_dir
        self.output_dir = os.path.join(profile_dir, "visualizations")
        os.makedirs(self.output_dir, exist_ok=True)

    def load_profile_data(self) -> Dict[str, Any]:
        """Load all profiling data from directory."""
        data = {
            "timings": [],
            "memory": [],
            "function_stats": []
        }
        
        # Load timing data from reports
        for filename in os.listdir(self.profile_dir):
            if filename.endswith('.md') and filename.startswith('report_'):
                with open(os.path.join(self.profile_dir, filename), 'r') as f:
                    content = f.read()
                    # Parse markdown table
                    for line in content.split('\n'):
                        if '|' in line and 'Operation' not in line and '---' not in line:
                            parts = [p.strip() for p in line.split('|') if p.strip()]
                            if len(parts) >= 3:
                                data["timings"].append({
                                    "operation": parts[0],
                                    "duration": float(parts[1]),
                                    "memory_delta": float(parts[2])
                                })
        
        # Load memory profiling data
        for filename in os.listdir(self.profile_dir):
            if filename.endswith('.txt') and 'memory' in filename:
                with open(os.path.join(self.profile_dir, filename), 'r') as f:
                    lines = f.readlines()
                    current_func = None
                    for line in lines:
                        if 'Line #' not in line and 'Mem usage' not in line:
                            parts = line.split()
                            if len(parts) >= 2:
                                try:
                                    mem = float(parts[3])
                                    inc = float(parts[4])
                                    data["memory"].append({
                                        "function": current_func or "unknown",
                                        "line": parts[0],
                                        "memory": mem,
                                        "increment": inc
                                    })
                                except (ValueError, IndexError):
                                    if len(parts) > 0:
                                        current_func = parts[0]

        # Load function profiling data
        for filename in os.listdir(self.profile_dir):
            if filename.endswith('.prof'):
                stats = pstats.Stats(os.path.join(self.profile_dir, filename))
                for func, (cc, nc, tt, ct, callers) in stats.stats.items():
                    data["function_stats"].append({
                        "function": f"{func[2]}:{func[0]}",
                        "calls": cc,
                        "time": ct,
                        "time_per_call": ct/cc if cc > 0 else 0
                    })
        
        return data

    def create_timing_visualization(self, data: Dict[str, Any]) -> None:
        """Create timing visualization."""
        df = pd.DataFrame(data["timings"])
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Operation Duration", "Memory Usage")
        )
        
        # Duration bar chart
        fig.add_trace(
            go.Bar(
                x=df["operation"],
                y=df["duration"],
                name="Duration (s)"
            ),
            row=1, col=1
        )
        
        # Memory delta bar chart
        fig.add_trace(
            go.Bar(
                x=df["operation"],
                y=df["memory_delta"],
                name="Memory Δ (MB)"
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=800,
            title_text="Operation Performance Profile",
            showlegend=True
        )
        
        fig.write_html(os.path.join(self.output_dir, "timing_profile.html"))

    def create_memory_visualization(self, data: Dict[str, Any]) -> None:
        """Create memory usage visualization."""
        df = pd.DataFrame(data["memory"])
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Memory Usage Over Time", "Memory Increments"),
            specs=[[{"type": "scatter"}], [{"type": "bar"}]]
        )
        
        # Memory usage line
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=df["memory"],
                name="Memory (MB)",
                mode="lines+markers"
            ),
            row=1, col=1
        )
        
        # Memory increments
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df["increment"],
                name="Memory Increment (MB)"
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=1000,
            title_text="Memory Usage Profile"
        )
        
        fig.write_html(os.path.join(self.output_dir, "memory_profile.html"))

    def create_function_visualization(self, data: Dict[str, Any]) -> None:
        """Create function profiling visualization."""
        df = pd.DataFrame(data["function_stats"])
        df = df.sort_values("time", ascending=False).head(20)  # Top 20 functions
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Total Time per Function", "Time per Call"),
            specs=[[{"type": "bar"}], [{"type": "bar"}]]
        )
        
        # Total time
        fig.add_trace(
            go.Bar(
                x=df["function"],
                y=df["time"],
                name="Total Time (s)"
            ),
            row=1, col=1
        )
        
        # Time per call
        fig.add_trace(
            go.Bar(
                x=df["function"],
                y=df["time_per_call"],
                name="Time per Call (s)"
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=1000,
            title_text="Function Performance Profile",
            xaxis_tickangle=45,
            xaxis2_tickangle=45
        )
        
        fig.write_html(os.path.join(self.output_dir, "function_profile.html"))

    def create_sunburst_visualization(self, data: Dict[str, Any]) -> None:
        """Create sunburst visualization of function calls."""
        df = pd.DataFrame(data["function_stats"])
        
        # Create hierarchy: module > function > metric
        fig = px.sunburst(
            df,
            path=['function'],
            values='calls',
            color='time_per_call',
            color_continuous_scale='RdYlBu_r'
        )
        
        fig.update_layout(
            title_text="Function Call Hierarchy"
        )
        
        fig.write_html(os.path.join(self.output_dir, "call_hierarchy.html"))

    def generate_visualization_report(self) -> str:
        """Generate complete visualization report."""
        data = self.load_profile_data()
        
        self.create_timing_visualization(data)
        self.create_memory_visualization(data)
        self.create_function_visualization(data)
        self.create_sunburst_visualization(data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.output_dir, f"visualization_report_{timestamp}.html")
        
        # Create HTML report combining all visualizations
        html_content = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Profile Visualization Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "iframe { width: 100%; height: 800px; border: none; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>Profile Visualization Report</h1>",
            f"<p>Generated: {datetime.now().isoformat()}</p>",
            "<h2>Operation Performance</h2>",
            '<iframe src="timing_profile.html"></iframe>',
            "<h2>Memory Usage</h2>",
            '<iframe src="memory_profile.html"></iframe>',
            "<h2>Function Performance</h2>",
            '<iframe src="function_profile.html"></iframe>',
            "<h2>Call Hierarchy</h2>",
            '<iframe src="call_hierarchy.html"></iframe>',
            "</body>",
            "</html>"
        ]
        
        with open(report_file, 'w') as f:
            f.write("\n".join(html_content))
        
        return report_file

def main():
    """Generate profile visualizations."""
    try:
        visualizer = ProfileVisualizer()
        report_file = visualizer.generate_visualization_report()
        print(f"Visualization report generated: {report_file}")
    except Exception as e:
        print(f"Error generating visualizations: {e}")

if __name__ == "__main__":
    main()
