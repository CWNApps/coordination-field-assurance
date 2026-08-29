"""CWN Coordination Field Assurance reference harness.

This package is research/advisory software. It does not mint authority,
modify Neo4j, or claim to predict incidents.
"""

from .metrics import baseline_ce, evaluate_deployment
from .models import AgentWindow, Deployment, Surface

__all__ = ["AgentWindow", "Deployment", "Surface", "baseline_ce", "evaluate_deployment"]

