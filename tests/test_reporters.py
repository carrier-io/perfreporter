import pytest
from perfreporter.reporter import Reporter

reporter = Reporter(config_file="tests/utils/config.yaml")


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
