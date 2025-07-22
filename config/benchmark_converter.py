# config/benchmark_converter.py
"""
Benchmark Converter for NEAR Partnership Analysis

Handles conversion between JSON and CSV formats for partnership benchmarks.
Supports both directions: JSON to CSV and CSV to JSON.
"""

import pandas as pd
import json
import os
from typing import Dict, Any, List


class BenchmarkConverter:
    """Converts partnership benchmarks between JSON and CSV formats."""
    
    def __init__(self, config_dir: str = None):
        """Initialize converter with config directory path."""
        self.config_dir = config_dir or os.path.dirname(__file__)
        
        # Define file paths
        self.json_file = os.path.join(self.config_dir, 'partnership_benchmarks.json')
        self.csv_examples_file = os.path.join(self.config_dir, 'partnership_benchmarks_examples.csv')
        self.csv_principles_file = os.path.join(self.config_dir, 'partnership_benchmarks_principles.csv')
        self.csv_scoring_file = os.path.join(self.config_dir, 'partnership_benchmarks_scoring.csv')
    
    def json_to_csv(self, json_data: Dict[str, Any] = None) -> None:
        """
        Convert JSON benchmark data to CSV files.
        
        Args:
            json_data: JSON data to convert. If None, reads from JSON file.
        """
        if json_data is None:
            if not os.path.exists(self.json_file):
                raise FileNotFoundError(f"JSON file not found: {self.json_file}")
            
            with open(self.json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
        
        # Convert examples (complementary and competitive)
        self._convert_examples_to_csv(json_data)
        
        # Convert principles
        self._convert_principles_to_csv(json_data)
        
        # Convert scoring guidance
        self._convert_scoring_to_csv(json_data)
        
        print(f"✅ JSON converted to CSV files:")
        print(f"   - {self.csv_examples_file}")
        print(f"   - {self.csv_principles_file}")
        print(f"   - {self.csv_scoring_file}")
    
    def csv_to_json(self) -> Dict[str, Any]:
        """
        Convert CSV files to JSON format.
        
        Returns:
            JSON data structure
        """
        # Check if CSV files exist
        required_files = [self.csv_examples_file, self.csv_principles_file, self.csv_scoring_file]
        missing_files = [f for f in required_files if not os.path.exists(f)]
        
        if missing_files:
            raise FileNotFoundError(f"CSV files not found: {missing_files}")
        
        json_data = {
            "framework_benchmarks": {},
            "framework_principles": {},
            "scoring_guidance": {}
        }
        
        # Convert examples
        examples_df = pd.read_csv(self.csv_examples_file)
        json_data["framework_benchmarks"] = self._convert_examples_from_csv(examples_df)
        
        # Convert principles
        principles_df = pd.read_csv(self.csv_principles_file)
        json_data["framework_principles"] = self._convert_principles_from_csv(principles_df)
        
        # Convert scoring guidance
        scoring_df = pd.read_csv(self.csv_scoring_file)
        json_data["scoring_guidance"] = self._convert_scoring_from_csv(scoring_df)
        
        # Save to JSON file
        with open(self.json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ CSV files converted to JSON: {self.json_file}")
        return json_data
    
    def _convert_examples_to_csv(self, json_data: Dict[str, Any]) -> None:
        """Convert framework examples to CSV."""
        examples = []
        
        # Process complementary examples
        for example in json_data.get("framework_benchmarks", {}).get("complementary_examples", []):
            examples.append({
                "category": "complementary",
                "partner": example.get("partner", ""),
                "score": example.get("score", 0),
                "type": example.get("type", ""),
                "description": example.get("description", ""),
                "evidence": example.get("evidence", "")
            })
        
        # Process competitive examples
        for example in json_data.get("framework_benchmarks", {}).get("competitive_examples", []):
            examples.append({
                "category": "competitive",
                "partner": example.get("partner", ""),
                "score": example.get("score", 0),
                "type": example.get("type", ""),
                "description": example.get("description", ""),
                "evidence": example.get("evidence", "")
            })
        
        # Save to CSV
        df = pd.DataFrame(examples)
        df.to_csv(self.csv_examples_file, index=False, encoding='utf-8')
    
    def _convert_principles_to_csv(self, json_data: Dict[str, Any]) -> None:
        """Convert framework principles to CSV."""
        principles = []
        
        # Process complementary signs
        for principle in json_data.get("framework_principles", {}).get("complementary_signs", []):
            principles.append({
                "principle_type": "complementary_signs",
                "principle_text": principle
            })
        
        # Process competitive red flags
        for principle in json_data.get("framework_principles", {}).get("competitive_red_flags", []):
            principles.append({
                "principle_type": "competitive_red_flags",
                "principle_text": principle
            })
        
        # Save to CSV
        df = pd.DataFrame(principles)
        df.to_csv(self.csv_principles_file, index=False, encoding='utf-8')
    
    def _convert_scoring_to_csv(self, json_data: Dict[str, Any]) -> None:
        """Convert scoring guidance to CSV."""
        scoring = []
        
        for category, details in json_data.get("scoring_guidance", {}).items():
            # Handle examples as comma-separated string
            examples_str = ", ".join(details.get("examples", []))
            
            scoring.append({
                "category": category,
                "range": details.get("range", ""),
                "action": details.get("action", ""),
                "examples": examples_str
            })
        
        # Save to CSV
        df = pd.DataFrame(scoring)
        df.to_csv(self.csv_scoring_file, index=False, encoding='utf-8')
    
    def _convert_examples_from_csv(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """Convert examples CSV back to JSON structure."""
        result = {
            "complementary_examples": [],
            "competitive_examples": []
        }
        
        for _, row in df.iterrows():
            example = {
                "partner": row["partner"],
                "score": int(row["score"]),
                "type": row["type"],
                "description": row["description"],
                "evidence": row["evidence"]
            }
            
            if row["category"] == "complementary":
                result["complementary_examples"].append(example)
            elif row["category"] == "competitive":
                result["competitive_examples"].append(example)
        
        return result
    
    def _convert_principles_from_csv(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Convert principles CSV back to JSON structure."""
        result = {
            "complementary_signs": [],
            "competitive_red_flags": []
        }
        
        for _, row in df.iterrows():
            principle_type = row["principle_type"]
            principle_text = row["principle_text"]
            
            if principle_type in result:
                result[principle_type].append(principle_text)
        
        return result
    
    def _convert_scoring_from_csv(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Convert scoring CSV back to JSON structure."""
        result = {}
        
        for _, row in df.iterrows():
            # Split examples string back to list
            examples_list = [ex.strip() for ex in row["examples"].split(",") if ex.strip()]
            
            result[row["category"]] = {
                "range": row["range"],
                "action": row["action"],
                "examples": examples_list
            }
        
        return result
    
    def detect_preferred_format(self) -> str:
        """
        Detect which format to use based on file existence and modification times.
        
        Returns:
            'csv' if CSV files exist and are newer, 'json' otherwise
        """
        csv_files = [self.csv_examples_file, self.csv_principles_file, self.csv_scoring_file]
        
        # Check if all CSV files exist
        csv_exist = all(os.path.exists(f) for f in csv_files)
        json_exists = os.path.exists(self.json_file)
        
        if not csv_exist and not json_exists:
            return 'json'  # Default to JSON
        
        if csv_exist and not json_exists:
            return 'csv'
        
        if json_exists and not csv_exist:
            return 'json'
        
        # Both exist, check modification times
        json_mtime = os.path.getmtime(self.json_file)
        csv_mtimes = [os.path.getmtime(f) for f in csv_files]
        newest_csv_mtime = max(csv_mtimes)
        
        # If any CSV file is newer than JSON, prefer CSV
        if newest_csv_mtime > json_mtime:
            return 'csv'
        else:
            return 'json'
    
    def get_benchmark_data(self, format_preference: str = 'auto') -> Dict[str, Any]:
        """
        Get benchmark data in the preferred format.
        
        Args:
            format_preference: 'auto', 'csv', or 'json'
            
        Returns:
            Benchmark data as JSON structure
        """
        if format_preference == 'auto':
            format_preference = self.detect_preferred_format()
        
        if format_preference == 'csv':
            try:
                return self.csv_to_json()
            except FileNotFoundError:
                print("⚠️  CSV files not found, falling back to JSON")
                format_preference = 'json'
        
        if format_preference == 'json':
            if os.path.exists(self.json_file):
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                raise FileNotFoundError(f"No benchmark files found in {self.config_dir}")
        
        raise ValueError(f"Invalid format preference: {format_preference}")


def main():
    """CLI for benchmark conversion."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert partnership benchmarks between JSON and CSV')
    parser.add_argument('action', choices=['json-to-csv', 'csv-to-json', 'detect'], 
                       help='Conversion action to perform')
    parser.add_argument('--config-dir', help='Config directory path')
    
    args = parser.parse_args()
    
    converter = BenchmarkConverter(args.config_dir)
    
    if args.action == 'json-to-csv':
        converter.json_to_csv()
    elif args.action == 'csv-to-json':
        converter.csv_to_json()
    elif args.action == 'detect':
        preferred = converter.detect_preferred_format()
        print(f"Preferred format: {preferred}")


if __name__ == "__main__":
    main() 