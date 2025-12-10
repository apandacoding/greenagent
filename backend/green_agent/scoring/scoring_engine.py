"""Main scoring orchestrator."""
from typing import Dict, Any, Optional
from ..execution.trace_ledger import TraceLedgerManager
from .schema_validator import SchemaValidator
from .grounding_validator import GroundingValidator
from .ndcg_scorer import NDCGScorer


class ScoringEngine:
    """Orchestrates all scoring components."""
    
    def __init__(self, trace_ledger: TraceLedgerManager):
        """
        Initialize scoring engine.
        
        Args:
            trace_ledger: Trace ledger for accessing tool results
        """
        self.trace_ledger = trace_ledger
        self.schema_validator = SchemaValidator()
        self.grounding_validator = GroundingValidator(trace_ledger)
        self.ndcg_scorer = NDCGScorer()
    
    def score_submission(
        self,
        submission: Dict[str, Any],
        traveler_brief: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Score a white agent submission.
        
        Args:
            submission: White agent output
            traveler_brief: Optional traveler preferences/brief
            
        Returns:
            Comprehensive scoring results
        """
        results = {
            'schema_validation': {},
            'grounding': {},
            'ndcg': {},
            'overall_score': 0.0
        }
        
        # Schema validation
        is_valid, errors = self.schema_validator.validate_schema(submission)
        results['schema_validation'] = {
            'is_valid': is_valid,
            'errors': errors
        }
        
        # Grounding checks
        claims = self.grounding_validator.extract_claims(submission)
        grounding_results = self.grounding_validator.validate_grounding(claims)
        results['grounding'] = grounding_results
        
        # NDCG@K for lodging ranking (if applicable)
        if traveler_brief and 'hotels' in submission:
            ranking = self.ndcg_scorer.extract_ranking_from_submission(submission)
            if ranking:
                relevance_scores = self.ndcg_scorer.calculate_relevance_scores(
                    submission.get('hotels', []),
                    traveler_brief
                )
                ndcg_at_3 = self.ndcg_scorer.calculate_ndcg_at_k(ranking, relevance_scores, k=3)
                ndcg_at_5 = self.ndcg_scorer.calculate_ndcg_at_k(ranking, relevance_scores, k=5)
                
                results['ndcg'] = {
                    'ndcg_at_3': ndcg_at_3,
                    'ndcg_at_5': ndcg_at_5,
                    'ranking': ranking
                }
        
        # Calculate overall score (weighted average)
        scores = []
        weights = []
        
        # Schema validation (must pass)
        if is_valid:
            scores.append(1.0)
        else:
            scores.append(0.0)
        weights.append(0.2)
        
        # Grounding score
        scores.append(grounding_results.get('score', 0.0))
        weights.append(0.5)
        
        # NDCG score (if available)
        if results['ndcg']:
            ndcg_score = (results['ndcg'].get('ndcg_at_3', 0) + results['ndcg'].get('ndcg_at_5', 0)) / 2
            scores.append(ndcg_score)
            weights.append(0.3)
        
        # Weighted average
        total_weight = sum(weights)
        if total_weight > 0:
            results['overall_score'] = sum(s * w for s, w in zip(scores, weights)) / total_weight
        
        return results

