import pytest
import hashlib
import requests_mock
from perfreporter.reporter import Reporter
from perfreporter.ado_reporter import ADOReporter
import tests.utils.constants as c

reporter = Reporter(config_file="tests/utils/config.yaml")

ado_reporter = ADOReporter(ado_config={"org": "my_org", "project": "my_project", "pat": "my_pat", "team": "my_team"},
                           args=c.ARGS)


def test_parse_config_file():
    args = {}
    rp_service, jira_service = reporter.parse_config_file(args)
    assert rp_service is not None
    assert jira_service is not None
    assert rp_service.rp_url == "https://rp.com"
    assert jira_service.url == "https://jira.com"
    assert not jira_service.valid


def test_get_jira_service():
    args = {}
    jira_core_config = {
                    "jira_url": "https://jira.com",
                    "jira_login": "my_login",
                    "jira_password": "my_password",
                    "jira_project": "my_project",
                    "issue_type": "Bug"
                }
    jira_additional_config = {
                "check_functional_errors": "True",
                "check_performance_degradation": "True",
                "check_missed_thresholds": "True",
                "performance_degradation_rate": 20,
                "missed_thresholds_rate": 50,
                "jira_labels": "performance, api",
                "jira_watchers": "",
                "jira_epic_key": ""
            }
    jira_service = reporter.get_jira_service(args, jira_core_config, jira_additional_config)
    assert jira_service is not None
    assert jira_service.url == "https://jira.com"
    assert not jira_service.valid


def test_get_rp_service():
    args = {}
    rp_core_config = {
                    "rp_host": "https://rp.com",
                    "rp_token": "my_secret_token",
                    "rp_project": "my_project"
                }
    rp_additional_config = {
            "rp_launch_name": "carrier",
            "check_functional_errors": "True",
            "check_performance_degradation": "True",
            "check_missed_thresholds": "True",
            "performance_degradation_rate": 20,
            "missed_thresholds_rate": 50
        }
    rp_service = reporter.get_rp_service(args, rp_core_config, rp_additional_config)
    assert rp_service is not None
    assert rp_service.rp_url == "https://rp.com"


def test_jira_create_functional_error_description():
    args = {}
    rp_service, jira_service = reporter.parse_config_file(args)
    functional_error_description = jira_service.create_functional_error_description(c.error, c.ARGS)
    assert len(functional_error_description) == 2361
    for each in ["*Request name*: Step5", "*HTTP Method*: GET", "*Request URL*: https://challengers.flood.io/done",
                 "*Request headers*: {code}Connection:keep-alive", "*Error count*: 2;", "*Response code*: 200;"]:
        assert each in functional_error_description


def test_jira_create_performance_degradation_description():
    args = {}
    rp_service, jira_service = reporter.parse_config_file(args)
    performance_degradation_description = jira_service.create_performance_degradation_description(c.baseline_rate,
                                                                                                  c.compare_with_baseline,
                                                                                                  c.ARGS)
    assert len(performance_degradation_description) == 528
    for each in ["Performance degradation in test: Flood", "Test performance degradation is 62.5%",
                 "\"Step4\" reached 420 ms by pct95. Baseline 415 ms.", "\"Step3\" reached 425 ms by pct95.",
                 "\"Step2\" reached 431 ms by pct95.", "\"Step1\" reached 428 ms by pct95."]:
        assert each in performance_degradation_description


def test_jira_create_missed_thresholds_description():
    args = {}
    rp_service, jira_service = reporter.parse_config_file(args)
    missed_thresholds_description = jira_service.create_missed_thresholds_description(c.threshold_rate,
                                                                                      c.compare_with_thresholds,
                                                                                      c.ARGS)
    assert len(missed_thresholds_description) == 582
    for each in ["Missed thresholds in test: Flood", "Percentage of requests exceeding the threshold was 40.0%",
                 "\"All\" error_rate % with value 5.26 % exceeded threshold of 5.0 %",
                 "\"Step1\" response_time ms with value 428 ms exceeded threshold of 200.0 ms"]:
        assert each in missed_thresholds_description


def test_jira_get_functional_error_hash_code():
    args = {}
    rp_service, jira_service = reporter.parse_config_file(args)
    item_hash_code = jira_service.get_functional_error_hash_code(c.error, c.ARGS)
    assert item_hash_code == hashlib.sha256(c.error_string.strip().encode('utf-8')).hexdigest()


def test_rp_create_project():
    args = {}
    rp_service, jira_service = reporter.parse_config_file(args)
    with requests_mock.Mocker() as mock:
        mock.get(c.rp_get_project_request, status_code=404)
        mock.post(c.rp_url, status_code=204)
        rp_service.create_project()
        assert mock.call_count == 2


def test_rp_html_decode():
    args = {}
    rp_service, jira_service = reporter.parse_config_file(args)
    decoded_string = rp_service.html_decode(c.html_str)
    assert decoded_string == c.decoded_html_string


def test_ado_create_functional_error_description():
    functional_error_description = ado_reporter.create_functional_error_description(c.error, c.ARGS)
    assert len(functional_error_description) == 3214
    for each in ["<strong>Request name</strong>: Step5<br>", "HTTP Method</strong>: GET",
                 "<strong>Request URL</strong>: https://challengers.flood.io/done<br>",
                 "<strong>Request headers</strong>: <br>Connection:keep-alive<br>Accept-Language:ru-RU,ru;q=0.8"]:
        assert each in functional_error_description


def test_ado_create_performance_degradation_description():
    performance_degradation_description = ado_reporter.create_performance_degradation_description(c.baseline_rate,
                                                                                                  c.compare_with_baseline,
                                                                                                  "123",
                                                                                                  c.ARGS)
    assert len(performance_degradation_description) == 434
    for each in ["Test performance degradation is 62.5% compared to the baseline",
                 "\"Step5_Get_Code\" reached 208 ms by pct95. Baseline 199 ms.",
                 "\"Step4\" reached 420 ms by pct95. Baseline 415 ms.", "\"Step3\" reached 425 ms by pct95."]:
        assert each in performance_degradation_description


def test_ado_create_missed_thresholds_description():
    missed_thresholds_description = ado_reporter.create_missed_thresholds_description(c.threshold_rate,
                                                                                      c.compare_with_thresholds,
                                                                                      c.ARGS)
    assert len(missed_thresholds_description) == 871
    for each in ["Percentage of requests exceeding the threshold was 40.0%.",
                 "\"All\" error_rate % with value 5.26 % exceeded threshold of 5.0 %",
                 "\"Step1\" response_time ms with value 428 ms exceeded threshold of 200.0 ms"]:
        assert each in missed_thresholds_description


def test_ado_get_functional_error_hash_code():
    item_hash_code = ado_reporter.get_functional_error_hash_code(c.error, c.ARGS)
    assert item_hash_code == hashlib.sha256(c.error_string.strip().encode('utf-8')).hexdigest()
