"""Statistical analysis tools for benchmark results."""

import json
import os
from typing import Dict, List, Any, Tuple

import numpy as np
from scipy import stats
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score
import statsmodels.api as sm
from utils.log import log

class BenchmarkStatistics:
    def __init__(self, results_dir="benchmark/results", output_dir="benchmark/statistics"):
        """Initialize the statistics analyzer."""
        self.results_dir = results_dir
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def load_data(self, filter_model=None, filter_scenario=None) -> pd.DataFrame:
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
                flat_result = self.flatten_result(result)
                results.append(flat_result)
        
        return pd.DataFrame(results)

    def flatten_result(self, result: Dict) -> Dict:
        """Flatten nested result structure."""
        flat = {
            "model": result["model"],
            "scenario": result["scenario"],
            "timestamp": result["timestamp"],
            "duration": result["duration"],
            "iterations": result["iterations_completed"]
        }
        
        # Flatten metrics
        for metric, value in result["metrics"].items():
            if isinstance(value, (int, float)):
                flat[f"metric_{metric}"] = value
        
        return flat

    def calculate_basic_stats(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Calculate basic statistical measures."""
        metrics = [col for col in df.columns if col.startswith('metric_')]
        stats_dict = {}
        
        for metric in metrics:
            stats_dict[metric] = {
                "mean": df[metric].mean(),
                "median": df[metric].median(),
                "std": df[metric].std(),
                "min": df[metric].min(),
                "max": df[metric].max(),
                "skewness": stats.skew(df[metric].dropna()),
                "kurtosis": stats.kurtosis(df[metric].dropna())
            }
        
        return stats_dict

    def perform_anova(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Perform one-way ANOVA for each metric across models."""
        metrics = [col for col in df.columns if col.startswith('metric_')]
        anova_results = {}
        
        for metric in metrics:
            models = df['model'].unique()
            groups = [df[df['model'] == model][metric].values for model in models]
            
            try:
                f_stat, p_value = stats.f_oneway(*groups)
                anova_results[metric] = {
                    "f_statistic": f_stat,
                    "p_value": p_value,
                    "significant": p_value < 0.05
                }
            except Exception as e:
                log(f"Error performing ANOVA for {metric}: {e}")
                continue
        
        return anova_results

    def analyze_trends(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Analyze performance trends over time."""
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        metrics = [col for col in df.columns if col.startswith('metric_')]
        trend_results = {}
        
        for metric in metrics:
            # Sort by timestamp
            metric_data = df.sort_values('timestamp')[[metric, 'timestamp']]
            x = (metric_data['timestamp'] - metric_data['timestamp'].min()).dt.total_seconds()
            y = metric_data[metric]
            
            try:
                # Linear regression
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                
                trend_results[metric] = {
                    "slope": slope,
                    "r_squared": r_value**2,
                    "p_value": p_value,
                    "significant": p_value < 0.05,
                    "trend": "improving" if slope > 0 else "declining"
                }
            except Exception as e:
                log(f"Error analyzing trend for {metric}: {e}")
                continue
        
        return trend_results

    def compare_models(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Perform statistical comparison between models."""
        metrics = [col for col in df.columns if col.startswith('metric_')]
        models = df['model'].unique()
        comparison_results = {}
        
        for metric in metrics:
            model_comparisons = {}
            
            for i, model1 in enumerate(models):
                for model2 in models[i+1:]:
                    group1 = df[df['model'] == model1][metric]
                    group2 = df[df['model'] == model2][metric]
                    
                    try:
                        # Perform t-test
                        t_stat, p_value = stats.ttest_ind(group1, group2)
                        
                        # Calculate effect size (Cohen's d)
                        cohens_d = (group1.mean() - group2.mean()) / np.sqrt(
                            ((group1.std() ** 2) + (group2.std() ** 2)) / 2
                        )
                        
                        model_comparisons[f"{model1}_vs_{model2}"] = {
                            "t_statistic": t_stat,
                            "p_value": p_value,
                            "significant": p_value < 0.05,
                            "effect_size": cohens_d,
                            "better_model": model1 if group1.mean() > group2.mean() else model2
                        }
                    except Exception as e:
                        log(f"Error comparing models for {metric}: {e}")
                        continue
            
            comparison_results[metric] = model_comparisons
        
        return comparison_results

    def generate_report(self, filter_model=None, filter_scenario=None) -> str:
        """Generate a comprehensive statistical analysis report."""
        df = self.load_data(filter_model, filter_scenario)
        if df.empty:
            return "No data available for analysis."

        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{self.output_dir}/stats_report_{timestamp}.md"

        # Perform analyses
        basic_stats = self.calculate_basic_stats(df)
        anova_results = self.perform_anova(df)
        trend_results = self.analyze_trends(df)
        model_comparisons = self.compare_models(df)

        # Generate report
        report = [
            "# Statistical Analysis Report",
            f"Generated: {pd.Timestamp.now().isoformat()}",
            "",
            "## Dataset Overview",
            f"- Total Samples: {len(df)}",
            f"- Models: {', '.join(df['model'].unique())}",
            f"- Scenarios: {', '.join(df['scenario'].unique())}",
            "",
            "## Basic Statistics",
        ]

        # Add basic stats
        for metric, stats_dict in basic_stats.items():
            report.extend([
                f"### {metric.replace('metric_', '')}",
                "```",
                *[f"{k}: {v:.4f}" for k, v in stats_dict.items()],
                "```",
                ""
            ])

        # Add ANOVA results
        report.extend([
            "## ANOVA Results",
            "Testing for significant differences between models:",
            ""
        ])
        for metric, results in anova_results.items():
            report.extend([
                f"### {metric.replace('metric_', '')}",
                f"- F-statistic: {results['f_statistic']:.4f}",
                f"- p-value: {results['p_value']:.4f}",
                f"- Significant: {'Yes' if results['significant'] else 'No'}",
                ""
            ])

        # Add trend analysis
        report.extend([
            "## Performance Trends",
            "Analysis of metric trends over time:",
            ""
        ])
        for metric, results in trend_results.items():
            report.extend([
                f"### {metric.replace('metric_', '')}",
                f"- Trend: {results['trend']}",
                f"- R-squared: {results['r_squared']:.4f}",
                f"- Significant: {'Yes' if results['significant'] else 'No'}",
                ""
            ])

        # Add model comparisons
        report.extend([
            "## Model Comparisons",
            "Pairwise comparison of model performance:",
            ""
        ])
        for metric, comparisons in model_comparisons.items():
            report.extend([
                f"### {metric.replace('metric_', '')}",
                ""
            ])
            for comparison, results in comparisons.items():
                report.extend([
                    f"#### {comparison}",
                    f"- Better model: {results['better_model']}",
                    f"- Effect size: {results['effect_size']:.4f}",
                    f"- Significant: {'Yes' if results['significant'] else 'No'}",
                    ""
                ])

        # Write report
        with open(report_file, 'w') as f:
            f.write("\n".join(report))

        log(f"Statistical analysis report generated: {report_file}")
        return report_file

def main():
    """Generate statistical analysis for benchmark results."""
    analyzer = BenchmarkStatistics()
    report_file = analyzer.generate_report()
    log(f"Analysis complete. Report saved to: {report_file}")

if __name__ == "__main__":
    main()
