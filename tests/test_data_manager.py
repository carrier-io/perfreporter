import pytest
import requests_mock
import os
from perfreporter.data_manager import DataManager
import tests.utils.constants as c
from perfreporter.junit_reporter import JUnit_reporter


galloper_url = "http://example"
token = "test"
project_id = 1
data_manager = DataManager(c.ARGS, galloper_url, token, project_id)


def test_compare_with_baseline():
    performance_degradation_rate, compare_with_baseline = data_manager.compare_with_baseline(c.BASELINE, c.TEST_DATA)
    print(performance_degradation_rate)
    print(compare_with_baseline)
    failed_requests = []
    for each in compare_with_baseline:
        failed_requests.append(each["request_name"])
    assert performance_degradation_rate == 62.5
    assert all(req in ['Step1', 'Step2', 'Step3', 'Step4', 'Step5_Get_Code'] for req in failed_requests)


def test_get_thresholds_and_create_junit_report():
    with requests_mock.Mocker() as mock:
        mock.get(f"{galloper_url}/api/v1/thresholds/{project_id}/backend?name={c.ARGS['simulation']}&"
                 f"environment={c.ARGS['env']}&order=asc", json=c.THRESHOLDS, status_code=200)
        mock.get(c.ALL_METRICS_REQUEST, json=c.ALL_METRICS_RESPONSE)
        mock.get(c.TP_REQUEST, json=c.TP_RESPONSE)
        total_checked, missed_threshold_rate, compare_with_thresholds = data_manager.get_thresholds(test=c.TEST_DATA,
                                                                                                    add_green=True)
        failed_requests = []
        print(missed_threshold_rate)
        print(compare_with_thresholds)
        for each in compare_with_thresholds:
            if each["threshold"] != "green":
                failed_requests.append(each["request_name"])
        assert missed_threshold_rate == 40.0
        assert all(req in ['Step1', 'Step5', 'All', 'all'] for req in failed_requests)

        JUnit_reporter.create_report(compare_with_thresholds, "1")
        assert os.path.exists("/tmp/junit_report_1.xml")
        os.remove("/tmp/junit_report_1.xml")


def test_write_comparison_data_to_influx():
    with requests_mock.Mocker() as mock:
        mock.get(c.user_count_request, json=c.user_count_response)
        mock.get(c.total_requests_count_request, json=c.total_requests_count_response)
        mock.get(c.request_names_request, json=c.request_names_response)
        mock.get(c.first_request, json=c.first_response)
        mock.get(c.last_request, json=c.last_response)
        mock.get(c.response_time_request.format("Home_Page"), json=c.home_page_response_time_response)
        mock.get(c.response_time_request.format("Step1"), json=c.step1_response_time_response)
        mock.get(c.response_time_request.format("Step2"), json=c.step2_response_time_response)
        mock.get(c.response_time_request.format("Step3"), json=c.step3_response_time_response)
        mock.get(c.response_time_request.format("Step4"), json=c.step4_response_time_response)
        mock.get(c.response_time_request.format("Step5"), json=c.step5_response_time_response)
        mock.get(c.response_time_request.format("Step5_Get_Code"), json=c.step5_get_code_response_time_response)

        for each in ["Home_Page", "Step1", "Step2", "Step3", "Step4", "Step5", "Step5_Get_Code"]:
            mock.get(c.methods_request.format(each), json=c.methods_response)
            mock.get(c.ko_count_request.format(each), json=c.empty_response)
            if each == "Step5":
                mock.get(c.ok_count_request.format(each), json=c.step5_total_response)
                mock.get(c.total_request.format(each), json=c.step5_total_response)
            else:
                mock.get(c.ok_count_request.format(each), json=c.total_response)
                mock.get(c.total_request.format(each), json=c.total_response)

        # mock status codes
        for each in ["Home_Page", "Step1", "Step2", "Step3", "Step4", "Step5", "Step5_Get_Code"]:
            mock.get(c.nan_status_code_request.format(each), json=c.empty_response)
            for code in [1, 2, 3, 4, 5]:
                if code == 2:
                    if each == "Step5":
                        mock.get(c.status_code_request.format(each, code), json=c.step5_total_response)
                    else:
                        mock.get(c.status_code_request.format(each, code), json=c.total_response)
                else:
                    mock.get(c.status_code_request.format(each, code), json=c.empty_response)

        mock.register_uri(requests_mock.POST, "http://localhost:8086/write", status_code=204)
        users_count, duration, response_times = data_manager.write_comparison_data_to_influx()

        assert users_count == 1
        assert duration == 29
        assert response_times["min"] == 206.0
        assert response_times["max"] == 1121.0
        assert response_times["mean"] == 401.0
        assert response_times["pct50"] == 416
        assert response_times["pct75"] == 420
        assert response_times["pct90"] == 424
        assert response_times["pct95"] == 461
        assert response_times["pct99"] == 989


def test_get_baseline():
    with requests_mock.Mocker() as mock:
        mock.get(f"{galloper_url}/api/v1/baseline/{project_id}?test_name=Flood&env=demo", json={"baseline": c.BASELINE})
        baseline = data_manager.get_baseline()
        assert baseline == c.BASELINE


def test_get_last_build():
    with requests_mock.Mocker() as mock:
        mock.get(c.last_build_request, json=c.last_build_response)
        last_build = data_manager.get_last_build()
        assert last_build == c.last_build
