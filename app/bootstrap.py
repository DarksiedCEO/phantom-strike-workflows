from temporalio.client import Client

from activities.core_updates import submit_signal_decision_activity
from activities.evidence import contradicting_evidence_activity, supporting_evidence_activity
from config.settings import Settings
from workflows.signal_validation import SignalValidationWorkflow


async def build_temporal_client(settings: Settings) -> Client:
    return await Client.connect(settings.temporal_server_url, namespace=settings.temporal_namespace)


def workflow_definitions() -> list[type]:
    return [SignalValidationWorkflow]


def activity_definitions() -> list:
    return [
        supporting_evidence_activity,
        contradicting_evidence_activity,
        submit_signal_decision_activity,
    ]
