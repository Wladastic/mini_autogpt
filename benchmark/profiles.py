"""Configuration profile management for benchmark system."""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional

from utils.log import log
from benchmark.validation import validate_and_update_config, ValidationError
from benchmark.config import DEFAULT_CONFIG

class ProfileManager:
    def __init__(self, profiles_dir: str = "benchmark/profiles"):
        """Initialize profile manager."""
        self.profiles_dir = profiles_dir
        self.active_profile = "default"
        os.makedirs(profiles_dir, exist_ok=True)

    def list_profiles(self) -> List[str]:
        """List available configuration profiles."""
        profiles = []
        for filename in os.listdir(self.profiles_dir):
            if filename.endswith(".json"):
                profiles.append(filename[:-5])  # Remove .json extension
        return sorted(profiles)

    def create_profile(self, name: str, config: Dict[str, Any] = None) -> str:
        """Create a new configuration profile."""
        if not name.isidentifier():
            raise ValueError(f"Invalid profile name: {name} (must be a valid Python identifier)")

        profile_path = os.path.join(self.profiles_dir, f"{name}.json")
        
        if os.path.exists(profile_path):
            raise FileExistsError(f"Profile '{name}' already exists")

        try:
            # Start with default config if none provided
            profile_config = config or DEFAULT_CONFIG.copy()
            
            # Validate configuration
            validated_config, errors = validate_and_update_config(profile_config)
            if errors:
                log("Configuration warnings for new profile:")
                for error in errors:
                    log(f"- {error}")

            # Save validated configuration
            with open(profile_path, 'w') as f:
                json.dump(validated_config, f, indent=2)
            
            log(f"Created profile '{name}'")
            return profile_path

        except Exception as e:
            log(f"Error creating profile '{name}': {e}")
            raise

    def load_profile(self, name: str) -> Dict[str, Any]:
        """Load a configuration profile."""
        profile_path = os.path.join(self.profiles_dir, f"{name}.json")
        
        if not os.path.exists(profile_path):
            raise FileNotFoundError(f"Profile '{name}' not found")

        try:
            with open(profile_path, 'r') as f:
                config = json.load(f)
            
            # Validate loaded configuration
            validated_config, errors = validate_and_update_config(config)
            if errors:
                log(f"Configuration warnings for profile '{name}':")
                for error in errors:
                    log(f"- {error}")
            
            self.active_profile = name
            return validated_config

        except Exception as e:
            log(f"Error loading profile '{name}': {e}")
            raise

    def save_profile(self, name: str, config: Dict[str, Any]) -> None:
        """Save current configuration to a profile."""
        profile_path = os.path.join(self.profiles_dir, f"{name}.json")
        
        try:
            # Create backup if profile exists
            if os.path.exists(profile_path):
                self._create_backup(profile_path)
            
            # Validate configuration before saving
            validated_config, errors = validate_and_update_config(config)
            if errors:
                log(f"Configuration warnings for profile '{name}':")
                for error in errors:
                    log(f"- {error}")
            
            # Save validated configuration
            with open(profile_path, 'w') as f:
                json.dump(validated_config, f, indent=2)
            
            log(f"Saved profile '{name}'")

        except Exception as e:
            log(f"Error saving profile '{name}': {e}")
            raise

    def delete_profile(self, name: str) -> None:
        """Delete a configuration profile."""
        if name == "default":
            raise ValueError("Cannot delete default profile")

        profile_path = os.path.join(self.profiles_dir, f"{name}.json")
        
        if not os.path.exists(profile_path):
            raise FileNotFoundError(f"Profile '{name}' not found")

        try:
            # Create backup before deletion
            self._create_backup(profile_path)
            
            # Delete profile
            os.remove(profile_path)
            log(f"Deleted profile '{name}'")

            # Reset to default if active profile was deleted
            if self.active_profile == name:
                self.active_profile = "default"
                log("Reset to default profile")

        except Exception as e:
            log(f"Error deleting profile '{name}': {e}")
            raise

    def _create_backup(self, profile_path: str) -> str:
        """Create a backup of a profile file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(self.profiles_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        filename = os.path.basename(profile_path)
        backup_path = os.path.join(backup_dir, f"{filename[:-5]}_{timestamp}.json")
        
        shutil.copy2(profile_path, backup_path)
        log(f"Created backup: {backup_path}")
        
        return backup_path

    def get_active_profile(self) -> str:
        """Get the name of the currently active profile."""
        return self.active_profile

def main():
    """CLI for profile management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark Profile Manager")
    subparsers = parser.add_subparsers(dest="command")
    
    # List command
    subparsers.add_parser("list", help="List available profiles")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new profile")
    create_parser.add_argument("name", help="Profile name")
    
    # Load command
    load_parser = subparsers.add_parser("load", help="Load a profile")
    load_parser.add_argument("name", help="Profile name")
    
    # Save command
    save_parser = subparsers.add_parser("save", help="Save current config to profile")
    save_parser.add_argument("name", help="Profile name")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a profile")
    delete_parser.add_argument("name", help="Profile name")
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show profile contents")
    show_parser.add_argument("name", help="Profile name")
    
    args = parser.parse_args()
    
    manager = ProfileManager()
    
    try:
        if args.command == "list":
            profiles = manager.list_profiles()
            print("\nAvailable profiles:")
            for profile in profiles:
                active = " (active)" if profile == manager.get_active_profile() else ""
                print(f"- {profile}{active}")
            
        elif args.command == "create":
            path = manager.create_profile(args.name)
            print(f"Created profile: {path}")
            
        elif args.command == "load":
            config = manager.load_profile(args.name)
            print(f"Loaded profile: {args.name}")
            print(json.dumps(config, indent=2))
            
        elif args.command == "save":
            from benchmark.config import config
            manager.save_profile(args.name, config.config)
            print(f"Saved current configuration to profile: {args.name}")
            
        elif args.command == "delete":
            manager.delete_profile(args.name)
            print(f"Deleted profile: {args.name}")
            
        elif args.command == "show":
            config = manager.load_profile(args.name)
            print(f"\nProfile: {args.name}")
            print(json.dumps(config, indent=2))
            
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
