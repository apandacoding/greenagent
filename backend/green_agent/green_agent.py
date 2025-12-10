"""Main Green Agent orchestrator."""
from typing import Dict, Any, Optional, List
import logging

from .infrastructure.controller import GreenAgentController
from .infrastructure.isolator import get_isolator
from .tools.tool_registry import ToolRegistry, get_registry
from .validation.plan_validator import PlanValidator
from .execution.tool_runner import ToolRunner
from .execution.trace_ledger import TraceLedgerManager
from .scoring.scoring_engine import ScoringEngine
from .environment.sandbox import Sandbox

logger = logging.getLogger(__name__)


class GreenAgent:
    """Main Green Agent orchestrator for deterministic benchmarking."""
    
    def __init__(
        self,
        seed: Optional[int] = None,
        scenario_id: Optional[str] = None,
        use_fixtures: bool = True,
        disable_network: bool = True
    ):
        """
        Initialize Green Agent.
        
        Args:
            seed: Seed for deterministic execution
            scenario_id: Optional scenario identifier
            use_fixtures: Whether to use fixtures (True) or real APIs (False)
            disable_network: Whether to disable network in sandbox mode
        """
        # Initialize controller
        self.controller = GreenAgentController(seed, scenario_id)
        
        # Initialize components
        self.tool_registry = get_registry()
        self.plan_validator = PlanValidator(self.tool_registry)
        self.isolator = get_isolator()
        self.sandbox = Sandbox(seed, disable_network)
        
        # Tool runner and trace ledger
        self.tool_runner = ToolRunner(self.controller, self.tool_registry, use_fixtures)
        self.trace_ledger = self.tool_runner.get_trace_ledger()
        
        # Scoring engine
        self.scoring_engine = ScoringEngine(self.trace_ledger)
        
        # Execution state
        self._run_id: Optional[str] = None
    
    def start_run(self, run_id: Optional[str] = None) -> str:
        """
        Start a new evaluation run.
        
        Args:
            run_id: Optional run ID
            
        Returns:
            Run ID for this execution
        """
        # Reset isolation
        self.isolator.reset()
        
        # Initialize trace ledger
        self._run_id = self.controller.start_run(run_id)
        self.trace_ledger.initialize(self._run_id)
        
        logger.info(f"Started Green Agent run: {self._run_id} (seed={self.controller.get_seed()})")
        
        return self._run_id
    
    def register_tool(self, tool_name: str, tool_function):
        """Register a tool function for execution."""
        self.tool_runner.register_tool(tool_name, tool_function)
    
    def validate_and_execute_plan(
        self,
        plan: Any
    ) -> Dict[str, Any]:
        """
        Validate and execute a tool plan.
        
        Args:
            plan: Tool execution plan (JSON-serializable list)
            
        Returns:
            Execution results with validation and execution status
        """
        # Validate plan
        is_valid, error_msg, normalized_plan = self.plan_validator.validate_and_normalize(plan)
        
        if not is_valid:
            return {
                'success': False,
                'error': error_msg,
                'executed': False
            }
        
        # Execute plan in sandbox
        with self.sandbox:
            results = self.tool_runner.execute_plan(normalized_plan)
        
        # Check for errors
        has_errors = any(not r.get('success', False) for r in results)
        
        return {
            'success': not has_errors,
            'plan': normalized_plan,
            'results': results,
            'executed': True,
            'trace_ledger': self.trace_ledger.get_traces()
        }
    
    def evaluate_submission(
        self,
        submission: Dict[str, Any],
        traveler_brief: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate white agent submission.
        
        Args:
            submission: White agent output
            traveler_brief: Optional traveler preferences
            
        Returns:
            Comprehensive evaluation results
        """
        # Run scoring
        scoring_results = self.scoring_engine.score_submission(submission, traveler_brief)
        
        # Get trace ledger
        ledger = self.trace_ledger.get_ledger()
        
        return {
            'run_id': self._run_id,
            'seed': self.controller.get_seed(),
            'scenario_id': self.controller.get_scenario_id(),
            'scoring': scoring_results,
            'trace_ledger': ledger.model_dump(mode='json') if ledger else None
        }
    
    def get_trace_ledger(self) -> TraceLedgerManager:
        """Get trace ledger manager."""
        return self.trace_ledger
    
    def reset(self, seed: Optional[int] = None):
        """Reset Green Agent state for new run."""
        if seed is not None:
            self.controller.reset(seed)
        else:
            self.controller.reset()
        
        self.trace_ledger.clear()
        self.isolator.reset()
        self._run_id = None
        
        logger.info("Green Agent reset")
    
    def export_artifacts(self, output_dir: str) -> Dict[str, str]:
        """
        Export all artifacts for a run.
        
        Args:
            output_dir: Directory to save artifacts
            
        Returns:
            Dictionary mapping artifact type to file path
        """
        import os
        from pathlib import Path
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        artifacts = {}
        
        # Export trace ledger
        ledger_path = output_path / "trace_ledger.json"
        self.trace_ledger.export_to_json(str(ledger_path))
        artifacts['trace_ledger'] = str(ledger_path)
        
        # Export metrics (placeholder - would include scoring results)
        metrics_path = output_path / "metrics.json"
        # TODO: Generate comprehensive metrics JSON
        artifacts['metrics'] = str(metrics_path)
        
        return artifacts

