import pytest
from perfreporter.utils import calculate_appendage


def test_utils():
    appendage = calculate_appendage("throughput")
    assert appendage == " RPS"
    appendage = calculate_appendage("response_time")
    assert appendage == " ms"
    appendage = calculate_appendage("error_rate")
    assert appendage == " %"
