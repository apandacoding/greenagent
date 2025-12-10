"""NDCG@K scorer for lodging ranking."""
import math
from typing import List, Dict, Any, Optional


class NDCGScorer:
    """Calculates NDCG@K for lodging ranking."""
    
    @staticmethod
    def calculate_ndcg_at_k(
        predicted_ranking: List[str],
        relevance_scores: Dict[str, float],
        k: int = 5
    ) -> float:
        """
        Calculate NDCG@K.
        
        Args:
            predicted_ranking: List of lodging IDs in predicted order
            relevance_scores: Dictionary mapping lodging ID to relevance score
            k: Cutoff point for NDCG
            
        Returns:
            NDCG@K score (0 to 1)
        """
        # Calculate DCG@K
        dcg = NDCGScorer._calculate_dcg(predicted_ranking[:k], relevance_scores)
        
        # Calculate IDCG@K (ideal ranking)
        ideal_ranking = sorted(
            relevance_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        ideal_ids = [item[0] for item in ideal_ranking[:k]]
        idcg = NDCGScorer._calculate_dcg(ideal_ids, relevance_scores)
        
        # Normalize
        if idcg == 0:
            return 0.0
        
        return dcg / idcg
    
    @staticmethod
    def _calculate_dcg(ranking: List[str], relevance_scores: Dict[str, float]) -> float:
        """Calculate Discounted Cumulative Gain."""
        dcg = 0.0
        
        for i, item_id in enumerate(ranking):
            position = i + 1
            relevance = relevance_scores.get(item_id, 0.0)
            
            # DCG formula: rel_i / log2(i + 1)
            dcg += relevance / math.log2(position + 1)
        
        return dcg
    
    @staticmethod
    def calculate_relevance_scores(
        lodging_items: List[Dict[str, Any]],
        traveler_brief: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calculate relevance scores for lodging items based on traveler brief.
        
        Args:
            lodging_items: List of lodging dictionaries
            traveler_brief: Traveler preferences/brief
            
        Returns:
            Dictionary mapping lodging ID to relevance score
        """
        scores = {}
        
        for item in lodging_items:
            item_id = item.get('id') or item.get('name') or str(hash(str(item)))
            score = NDCGScorer._calculate_item_relevance(item, traveler_brief)
            scores[item_id] = score
        
        return scores
    
    @staticmethod
    def _calculate_item_relevance(
        item: Dict[str, Any],
        brief: Dict[str, Any]
    ) -> float:
        """Calculate relevance score for a single lodging item."""
        score = 0.0
        max_score = 0.0
        
        # Amenities match (0-0.3)
        if 'amenities' in brief:
            required_amenities = brief['amenities']
            item_amenities = item.get('amenities', [])
            if isinstance(item_amenities, str):
                item_amenities = [a.strip() for a in item_amenities.split(',')]
            
            matched = sum(1 for a in required_amenities if a in item_amenities)
            amenity_score = (matched / len(required_amenities)) * 0.3 if required_amenities else 0
            score += amenity_score
            max_score += 0.3
        
        # Budget fit (0-0.3)
        if 'budget' in brief and 'price' in item:
            budget = brief['budget']
            price = item.get('price') or item.get('rate_per_night') or item.get('total_rate')
            if price and budget:
                try:
                    price_val = float(price) if isinstance(price, (int, float)) else float(str(price).replace('$', '').replace(',', ''))
                    budget_val = float(budget) if isinstance(budget, (int, float)) else float(str(budget).replace('$', '').replace(',', ''))
                    
                    if price_val <= budget_val:
                        # Within budget - full score
                        budget_score = 0.3
                    elif price_val <= budget_val * 1.1:
                        # Within 10% - partial score
                        budget_score = 0.15
                    else:
                        # Over budget
                        budget_score = 0.0
                    
                    score += budget_score
                except (ValueError, TypeError):
                    pass
            max_score += 0.3
        
        # Distance from activities (0-0.2)
        if 'activity_location' in brief and 'location' in item:
            # Simplified distance scoring (would need actual distance calculation)
            score += 0.1  # Placeholder
            max_score += 0.2
        
        # Policies match (0-0.2)
        if 'policies' in brief:
            # Check cancellation, pet policy, etc.
            score += 0.1  # Placeholder
            max_score += 0.2
        
        # Normalize to 0-1
        if max_score > 0:
            return min(1.0, score / max_score)
        return 0.0
    
    @staticmethod
    def extract_ranking_from_submission(submission: Dict[str, Any]) -> List[str]:
        """
        Extract lodging ranking from white agent submission.
        
        Args:
            submission: White agent output
            
        Returns:
            List of lodging IDs in ranked order
        """
        ranking = []
        
        # Look for hotels/lodging in submission
        if 'hotels' in submission:
            hotels = submission['hotels']
            if isinstance(hotels, list):
                for hotel in hotels:
                    hotel_id = hotel.get('id') or hotel.get('name') or hotel.get('hotel_id')
                    if hotel_id:
                        ranking.append(str(hotel_id))
        
        # Also check itinerary
        if 'itinerary' in submission:
            itinerary = submission['itinerary']
            if isinstance(itinerary, dict) and 'lodging' in itinerary:
                lodging = itinerary['lodging']
                if isinstance(lodging, list):
                    for item in lodging:
                        item_id = item.get('id') or item.get('name')
                        if item_id and item_id not in ranking:
                            ranking.append(str(item_id))
        
        return ranking

