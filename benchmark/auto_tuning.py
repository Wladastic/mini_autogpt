"""Automated template tuning using optimization algorithms."""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel

from utils.log import log
from benchmark.templates import get_template, TEMPLATES
from benchmark.learning import TemplateOptimizationLearner
from benchmark.validation import validate_and_update_config

@dataclass
class OptimizationBounds:
    """Parameter bounds for optimization."""
    min_value: float
    max_value: float
    step: float = 0.01

class TemplateTuner:
    def __init__(self, data_dir="benchmark/tuning"):
        """Initialize the template tuner."""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.learner = TemplateOptimizationLearner()
        self.parameter_bounds = self._define_parameter_bounds()
        self.optimization_history = []

    def _define_parameter_bounds(self) -> Dict[str, OptimizationBounds]:
        """Define optimization bounds for parameters."""
        return {
            "max_retries": OptimizationBounds(0, 5, 1),
            "retry_delay": OptimizationBounds(1, 30, 1),
            "statistical_significance": OptimizationBounds(0.01, 0.1, 0.01),
            "min_samples": OptimizationBounds(3, 20, 1),
            "outlier_threshold": OptimizationBounds(1.5, 4.0, 0.1),
            "threshold": OptimizationBounds(0.5, 0.95, 0.05),
            "weight": OptimizationBounds(0.1, 2.0, 0.1)
        }

    def _create_objective_function(self, template: Dict[str, Any], target_metrics: Dict[str, float]) -> Callable:
        """Create an objective function for optimization."""
        def objective(x: np.ndarray) -> float:
            # Create template configuration from parameters
            config = template.copy()
            param_names = list(self.parameter_bounds.keys())
            
            for i, param in enumerate(x):
                if "threshold" in param_names[i]:
                    metric = param_names[i].split("_")[0]
                    config["metrics"][metric]["threshold"] = float(param)
                elif "weight" in param_names[i]:
                    metric = param_names[i].split("_")[0]
                    config["metrics"][metric]["weight"] = float(param)
                else:
                    config["system"][param_names[i]] = float(param)
            
            try:
                # Predict performance
                predictions = self.learner.predict_performance(config)
                
                # Calculate weighted loss
                loss = 0.0
                for metric, target in target_metrics.items():
                    if metric in predictions:
                        loss += abs(predictions[metric] - target)
                
                return loss
            except Exception as e:
                log(f"Error in objective function: {e}")
                return float('inf')
        
        return objective

    def tune_template(self, template_name: str, target_metrics: Dict[str, float], 
                     max_iterations: int = 100) -> Dict[str, Any]:
        """Tune a template to achieve target metrics."""
        template = get_template(template_name)
        initial_performance = self.learner.predict_performance(template)
        
        log(f"Initial performance for {template_name}:")
        for metric, value in initial_performance.items():
            log(f"- {metric}: {value:.3f}")
        
        # Set up optimization
        param_bounds = []
        initial_params = []
        param_names = []
        
        # Add bounds for system parameters
        for param, bounds in self.parameter_bounds.items():
            if param in template["system"]:
                param_bounds.append((bounds.min_value, bounds.max_value))
                initial_params.append(template["system"][param])
                param_names.append(param)
        
        # Add bounds for metric parameters
        for metric in target_metrics:
            if metric in template["metrics"]:
                # Threshold bounds
                param_bounds.append((0.5, 0.95))
                initial_params.append(template["metrics"][metric]["threshold"])
                param_names.append(f"{metric}_threshold")
                
                # Weight bounds
                param_bounds.append((0.1, 2.0))
                initial_params.append(template["metrics"][metric]["weight"])
                param_names.append(f"{metric}_weight")
        
        # Create objective function
        objective = self._create_objective_function(template, target_metrics)
        
        # Run optimization
        try:
            result = minimize(
                objective,
                x0=np.array(initial_params),
                bounds=param_bounds,
                method="L-BFGS-B",
                options={"maxiter": max_iterations}
            )
            
            # Create optimized template
            optimized = template.copy()
            for i, param_value in enumerate(result.x):
                param_name = param_names[i]
                if "_threshold" in param_name:
                    metric = param_name.split("_")[0]
                    optimized["metrics"][metric]["threshold"] = float(param_value)
                elif "_weight" in param_name:
                    metric = param_name.split("_")[0]
                    optimized["metrics"][metric]["weight"] = float(param_value)
                else:
                    optimized["system"][param_name] = float(param_value)
            
            # Validate optimized template
            validated, errors = validate_and_update_config(optimized)
            if errors:
                log("Validation warnings for optimized template:")
                for error in errors:
                    log(f"- {error}")
            
            # Save optimization history
            self.optimization_history.append({
                "timestamp": datetime.now().isoformat(),
                "template_name": template_name,
                "target_metrics": target_metrics,
                "initial_performance": initial_performance,
                "final_performance": self.learner.predict_performance(validated),
                "optimization_result": {
                    "success": result.success,
                    "message": result.message,
                    "iterations": result.nit,
                    "final_loss": float(result.fun)
                }
            })
            self._save_history()
            
            return validated
            
        except Exception as e:
            log(f"Optimization failed: {e}")
            return template

    def _save_history(self):
        """Save optimization history."""
        history_file = os.path.join(self.data_dir, "optimization_history.json")
        with open(history_file, "w") as f:
            json.dump(self.optimization_history, f, indent=2)

    def generate_tuning_report(self, template_name: str, original: Dict[str, Any], 
                             optimized: Dict[str, Any]) -> str:
        """Generate a report comparing original and optimized templates."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{self.data_dir}/tuning_report_{template_name}_{timestamp}.md"
        
        orig_perf = self.learner.predict_performance(original)
        opt_perf = self.learner.predict_performance(optimized)
        
        report = [
            f"# Template Tuning Report: {template_name}",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Performance Comparison",
            "| Metric | Original | Optimized | Change |",
            "|--------|-----------|------------|--------|"
        ]
        
        for metric in self.learner.metrics:
            orig = orig_perf.get(metric, 0)
            opt = opt_perf.get(metric, 0)
            change = ((opt - orig) / orig * 100) if orig != 0 else float('inf')
            report.append(
                f"| {metric} | {orig:.3f} | {opt:.3f} | "
                f"{'↑' if change > 0 else '↓'} {abs(change):.1f}% |"
            )
        
        report.extend([
            "",
            "## Parameter Changes",
            "### System Settings",
            "| Parameter | Original | Optimized |",
            "|-----------|-----------|------------|"
        ])
        
        for param in self.parameter_bounds:
            if param in original["system"]:
                orig = original["system"][param]
                opt = optimized["system"][param]
                report.append(f"| {param} | {orig} | {opt} |")
        
        report.extend([
            "",
            "### Metric Settings",
            "| Metric | Parameter | Original | Optimized |",
            "|--------|-----------|-----------|------------|"
        ])
        
        for metric in self.learner.metrics:
            if metric in original["metrics"]:
                for param in ["threshold", "weight"]:
                    orig = original["metrics"][metric].get(param, "-")
                    opt = optimized["metrics"][metric].get(param, "-")
                    report.append(f"| {metric} | {param} | {orig} | {opt} |")
        
        with open(report_file, "w") as f:
            f.write("\n".join(report))
        
        return report_file

def main():
    """CLI for template tuning."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Template Auto-Tuning")
    subparsers = parser.add_subparsers(dest="command")
    
    # Tune command
    tune_parser = subparsers.add_parser("tune", help="Tune a template")
    tune_parser.add_argument("template", help="Template name")
    tune_parser.add_argument("targets", help="JSON string of target metrics")
    tune_parser.add_argument("--iterations", type=int, default=100, help="Max iterations")
    tune_parser.add_argument("--save", help="Save as new profile")
    
    args = parser.parse_args()
    
    try:
        if args.command == "tune":
            tuner = TemplateTuner()
            targets = json.loads(args.targets)
            
            template = get_template(args.template)
            optimized = tuner.tune_template(args.template, targets, args.iterations)
            
            report_file = tuner.generate_tuning_report(args.template, template, optimized)
            print(f"Tuning report generated: {report_file}")
            
            if args.save:
                from benchmark.profiles import ProfileManager
                manager = ProfileManager()
                manager.create_profile(args.save, optimized)
                print(f"Saved tuned template as profile: {args.save}")
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
