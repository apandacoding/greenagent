"""Grounding checks for concrete claims."""
import re
from typing import Dict, Any, List, Tuple, Optional
from ..execution.trace_ledger import TraceLedgerManager


class GroundingValidator:
    """Validates that claims are grounded in tool results."""
    
    def __init__(self, trace_ledger: TraceLedgerManager):
        """
        Initialize grounding validator.
        
        Args:
            trace_ledger: Trace ledger containing tool call results
        """
        self.trace_ledger = trace_ledger
    
    def extract_claims(self, submission: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract all concrete claims from submission.
        
        Returns list of claims with their values and context.
        """
        claims = []
        
        # Extract from various fields
        fields_to_check = ['flights', 'hotels', 'restaurants', 'itinerary', 'cost', 'summary']
        
        for field in fields_to_check:
            if field not in submission:
                continue
            
            value = submission[field]
            
            if isinstance(value, dict):
                # Extract numeric claims (prices, times, distances)
                self._extract_from_dict(value, field, claims)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        self._extract_from_dict(item, f"{field}[{i}]", claims)
            elif isinstance(value, (int, float)):
                # Direct numeric value
                claims.append({
                    'field': field,
                    'value': value,
                    'type': 'number',
                    'context': submission
                })
        
        return claims
    
    def _extract_from_dict(self, data: Dict[str, Any], prefix: str, claims: List[Dict[str, Any]]):
        """Extract claims from a dictionary."""
        numeric_fields = ['price', 'cost', 'total_cost', 'rate_per_night', 'total_rate',
                         'duration', 'time', 'distance', 'rating', 'review_count']
        
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if key in numeric_fields and isinstance(value, (int, float)):
                claims.append({
                    'field': full_key,
                    'value': value,
                    'type': 'number',
                    'context': data
                })
            elif isinstance(value, str):
                # Extract addresses, times, dates
                if any(indicator in key.lower() for indicator in ['address', 'location', 'city']):
                    claims.append({
                        'field': full_key,
                        'value': value,
                        'type': 'address',
                        'context': data
                    })
                elif any(indicator in key.lower() for indicator in ['time', 'date', 'departure', 'arrival']):
                    claims.append({
                        'field': full_key,
                        'value': value,
                        'type': 'datetime',
                        'context': data
                    })
            elif isinstance(value, dict):
                self._extract_from_dict(value, full_key, claims)
    
    def validate_grounding(self, claims: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate that claims are grounded in tool results.
        
        Returns:
            Dictionary with validation results
        """
        traces = self.trace_ledger.get_traces()
        
        results = {
            'total_claims': len(claims),
            'grounded_claims': 0,
            'ungrounded_claims': [],
            'contradicted_claims': [],
            'exact_matches': 0,
            'score': 0.0
        }
        
        for claim in claims:
            is_grounded, match_type, contradiction = self._check_claim_grounding(claim, traces)
            
            if is_grounded:
                results['grounded_claims'] += 1
                if match_type == 'exact':
                    results['exact_matches'] += 1
            else:
                results['ungrounded_claims'].append({
                    'field': claim['field'],
                    'value': claim['value'],
                    'reason': 'No tool reference found'
                })
            
            if contradiction:
                results['contradicted_claims'].append({
                    'field': claim['field'],
                    'value': claim['value'],
                    'tool_value': contradiction
                })
        
        # Calculate score
        if results['total_claims'] > 0:
            # Base score from grounding
            grounded_ratio = results['grounded_claims'] / results['total_claims']
            
            # Bonus for exact matches
            exact_bonus = (results['exact_matches'] / results['total_claims']) * 0.2
            
            # Penalty for contradictions
            contradiction_penalty = (len(results['contradicted_claims']) / results['total_claims']) * 0.5
            
            results['score'] = max(0.0, min(1.0, grounded_ratio + exact_bonus - contradiction_penalty))
        
        return results
    
    def _check_claim_grounding(
        self,
        claim: Dict[str, Any],
        traces: List[Any]
    ) -> Tuple[bool, Optional[str], Optional[Any]]:
        """Check if a claim is grounded in traces."""
        claim_value = claim['value']
        claim_type = claim['type']
        context = claim.get('context', {})
        
        # Check for explicit reference in context
        if 'tool_reference' in context or 'reference_id' in context or 'citation' in context:
            # Try to find the referenced tool result
            reference_id = context.get('tool_reference') or context.get('reference_id')
            if reference_id:
                for trace in traces:
                    if str(trace.run_id) == str(reference_id) or hasattr(trace, 'id') and trace.id == reference_id:
                        # Check if value matches
                        return self._compare_values(claim_value, trace.return_value, claim_type)
        
        # Search all traces for matching value
        for trace in traces:
            if trace.return_value is None:
                continue
            
            # Compare values
            is_match, match_type, contradiction = self._search_in_result(
                claim_value, trace.return_value, claim_type
            )
            
            if is_match:
                return True, match_type, None
            elif contradiction:
                return False, None, contradiction
        
        return False, None, None
    
    def _search_in_result(
        self,
        claim_value: Any,
        result: Any,
        claim_type: str
    ) -> Tuple[bool, Optional[str], Optional[Any]]:
        """Search for claim value in tool result."""
        if isinstance(result, dict):
            return self._search_in_dict(claim_value, result, claim_type)
        elif isinstance(result, list):
            for item in result:
                is_match, match_type, contradiction = self._search_in_result(claim_value, item, claim_type)
                if is_match:
                    return True, match_type, None
                elif contradiction:
                    return True, None, contradiction  # Found but contradictory
        elif isinstance(result, str):
            # For string results, check if claim value appears
            if claim_type == 'address' or claim_type == 'datetime':
                if str(claim_value).lower() in str(result).lower():
                    return True, 'partial', None
        
        return False, None, None
    
    def _search_in_dict(
        self,
        claim_value: Any,
        data: Dict[str, Any],
        claim_type: str
    ) -> Tuple[bool, Optional[str], Optional[Any]]:
        """Search for claim value in dictionary."""
        for key, value in data.items():
            if claim_type == 'number' and isinstance(value, (int, float)):
                is_match, match_type = self._compare_numbers(claim_value, value)
                if is_match:
                    return True, match_type, None
                # Check for contradiction (very different value)
                if abs(claim_value - value) > max(abs(claim_value), abs(value)) * 0.1:
                    return False, None, value
            elif claim_type in ['address', 'datetime'] and isinstance(value, str):
                if str(claim_value).lower() in str(value).lower() or str(value).lower() in str(claim_value).lower():
                    return True, 'partial', None
            elif isinstance(value, (dict, list)):
                is_match, match_type, contradiction = self._search_in_result(claim_value, value, claim_type)
                if is_match:
                    return True, match_type, None
                elif contradiction:
                    return False, None, contradiction
        
        return False, None, None
    
    def _compare_values(
        self,
        claim_value: Any,
        tool_value: Any,
        claim_type: str
    ) -> Tuple[bool, Optional[str], Optional[Any]]:
        """Compare claim value with tool value."""
        if claim_type == 'number':
            return self._compare_numbers(claim_value, tool_value)
        elif claim_type in ['address', 'datetime']:
            if isinstance(tool_value, str):
                return str(claim_value).lower() in str(tool_value).lower(), 'partial', None
        else:
            # Exact match
            if claim_value == tool_value:
                return True, 'exact', None
        
        return False, None, None
    
    @staticmethod
    def _compare_numbers(claim: float, tool: float, tolerance: float = 0.01) -> Tuple[bool, str]:
        """Compare numeric values with tolerance."""
        if abs(claim - tool) < tolerance:
            return True, 'exact'
        elif abs(claim - tool) / max(abs(claim), abs(tool), 1) < 0.05:  # 5% tolerance
            return True, 'close'
        return False, None

