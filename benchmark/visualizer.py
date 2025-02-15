"""Visualization tools for benchmark results."""

import json
import os
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from utils.log import log

class BenchmarkVisualizer:
    def __init__(self, results_dir="benchmark/results", output_dir="benchmark/visualizations"):
        """Initialize the visualizer."""
        self.results_dir = results_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def load_results_to_dataframe(self, filter_model=None, filter_scenario=None):
        """Load benchmark results into a pandas DataFrame."""
        results = []
        
        for filename in os.listdir(self.results_dir):
            if not filename.endswith('.json'):
                continue
            
            if filter_model and filter_model not in filename:
                continue
                
            if filter_scenario and filter_scenario not in filename:
                continue

            with open(os.path.join(self.results_dir, filename), 'r') as f:
                result = json.load(f)
                
                # Flatten metrics into columns
                flat_result = {
                    "model": result["model"],
                    "scenario": result["scenario"],
                    "timestamp": result["timestamp"],
                    "duration": result["duration"],
                    "iterations": result["iterations_completed"]
                }
                
                # Add metrics as columns
                for metric, value in result["metrics"].items():
                    if isinstance(value, (int, float)):
                        flat_result[f"metric_{metric}"] = value
                
                results.append(flat_result)
        
        return pd.DataFrame(results)

    def create_performance_heatmap(self, df):
        """Create a heatmap of model performance across scenarios."""
        metrics = [col for col in df.columns if col.startswith('metric_')]
        
        # Calculate average metrics per model/scenario
        pivot_data = {}
        for metric in metrics:
            pivot = df.pivot_table(
                values=metric,
                index='model',
                columns='scenario',
                aggfunc='mean'
            )
            pivot_data[metric] = pivot

        # Create subplots for each metric
        n_metrics = len(metrics)
        fig = make_subplots(
            rows=n_metrics, cols=1,
            subplot_titles=[m.replace('metric_', '') for m in metrics],
            vertical_spacing=0.1
        )

        for idx, (metric, pivot) in enumerate(pivot_data.items()):
            heatmap = go.Heatmap(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorscale='RdYlBu',
                name=metric.replace('metric_', '')
            )
            fig.add_trace(heatmap, row=idx+1, col=1)

        fig.update_layout(
            height=300 * n_metrics,
            title="Model Performance Heatmap",
            showlegend=False
        )

        return fig

    def create_metric_comparison(self, df, metric):
        """Create box plots comparing models for a specific metric."""
        fig = px.box(
            df,
            x="model",
            y=f"metric_{metric}",
            color="scenario",
            title=f"{metric} Comparison Across Models",
            points="all"
        )
        
        fig.update_layout(
            xaxis_title="Model",
            yaxis_title=metric
        )
        
        return fig

    def create_timeline_view(self, df):
        """Create a timeline view of performance trends."""
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        metrics = [col for col in df.columns if col.startswith('metric_')]
        
        fig = go.Figure()
        
        for metric in metrics:
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df[metric],
                name=metric.replace('metric_', ''),
                mode='lines+markers'
            ))
        
        fig.update_layout(
            title="Performance Metrics Over Time",
            xaxis_title="Timestamp",
            yaxis_title="Metric Value"
        )
        
        return fig

    def create_action_distribution(self, results):
        """Create a bar chart of action distributions."""
        action_counts = {}
        
        for result in results:
            for log in result.get("debug_logs", []):
                action_type = log.get("request_type", "unknown")
                action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        fig = go.Figure(data=[
            go.Bar(
                x=list(action_counts.keys()),
                y=list(action_counts.values())
            )
        ])
        
        fig.update_layout(
            title="Action Type Distribution",
            xaxis_title="Action Type",
            yaxis_title="Count"
        )
        
        return fig

    def generate_visualization_report(self, filter_model=None, filter_scenario=None):
        """Generate a complete visualization report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = f"{self.output_dir}/report_{timestamp}"
        os.makedirs(report_dir, exist_ok=True)

        # Load and process data
        df = self.load_results_to_dataframe(filter_model, filter_scenario)
        if df.empty:
            log("No data to visualize")
            return None

        # Create visualizations
        try:
            # Performance heatmap
            heatmap = self.create_performance_heatmap(df)
            heatmap.write_html(f"{report_dir}/heatmap.html")

            # Metric comparisons
            metrics = [col.replace('metric_', '') for col in df.columns if col.startswith('metric_')]
            for metric in metrics:
                comparison = self.create_metric_comparison(df, metric)
                comparison.write_html(f"{report_dir}/{metric}_comparison.html")

            # Timeline view
            timeline = self.create_timeline_view(df)
            timeline.write_html(f"{report_dir}/timeline.html")

            # Create index file
            with open(f"{report_dir}/index.html", 'w') as f:
                f.write("""
                <html>
                <head><title>Benchmark Visualization Report</title></head>
                <body>
                    <h1>Benchmark Visualization Report</h1>
                    <h2>Generated: {}</h2>
                    <ul>
                        <li><a href="heatmap.html">Performance Heatmap</a></li>
                        {}
                        <li><a href="timeline.html">Timeline View</a></li>
                    </ul>
                </body>
                </html>
                """.format(
                    datetime.now().isoformat(),
                    '\n'.join([
                        f'<li><a href="{metric}_comparison.html">{metric} Comparison</a></li>'
                        for metric in metrics
                    ])
                ))

            log(f"Visualization report generated: {report_dir}/index.html")
            return report_dir

        except Exception as e:
            log(f"Error generating visualizations: {e}")
            return None

def main():
    """Generate visualizations for benchmark results."""
    visualizer = BenchmarkVisualizer()
    report_dir = visualizer.generate_visualization_report()
    if report_dir:
        log(f"Open {report_dir}/index.html in a web browser to view the report")

if __name__ == "__main__":
    main()
