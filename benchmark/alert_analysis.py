"""Alert trend prediction and correlation analysis."""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from scipy import stats
from sklearn.linear_model import LinearRegression
import pandas as pd

from utils.log import log
from benchmark.alert_notifications import AlertSeverity

@dataclass
class TrendPrediction:
    """Trend prediction results."""
    resource: str
    current_value: float
    predicted_value: float
    confidence: float
    trend_direction: str
    time_to_threshold: Optional[float]  # Hours until threshold breach
    description: str

@dataclass
class ResourceCorrelation:
    """Correlation between resources."""
    resource1: str
    resource2: str
    correlation: float
    confidence: float
    lag: int  # Time lag in minutes
    description: str

class AlertAnalyzer:
    def __init__(self):
        """Initialize alert analyzer."""
        self.min_samples = 10
        self.confidence_threshold = 0.8

    def prepare_timeseries(self, alerts: List[Dict[str, Any]], 
                          resource: str) -> pd.DataFrame:
        """Prepare timeseries data for analysis."""
        # Convert alerts to dataframe
        df = pd.DataFrame([
            {
                "timestamp": datetime.fromisoformat(a["timestamp"]),
                "value": float(a["value"])
            }
            for a in alerts
            if a["resource"] == resource
        ])
        
        if df.empty:
            return pd.DataFrame()
        
        # Sort by timestamp
        df = df.sort_values("timestamp")
        
        # Add time features
        df["hour"] = df["timestamp"].dt.hour
        df["day_of_week"] = df["timestamp"].dt.dayofweek
        df["minutes"] = df["timestamp"].dt.minute
        
        return df

    def predict_trend(self, alerts: List[Dict[str, Any]], 
                     resource: str, 
                     hours_ahead: int = 24) -> Optional[TrendPrediction]:
        """Predict trend for a resource."""
        df = self.prepare_timeseries(alerts, resource)
        if len(df) < self.min_samples:
            return None
        
        try:
            # Prepare features
            X = np.array(range(len(df))).reshape(-1, 1)
            y = df["value"].values
            
            # Fit linear regression
            model = LinearRegression()
            model.fit(X, y)
            
            # Calculate confidence
            y_pred = model.predict(X)
            r2 = model.score(X, y)
            
            # Predict future value
            future_x = np.array([[len(df) + hours_ahead]])
            predicted_value = float(model.predict(future_x)[0])
            
            # Determine trend direction
            trend = "increasing" if model.coef_[0] > 0 else "decreasing"
            
            # Find latest threshold
            latest_threshold = max(
                (a["threshold"] for a in alerts if a["resource"] == resource),
                default=None
            )
            
            # Calculate time to threshold breach
            time_to_threshold = None
            if latest_threshold and model.coef_[0] != 0:
                steps_to_threshold = (latest_threshold - model.intercept_) / model.coef_[0]
                if steps_to_threshold > 0:
                    time_to_threshold = steps_to_threshold * (
                        sum(np.diff(df["timestamp"].values)) / len(df) / np.timedelta64(1, "h")
                    )
            
            return TrendPrediction(
                resource=resource,
                current_value=float(y[-1]),
                predicted_value=predicted_value,
                confidence=r2,
                trend_direction=trend,
                time_to_threshold=time_to_threshold,
                description=(
                    f"{resource} shows {trend} trend "
                    f"(R²={r2:.2f}). "
                    f"Current: {float(y[-1]):.1f}, "
                    f"Predicted in {hours_ahead}h: {predicted_value:.1f}"
                    + (f", Threshold breach in {time_to_threshold:.1f}h"
                       if time_to_threshold is not None else "")
                )
            )
        
        except Exception as e:
            log(f"Error predicting trend for {resource}: {e}")
            return None

    def analyze_correlations(self, alerts: List[Dict[str, Any]], 
                           max_lag_minutes: int = 60) -> List[ResourceCorrelation]:
        """Analyze correlations between resources."""
        # Group alerts by resource
        resource_data = {}
        for alert in alerts:
            resource = alert["resource"]
            if resource not in resource_data:
                resource_data[resource] = self.prepare_timeseries(alerts, resource)
        
        correlations = []
        for resource1 in resource_data:
            df1 = resource_data[resource1]
            if df1.empty:
                continue
                
            for resource2 in resource_data:
                if resource1 >= resource2:  # Avoid duplicates
                    continue
                    
                df2 = resource_data[resource2]
                if df2.empty:
                    continue
                
                try:
                    # Calculate cross-correlation with different lags
                    max_corr = 0
                    best_lag = 0
                    
                    for lag in range(-max_lag_minutes, max_lag_minutes + 1):
                        if lag > 0:
                            series1 = df1["value"][lag:]
                            series2 = df2["value"][:-lag]
                        else:
                            series1 = df1["value"][:lag]
                            series2 = df2["value"][-lag:]
                        
                        if len(series1) < self.min_samples:
                            continue
                            
                        corr = stats.pearsonr(series1, series2)
                        if abs(corr[0]) > abs(max_corr):
                            max_corr = corr[0]
                            best_lag = lag
                    
                    if abs(max_corr) > 0.5:  # Only include significant correlations
                        correlations.append(ResourceCorrelation(
                            resource1=resource1,
                            resource2=resource2,
                            correlation=max_corr,
                            confidence=1 - stats.pearsonr(
                                df1["value"], df2["value"]
                            )[1],
                            lag=best_lag,
                            description=(
                                f"{resource1} and {resource2} show "
                                f"{'positive' if max_corr > 0 else 'negative'} "
                                f"correlation (r={max_corr:.2f}) "
                                f"with {abs(best_lag)}min lag"
                            )
                        ))
                
                except Exception as e:
                    log(f"Error analyzing correlation between {resource1} and {resource2}: {e}")
        
        return correlations

    def generate_analysis_report(self, alerts: List[Dict[str, Any]], 
                               hours_ahead: int = 24) -> str:
        """Generate trend and correlation analysis report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"benchmark/analysis/analysis_report_{timestamp}.html"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        # Get unique resources
        resources = sorted(set(alert["resource"] for alert in alerts))
        
        # Generate predictions and correlations
        predictions = []
        for resource in resources:
            pred = self.predict_trend(alerts, resource, hours_ahead)
            if pred:
                predictions.append(pred)
        
        correlations = self.analyze_correlations(alerts)
        
        # Generate report
        html_content = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Alert Analysis Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            ".prediction { background-color: #e3f2fd; padding: 10px; margin: 10px 0; }",
            ".correlation { background-color: #f3e5f5; padding: 10px; margin: 10px 0; }",
            ".warning { color: #f57c00; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>Alert Analysis Report</h1>",
            f"<p>Generated: {datetime.now().isoformat()}</p>",
            f"<p>Analyzing {len(alerts)} alerts across {len(resources)} resources</p>"
        ]
        
        # Add predictions section
        html_content.extend([
            "<h2>Trend Predictions</h2>"
        ])
        
        for pred in sorted(predictions, key=lambda p: p.confidence, reverse=True):
            warning_class = " warning" if pred.time_to_threshold and pred.time_to_threshold < 24 else ""
            html_content.append(
                f'<div class="prediction{warning_class}">'
                f"<h3>{pred.resource}</h3>"
                f"<p>{pred.description}</p>"
                f"<p>Confidence: {pred.confidence:.2%}</p>"
                "</div>"
            )
        
        # Add correlations section
        if correlations:
            html_content.extend([
                "<h2>Resource Correlations</h2>"
            ])
            
            for corr in sorted(correlations, key=lambda c: abs(c.correlation), reverse=True):
                html_content.append(
                    f'<div class="correlation">'
                    f"<p>{corr.description}</p>"
                    f"<p>Confidence: {corr.confidence:.2%}</p>"
                    "</div>"
                )
        
        html_content.extend([
            "</body>",
            "</html>"
        ])
        
        with open(report_file, "w") as f:
            f.write("\n".join(html_content))
        
        return report_file

def create_alert_analyzer() -> AlertAnalyzer:
    """Create alert analyzer."""
    return AlertAnalyzer()
