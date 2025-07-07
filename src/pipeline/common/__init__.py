"""Utility functions for the flows and tasks."""

from prefect.runtime import flow_run


def generate_flow_run_name() -> str:
    flow_name = flow_run.flow_name
    parameters = flow_run.parameters
    username = parameters["watchlist_parameters"].username
    return f"{flow_name}-{username}"
