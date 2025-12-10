"""Normalization utilities for tool plans."""
import re
from typing import Any, Dict, List
from datetime import datetime


class PlanNormalizer:
    """Normalizes tool plans with safe transformations."""
    
    @staticmethod
    def normalize_string(s: str) -> str:
        """Normalize a string value."""
        if not isinstance(s, str):
            return s
        
        # Trim whitespace
        s = s.strip()
        
        # Normalize arrows
        s = re.sub(r'[→⇒]', '>', s)
        
        # Remove stray markdown (but preserve structure)
        # Remove markdown links but keep text
        s = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', s)
        # Remove markdown bold/italic markers but keep text
        s = re.sub(r'[*_]{1,2}([^*_]+)[*_]{1,2}', r'\1', s)
        
        return s
    
    @staticmethod
    def normalize_date(date_str: str) -> str:
        """
        Normalize date string to YYYY-MM-DD format.
        
        Examples:
            "Dec 2" -> "2025-12-02" (assumes current year)
            "2024-12-02" -> "2024-12-02"
            "12/02/2024" -> "2024-12-02"
        """
        if not isinstance(date_str, str):
            return date_str
        
        date_str = date_str.strip()
        
        # Already in YYYY-MM-DD format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str
        
        # Try to parse common formats
        try:
            # MM/DD/YYYY or M/D/YYYY
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    month, day, year = parts
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            # Month name format (e.g., "Dec 2", "December 2")
            month_names = {
                'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
            }
            
            # Try to match "Month Day" or "Mon Day"
            match = re.match(r'([a-z]+)\s+(\d+)', date_str.lower())
            if match:
                month_name, day = match.groups()
                month = month_names.get(month_name[:3])
                if month:
                    # Assume current year (or you could make this configurable)
                    year = datetime.now().year
                    return f"{year}-{month}-{day.zfill(2)}"
        except Exception:
            pass
        
        # Return as-is if we can't normalize
        return date_str
    
    @staticmethod
    def normalize_value(value: Any) -> Any:
        """Normalize a value based on its type."""
        if isinstance(value, str):
            # Try date normalization first
            normalized = PlanNormalizer.normalize_date(value)
            if normalized != value:
                return normalized
            # Otherwise string normalization
            return PlanNormalizer.normalize_string(value)
        elif isinstance(value, dict):
            return {k: PlanNormalizer.normalize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [PlanNormalizer.normalize_value(item) for item in value]
        else:
            return value
    
    @staticmethod
    def normalize_plan(plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize a tool plan.
        
        Args:
            plan: List of tool call dictionaries
            
        Returns:
            Normalized plan
        """
        normalized = []
        for call in plan:
            normalized_call = {}
            for key, value in call.items():
                normalized_key = PlanNormalizer.normalize_string(key) if isinstance(key, str) else key
                normalized_value = PlanNormalizer.normalize_value(value)
                normalized_call[normalized_key] = normalized_value
            normalized.append(normalized_call)
        
        return normalized

