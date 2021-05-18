import pytest
from json import loads
from perfreporter.post_processor import PostProcessor

post_processor = PostProcessor(config_file={})
results = {'requests':
               {'Home_Page': {'request_name': 'Home_Page', 'response_time': 1135, 'OK': 3, 'KO': 0},
                'Step1': {'request_name': 'Step1', 'response_time': 422, 'OK': 3, 'KO': 0},
                'Step2': {'request_name': 'Step2', 'response_time': 434, 'OK': 3, 'KO': 0},
                'Step3': {'request_name': 'Step3', 'response_time': 423, 'OK': 3, 'KO': 0},
                'Step4': {'request_name': 'Step4', 'response_time': 423, 'OK': 3, 'KO': 0},
                'Step5_Get_Code': {'request_name': 'Step5_Get_Code', 'response_time': 217, 'OK': 3, 'KO': 0},
                'Step5': {'request_name': 'Step5', 'response_time': 436, 'OK': 0, 'KO': 2}},
           'throughput': 0.62,
           'error_rate': 10.0}


def test_aggregate_errors():
    errors = []
    with open("tests/utils/aggregated_errors.json", "r") as f:
        error = loads(f.read())
        errors.append(error)
        errors.append(error)

    aggregated_errors = post_processor.aggregate_errors(errors)
    assert aggregated_errors["Step5_GET_200"]["Error count"] == 4


def test_calculate_thresholds():
    thresholds = post_processor.calculate_thresholds(results)
    assert len(thresholds) == 9
    for i in range(3):
        assert thresholds[i]["status"] == "FAILED"
    for i in range(3, 9):
        assert thresholds[i]["status"] == "PASSED"



