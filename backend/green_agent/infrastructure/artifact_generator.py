"""Artifact generator for exporting evaluation results."""
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from ..execution.trace_ledger import TraceLedgerManager
from ..infrastructure.controller import GreenAgentController


class ArtifactGenerator:
    """Generates artifacts for evaluation runs."""
    
    def __init__(
        self,
        controller: GreenAgentController,
        trace_ledger: TraceLedgerManager
    ):
        """
        Initialize artifact generator.
        
        Args:
            controller: Green Agent controller
            trace_ledger: Trace ledger manager
        """
        self.controller = controller
        self.trace_ledger = trace_ledger
    
    def generate_metrics_json(
        self,
        scoring_results: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate metrics.json artifact.
        
        Args:
            scoring_results: Scoring results from evaluation
            output_path: Optional file path to save to
            
        Returns:
            Metrics dictionary
        """
        metrics = {
            'run_id': self.controller.get_run_id(),
            'seed': self.controller.get_seed(),
            'scenario_id': self.controller.get_scenario_id(),
            'timestamp': datetime.now().isoformat(),
            'scores': {
                'overall': scoring_results.get('overall_score', 0.0),
                'schema_validation': scoring_results.get('schema_validation', {}).get('is_valid', False),
                'grounding': scoring_results.get('grounding', {}).get('score', 0.0),
                'ndcg_at_3': scoring_results.get('ndcg', {}).get('ndcg_at_3', None),
                'ndcg_at_5': scoring_results.get('ndcg', {}).get('ndcg_at_5', None)
            },
            'details': scoring_results
        }
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(metrics, f, indent=2, default=str)
        
        return metrics
    
    def generate_leaderboard_row(
        self,
        scoring_results: Dict[str, Any],
        agent_name: str = "White Agent",
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate leaderboard-row.json artifact.
        
        Args:
            scoring_results: Scoring results
            agent_name: Name of the agent being evaluated
            output_path: Optional file path to save to
            
        Returns:
            Leaderboard row dictionary
        """
        row = {
            'agent_name': agent_name,
            'run_id': self.controller.get_run_id(),
            'seed': self.controller.get_seed(),
            'scenario_id': self.controller.get_scenario_id(),
            'timestamp': datetime.now().isoformat(),
            'overall_score': scoring_results.get('overall_score', 0.0),
            'scores': {
                'schema_validation': scoring_results.get('schema_validation', {}).get('is_valid', False),
                'grounding': scoring_results.get('grounding', {}).get('score', 0.0),
                'ndcg_at_3': scoring_results.get('ndcg', {}).get('ndcg_at_3', None),
                'ndcg_at_5': scoring_results.get('ndcg', {}).get('ndcg_at_5', None)
            }
        }
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(row, f, indent=2, default=str)
        
        return row
    
    def export_tool_results_bundle(
        self,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Export tool results bundle.
        
        Args:
            output_path: Optional file path to save to
            
        Returns:
            Tool results bundle dictionary
        """
        traces = self.trace_ledger.get_traces()
        
        bundle = {
            'run_id': self.controller.get_run_id(),
            'seed': self.controller.get_seed(),
            'timestamp': datetime.now().isoformat(),
            'tool_calls': [
                {
                    'tool_name': trace.tool_name,
                    'arguments': trace.arguments,
                    'return_value': trace.return_value,
                    'return_value_hash': trace.return_value_hash,
                    'timestamp': trace.timestamp.isoformat(),
                    'execution_time_ms': trace.execution_time_ms
                }
                for trace in traces
            ]
        }
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(bundle, f, indent=2, default=str)
        
        return bundle
    
    def export_all_artifacts(
        self,
        scoring_results: Dict[str, Any],
        output_dir: str,
        agent_name: str = "White Agent",
        white_agent_output: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Export all artifacts for a run.
        
        Args:
            scoring_results: Scoring results
            output_dir: Output directory
            agent_name: Agent name
            white_agent_output: Optional white agent output to export
            
        Returns:
            Dictionary mapping artifact type to file path
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        artifacts = {}
        
        # Metrics
        metrics_path = output_path / "metrics.json"
        self.generate_metrics_json(scoring_results, str(metrics_path))
        artifacts['metrics'] = str(metrics_path)
        
        # Leaderboard row
        leaderboard_path = output_path / "leaderboard-row.json"
        self.generate_leaderboard_row(scoring_results, agent_name, str(leaderboard_path))
        artifacts['leaderboard'] = str(leaderboard_path)
        
        # Trace ledger
        ledger_path = output_path / "trace_ledger.json"
        self.trace_ledger.export_to_json(str(ledger_path))
        artifacts['trace_ledger'] = str(ledger_path)
        
        # Tool results bundle
        bundle_path = output_path / "tool_results_bundle.json"
        self.export_tool_results_bundle(str(bundle_path))
        artifacts['tool_results'] = str(bundle_path)
        
        # White agent output
        if white_agent_output:
            output_file = output_path / "white_agent_output.json"
            with open(output_file, 'w') as f:
                json.dump(white_agent_output, f, indent=2, default=str)
            artifacts['white_agent_output'] = str(output_file)
        
        return artifacts

