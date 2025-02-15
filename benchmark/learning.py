"""Learning-based optimization for template performance."""

import os
import json
import pickle
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score

from utils.log import log
from benchmark.templates import TEMPLATES, get_template
from benchmark.recommendations import TemplateOptimizer

class TemplateOptimizationLearner:
    def __init__(self, data_dir="benchmark/learning_data"):
        """Initialize the learning-based optimizer."""
        self.data_dir = data_dir
        self.models_dir = os.path.join(data_dir, "models")
        self.history_dir = os.path.join(data_dir, "history")
        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)
        
        self.optimizer = TemplateOptimizer()
        self.metrics = ["response_quality", "context_usage", "memory_retention", "decision_quality"]
        self.features = self._get_feature_names()
        
        self.models = self._load_models()
        self.scalers = self._load_scalers()
        self.history = self._load_history()

    def _get_feature_names(self) -> List[str]:
        """Get all possible feature names from templates."""
        features = set()
        for template_name in TEMPLATES:
            template = get_template(template_name)
            features.update(self._extract_features(template).keys())
        return sorted(list(features))

    def _extract_features(self, template: Dict[str, Any]) -> Dict[str, float]:
        """Extract numerical features from template configuration."""
        features = {}
        
        # System features
        system = template.get("system", {})
        features["max_retries"] = float(system.get("max_retries", 0))
        features["retry_delay"] = float(system.get("retry_delay", 0))
        
        # Metric features
        metrics = template.get("metrics", {})
        for metric in self.metrics:
            config = metrics.get(metric, {})
            features[f"{metric}_enabled"] = float(config.get("enabled", False))
            features[f"{metric}_weight"] = float(config.get("weight", 0.0))
            features[f"{metric}_threshold"] = float(config.get("threshold", 0.0))
        
        # Analysis features
        analysis = template.get("analysis", {})
        features["statistical_significance"] = float(analysis.get("statistical_significance", 0.05))
        features["min_samples"] = float(analysis.get("min_samples", 5))
        features["outlier_threshold"] = float(analysis.get("outlier_threshold", 2.0))
        
        return features

    def _load_models(self) -> Dict[str, RandomForestRegressor]:
        """Load trained models for each metric."""
        models = {}
        for metric in self.metrics:
            model_path = os.path.join(self.models_dir, f"{metric}_model.pkl")
            if os.path.exists(model_path):
                with open(model_path, "rb") as f:
                    models[metric] = pickle.load(f)
            else:
                models[metric] = RandomForestRegressor(n_estimators=100, random_state=42)
        return models

    def _load_scalers(self) -> Dict[str, StandardScaler]:
        """Load feature scalers for each metric."""
        scalers = {}
        for metric in self.metrics:
            scaler_path = os.path.join(self.models_dir, f"{metric}_scaler.pkl")
            if os.path.exists(scaler_path):
                with open(scaler_path, "rb") as f:
                    scalers[metric] = pickle.load(f)
            else:
                scalers[metric] = StandardScaler()
        return scalers

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load training history."""
        history_path = os.path.join(self.history_dir, "training_history.json")
        if os.path.exists(history_path):
            with open(history_path, "r") as f:
                return json.load(f)
        return []

    def _save_models(self):
        """Save trained models and scalers."""
        for metric in self.metrics:
            model_path = os.path.join(self.models_dir, f"{metric}_model.pkl")
            scaler_path = os.path.join(self.models_dir, f"{metric}_scaler.pkl")
            
            with open(model_path, "wb") as f:
                pickle.dump(self.models[metric], f)
            with open(scaler_path, "wb") as f:
                pickle.dump(self.scalers[metric], f)

    def _save_history(self):
        """Save training history."""
        history_path = os.path.join(self.history_dir, "training_history.json")
        with open(history_path, "w") as f:
            json.dump(self.history, f, indent=2)

    def add_training_data(self, template_name: str, metrics: Dict[str, float]):
        """Add new training data from template performance."""
        template = get_template(template_name)
        features = self._extract_features(template)
        
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "template": template_name,
            "features": features,
            "metrics": metrics
        })
        
        self._save_history()
        self.train_models()  # Retrain models with new data

    def train_models(self):
        """Train predictive models for each metric."""
        if not self.history:
            log("No training data available")
            return
        
        # Prepare training data
        X = []
        y_dict = defaultdict(list)
        
        for entry in self.history:
            feature_vector = [entry["features"].get(f, 0.0) for f in self.features]
            X.append(feature_vector)
            for metric in self.metrics:
                y_dict[metric].append(entry["metrics"].get(metric, 0.0))
        
        X = np.array(X)
        
        # Train models for each metric
        for metric in self.metrics:
            y = np.array(y_dict[metric])
            if len(y) > 0:
                # Scale features
                X_scaled = self.scalers[metric].fit_transform(X)
                
                # Train model
                self.models[metric].fit(X_scaled, y)
                
                # Evaluate model
                scores = cross_val_score(self.models[metric], X_scaled, y, cv=3)
                log(f"Model performance for {metric}: {scores.mean():.3f} (±{scores.std():.3f})")
        
        self._save_models()

    def predict_performance(self, template: Dict[str, Any]) -> Dict[str, float]:
        """Predict performance metrics for a template configuration."""
        features = self._extract_features(template)
        feature_vector = np.array([[features.get(f, 0.0) for f in self.features]])
        
        predictions = {}
        for metric in self.metrics:
            if self.models[metric] is not None:
                X_scaled = self.scalers[metric].transform(feature_vector)
                predictions[metric] = float(self.models[metric].predict(X_scaled)[0])
        
        return predictions

    def suggest_improvements(self, template_name: str) -> Dict[str, Any]:
        """Suggest template improvements based on learned patterns."""
        template = get_template(template_name)
        current_performance = self.predict_performance(template)
        
        suggestions = {
            "current_performance": current_performance,
            "suggested_changes": [],
            "expected_improvements": {}
        }
        
        # Try adjusting each feature
        base_features = self._extract_features(template)
        for feature in self.features:
            if feature in base_features:
                original_value = base_features[feature]
                
                # Try increasing and decreasing the feature value
                for adjustment in [0.8, 1.2]:  # -20% and +20%
                    base_features[feature] = original_value * adjustment
                    new_performance = self.predict_performance({"metrics": base_features})
                    
                    improvements = {
                        metric: new_perf - current_performance[metric]
                        for metric, new_perf in new_performance.items()
                    }
                    
                    if any(imp > 0.05 for imp in improvements.values()):  # 5% improvement threshold
                        suggestions["suggested_changes"].append({
                            "feature": feature,
                            "current_value": original_value,
                            "suggested_value": base_features[feature],
                            "improvements": improvements
                        })
                
                # Reset feature value
                base_features[feature] = original_value
        
        return suggestions

def main():
    """CLI for learning-based optimization."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Learning-based Template Optimization")
    subparsers = parser.add_subparsers(dest="command")
    
    # Train command
    train_parser = subparsers.add_parser("train", help="Train optimization models")
    
    # Predict command
    predict_parser = subparsers.add_parser("predict", help="Predict template performance")
    predict_parser.add_argument("template", help="Template name")
    
    # Improve command
    improve_parser = subparsers.add_parser("improve", help="Suggest template improvements")
    improve_parser.add_argument("template", help="Template name")
    
    args = parser.parse_args()
    
    learner = TemplateOptimizationLearner()
    
    try:
        if args.command == "train":
            learner.train_models()
            print("Models trained successfully")
        
        elif args.command == "predict":
            template = get_template(args.template)
            predictions = learner.predict_performance(template)
            print("\nPredicted Performance:")
            for metric, value in predictions.items():
                print(f"- {metric}: {value:.3f}")
        
        elif args.command == "improve":
            suggestions = learner.suggest_improvements(args.template)
            print("\nImprovement Suggestions:")
            for change in suggestions["suggested_changes"]:
                print(f"\nFeature: {change['feature']}")
                print(f"Current value: {change['current_value']:.3f}")
                print(f"Suggested value: {change['suggested_value']:.3f}")
                print("Expected improvements:")
                for metric, imp in change["improvements"].items():
                    if imp > 0:
                        print(f"- {metric}: +{imp:.1%}")
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
