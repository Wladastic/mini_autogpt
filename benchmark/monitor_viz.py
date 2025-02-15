"""Visualization tools for resource monitoring data."""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class MonitoringVisualizer:
    def __init__(self, monitoring_dir: str = "benchmark/monitoring"):
        """Initialize monitoring visualizer."""
        self.monitoring_dir = monitoring_dir
        self.output_dir = os.path.join(monitoring_dir, "visualizations")
        os.makedirs(self.output_dir, exist_ok=True)

    def load_monitoring_data(self) -> Dict[str, Any]:
        """Load monitoring data from files."""
        data = {"summaries": [], "details": []}
        
        # Load summary files
        for filename in os.listdir(self.monitoring_dir):
            if filename.startswith("monitor_summary_") and filename.endswith(".json"):
                with open(os.path.join(self.monitoring_dir, filename), 'r') as f:
                    data["summaries"].append(json.load(f))
            
            elif filename.startswith("monitor_details_") and filename.endswith(".json"):
                with open(os.path.join(self.monitoring_dir, filename), 'r') as f:
                    data["details"].extend(json.load(f))
        
        return data

    def create_resource_timeline(self, data: List[Dict[str, Any]]) -> None:
        """Create timeline visualization of resource usage."""
        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        
        fig = make_subplots(
            rows=4, cols=1,
            subplot_titles=(
                "CPU Usage",
                "Memory Usage",
                "Disk I/O",
                "Network I/O"
            ),
            vertical_spacing=0.1
        )
        
        # CPU Usage
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['cpu_percent'],
                name="CPU %",
                mode="lines",
                line=dict(color='red')
            ),
            row=1, col=1
        )
        
        # Memory Usage
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['memory_percent'],
                name="Memory %",
                mode="lines",
                line=dict(color='blue')
            ),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['memory_used_mb'],
                name="Memory Used (MB)",
                mode="lines",
                line=dict(color='lightblue'),
                visible='legendonly'
            ),
            row=2, col=1
        )
        
        # Disk I/O
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['disk_read_mbs'],
                name="Disk Read (MB/s)",
                mode="lines",
                line=dict(color='green')
            ),
            row=3, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['disk_write_mbs'],
                name="Disk Write (MB/s)",
                mode="lines",
                line=dict(color='lightgreen')
            ),
            row=3, col=1
        )
        
        # Network I/O
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['network_sent_mbs'],
                name="Network Send (MB/s)",
                mode="lines",
                line=dict(color='orange')
            ),
            row=4, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df['network_recv_mbs'],
                name="Network Receive (MB/s)",
                mode="lines",
                line=dict(color='yellow')
            ),
            row=4, col=1
        )
        
        fig.update_layout(
            height=1200,
            title_text="Resource Usage Timeline",
            showlegend=True
        )
        
        fig.write_html(os.path.join(self.output_dir, "resource_timeline.html"))

    def create_resource_summary(self, summaries: List[Dict[str, Any]]) -> None:
        """Create summary visualization of resource usage across runs."""
        if not summaries:
            return
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "CPU Usage Distribution",
                "Memory Usage Distribution",
                "I/O Performance",
                "Thread/Process Count"
            )
        )
        
        # CPU Distribution
        cpu_data = []
        for summary in summaries:
            cpu_data.extend([
                summary["cpu"]["min"],
                summary["cpu"]["avg"],
                summary["cpu"]["max"]
            ])
        
        fig.add_trace(
            go.Box(
                y=cpu_data,
                name="CPU %",
                boxpoints="all"
            ),
            row=1, col=1
        )
        
        # Memory Distribution
        memory_data = []
        for summary in summaries:
            memory_data.extend([
                summary["memory"]["min"],
                summary["memory"]["avg"],
                summary["memory"]["max"]
            ])
        
        fig.add_trace(
            go.Box(
                y=memory_data,
                name="Memory %",
                boxpoints="all"
            ),
            row=1, col=2
        )
        
        # I/O Performance
        io_reads = [s["disk_read_mbs"]["avg"] for s in summaries]
        io_writes = [s["disk_write_mbs"]["avg"] for s in summaries]
        net_send = [s["network_sent_mbs"]["avg"] for s in summaries]
        net_recv = [s["network_recv_mbs"]["avg"] for s in summaries]
        
        fig.add_trace(
            go.Bar(
                x=["Disk Read", "Disk Write", "Net Send", "Net Recv"],
                y=[sum(io_reads)/len(io_reads),
                   sum(io_writes)/len(io_writes),
                   sum(net_send)/len(net_send),
                   sum(net_recv)/len(net_recv)],
                name="I/O MB/s"
            ),
            row=2, col=1
        )
        
        # Thread/Process counts
        threads = [s["max_threads"] for s in summaries]
        processes = [s["max_processes"] for s in summaries]
        
        fig.add_trace(
            go.Bar(
                x=["Threads", "Processes"],
                y=[max(threads), max(processes)],
                name="Peak Counts"
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=800,
            title_text="Resource Usage Summary",
            showlegend=True
        )
        
        fig.write_html(os.path.join(self.output_dir, "resource_summary.html"))

    def generate_report(self) -> str:
        """Generate complete monitoring visualization report."""
        data = self.load_monitoring_data()
        
        if data["details"]:
            self.create_resource_timeline(data["details"])
        if data["summaries"]:
            self.create_resource_summary(data["summaries"])
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.output_dir, f"monitoring_report_{timestamp}.html")
        
        # Create combined report
        html_content = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Resource Monitoring Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "iframe { width: 100%; height: 800px; border: none; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>Resource Monitoring Report</h1>",
            f"<p>Generated: {datetime.now().isoformat()}</p>",
            "<h2>Resource Usage Timeline</h2>",
            '<iframe src="resource_timeline.html"></iframe>',
            "<h2>Resource Usage Summary</h2>",
            '<iframe src="resource_summary.html"></iframe>',
            "</body>",
            "</html>"
        ]
        
        with open(report_file, 'w') as f:
            f.write("\n".join(html_content))
        
        return report_file

def main():
    """Generate monitoring visualizations."""
    try:
        visualizer = MonitoringVisualizer()
        report_file = visualizer.generate_report()
        print(f"Monitoring visualization report generated: {report_file}")
    except Exception as e:
        print(f"Error generating visualizations: {e}")

if __name__ == "__main__":
    main()
