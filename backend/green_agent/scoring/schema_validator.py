"""Schema validation for white agent submissions."""
from typing import Dict, Any, List, Optional, Tuple
import json


class SchemaValidator:
    """Validates white agent output schema."""
    
    def __init__(self, required_fields: Optional[List[str]] = None):
        """
        Initialize schema validator.
        
        Args:
            required_fields: List of required field names
        """
        self.required_fields = required_fields or []
    
    def validate_schema(
        self,
        submission: Any,
        schema: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate submission against schema.
        
        Args:
            submission: White agent submission (dict, JSON string, etc.)
            schema: Optional JSON schema. If None, checks required fields.
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Parse JSON if string
        if isinstance(submission, str):
            try:
                submission = json.loads(submission)
            except json.JSONDecodeError as e:
                return False, [f"Invalid JSON: {str(e)}"]
        
        # Must be dict
        if not isinstance(submission, dict):
            return False, ["Submission must be a dictionary/object"]
        
        # Check required fields
        for field in self.required_fields:
            if field not in submission:
                errors.append(f"Missing required field: {field}")
            elif submission[field] is None:
                errors.append(f"Required field '{field}' is null")
        
        # If schema provided, validate against it
        if schema:
            # Basic schema validation (can be extended with jsonschema library)
            schema_errors = self._validate_against_schema(submission, schema)
            errors.extend(schema_errors)
        
        return len(errors) == 0, errors
    
    def _validate_against_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """Validate data against JSON schema."""
        errors = []
        
        # Check properties
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        
        for prop_name, prop_schema in properties.items():
            if prop_name in data:
                value = data[prop_name]
                prop_type = prop_schema.get('type')
                
                # Type checking
                if prop_type:
                    type_valid = self._check_type(value, prop_type)
                    if not type_valid:
                        errors.append(f"Field '{prop_name}' has wrong type. Expected {prop_type}")
            
            # Check required
            if prop_name in required and prop_name not in data:
                errors.append(f"Required field '{prop_name}' is missing")
        
        # Check for extraneous fields
        if schema.get('additionalProperties') is False:
            allowed_props = set(properties.keys())
            for prop in data.keys():
                if prop not in allowed_props:
                    errors.append(f"Extraneous field '{prop}' not in schema")
        
        return errors
    
    @staticmethod
    def _check_type(value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_map = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type is None:
            return True  # Unknown type, skip check
        
        if isinstance(expected_python_type, tuple):
            return isinstance(value, expected_python_type)
        return isinstance(value, expected_python_type)
    
    def validate_grounding_references(self, submission: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that claims have proper grounding references.
        
        Args:
            submission: White agent submission
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Look for fields that should have grounding references
        grounding_fields = ['flights', 'hotels', 'restaurants', 'activities', 'itinerary']
        
        for field in grounding_fields:
            if field in submission:
                items = submission[field]
                if isinstance(items, list):
                    for i, item in enumerate(items):
                        if isinstance(item, dict):
                            # Check for tool reference or citation
                            has_reference = any(
                                key in item for key in 
                                ['tool_reference', 'citation', 'source', 'reference_id']
                            )
                            if not has_reference:
                                errors.append(
                                    f"Item {i} in '{field}' missing grounding reference"
                                )
        
        return len(errors) == 0, errors

