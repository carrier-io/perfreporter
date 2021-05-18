import pytest
from perfreporter.jtl_parser import JTLParser


def test_parse_jtl():
    jtl_parser = JTLParser()
    results = jtl_parser.parse_jtl(log_file="tests/utils/jmeter.jtl")
    assert results["throughput"] == 0.62
    assert results["error_rate"] == 10.0
    assert all(key in list(results["requests"].keys()) for key in ['Home_Page', 'Step1', 'Step2', 'Step3', 'Step4',
                                                                   'Step5_Get_Code', 'Step5'])
