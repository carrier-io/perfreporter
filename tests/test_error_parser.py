import pytest
from perfreporter.error_parser import ErrorLogParser


def test_error_parser():
    args = {"error_logs": "tests/utils/", "simulation": "error"}
    error_parser = ErrorLogParser(args)
    aggregated_errors = error_parser.parse_errors()
    assert aggregated_errors["Step5_GET_200"]["Error count"] == 5
