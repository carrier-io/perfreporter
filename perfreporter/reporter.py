import sys
import yaml

from perfreporter.report_portal import ReportPortal
from perfreporter.jira_wrapper import JiraWrapper


PATH_TO_CONFIG = "/tmp/config.yaml"


class Reporter(object):

    @staticmethod
    def parse_config_file(args):
        report_types = []
        try:
            with open(PATH_TO_CONFIG, "rb") as f:
                config = yaml.load(f.read())
            if config:
                report_types = list(config.keys())
        except:
            return None, None

        rp_service = None
        if 'reportportal' in report_types:
            rp_project = config['reportportal'].get("rp_project_name")
            rp_url = config['reportportal'].get("rp_host")
            rp_token = config['reportportal'].get("rp_token")
            rp_launch_name = config['reportportal'].get("rp_launch_name")
            check_functional_errors = config['reportportal'].get("check_functional_errors", 'False')
            check_performance_degradation = config['reportportal'].get("check_performance_degradation", 'False')
            check_missed_thresholds = config['reportportal'].get("check_missed_thresholds", 'False')
            performance_degradation_rate = config['reportportal'].get("performance_degradation_rate", 20)
            missed_thresholds_rate = config['reportportal'].get("missed_thresholds_rate", 50)
            if not all([rp_project, rp_url, rp_token, rp_launch_name]):
                print("ReportPortal configuration values missing, proceeding "
                      "without report portal integration ")
            else:
                rp_service = ReportPortal(args, rp_url, rp_token, rp_project, rp_launch_name, check_functional_errors,
                                          check_performance_degradation, check_missed_thresholds,
                                          performance_degradation_rate, missed_thresholds_rate)
                rp_service.my_error_handler(sys.exc_info())

        jira_service = None
        if 'jira' in report_types:
            jira_url = config['jira'].get("url", None)
            jira_user = config['jira'].get("username", None)
            jira_pwd = config['jira'].get("password", None)
            jira_project = config['jira'].get("jira_project", None)
            jira_assignee = config['jira'].get("assignee", None)
            jira_issue_type = config['jira'].get("issue_type", 'Bug')
            jira_labels = config['jira'].get("labels", '')
            jira_watchers = config['jira'].get("watchers", '')
            jira_epic_key = config['jira'].get("epic_link", None)
            check_functional_errors = config['jira'].get("check_functional_errors", 'False')
            check_performance_degradation = config['jira'].get("check_performance_degradation", 'False')
            check_missed_thresholds = config['jira'].get("check_missed_thresholds", 'False')
            performance_degradation_rate = config['jira'].get("performance_degradation_rate", 20)
            missed_thresholds_rate = config['jira'].get("missed_thresholds_rate", 50)
            if not (jira_url and jira_user and jira_pwd and jira_project and jira_assignee):
                print("Jira configuration values missing, proceeding without Jira")
            else:
                jira_service = JiraWrapper(args, jira_url, jira_user, jira_pwd, jira_project, jira_assignee,
                                           check_functional_errors, check_performance_degradation,
                                           check_missed_thresholds, performance_degradation_rate,
                                           missed_thresholds_rate, jira_issue_type, jira_labels, jira_watchers,
                                           jira_epic_key)

        return rp_service, jira_service

    def get_jira_service(self, args, jira_config, jira_additional_config):
        for each in ["jira_url", "jira_login", "jira_password", "jira_project"]:
            if not jira_config.get(each):
                print("Jira configuration values missing, proceeding without Jira")
                return None
        jira_service = JiraWrapper(args, jira_config["jira_url"], jira_config["jira_login"],
                                   jira_config["jira_password"], jira_config["jira_project"],
                                   jira_additional_config.get("assignee", jira_config["jira_login"]),
                                   jira_additional_config.get("check_functional_errors", False),
                                   jira_additional_config.get("check_performance_degradation", False),
                                   jira_additional_config.get("check_missed_thresholds", False),
                                   jira_additional_config.get("performance_degradation_rate", 20),
                                   jira_additional_config.get("missed_thresholds_rate", 50),
                                   jira_config.get("issue_type", "Bug"), jira_additional_config.get("jira_labels", ""),
                                   jira_additional_config.get("jira_watchers", ""),
                                   jira_additional_config.get("jira_epic_key", None))
        return jira_service

    def get_rp_service(self, args, rp_config, rp_additional_config):
        for each in ["rp_host", "rp_token", "rp_project"]:
            if not rp_config.get(each):
                print("RP configuration values missing, proceeding without RP")
                return None
        rp_project = rp_config['rp_project']
        rp_url = rp_config['rp_host']
        rp_token = rp_config['rp_token']
        rp_launch_name = rp_additional_config.get('rp_launch_name', 'carrier')
        check_functional_errors = rp_additional_config.get('check_functional_errors', 'False')
        check_performance_degradation = rp_additional_config.get('check_performance_degradation', 'False')
        check_missed_thresholds = rp_additional_config.get('check_missed_thresholds', 'False')
        performance_degradation_rate = rp_additional_config.get('performance_degradation_rate', 20)
        missed_thresholds_rate = rp_additional_config.get('missed_thresholds_rate', 50)
        if not all([rp_project, rp_url, rp_token, rp_launch_name]):
            print("ReportPortal configuration values missing, proceeding "
                  "without report portal integration ")
            return None
        else:
            rp_service = ReportPortal(args, rp_url, rp_token, rp_project, rp_launch_name, check_functional_errors,
                                      check_performance_degradation, check_missed_thresholds,
                                      performance_degradation_rate, missed_thresholds_rate)
            rp_service.my_error_handler(sys.exc_info())
        return rp_service

    @staticmethod
    def report_errors(aggregated_errors, rp_service, jira_service, performance_degradation_rate, compare_with_baseline,
                      missed_threshold_rate, compare_with_thresholds, ado_reporter):
        if rp_service:
            rp_service.report_test_results(aggregated_errors, performance_degradation_rate, compare_with_baseline,
                                           missed_threshold_rate, compare_with_thresholds)

        if jira_service and jira_service.check_functional_errors:
            jira_service.connect()
            if jira_service.valid:
                jira_service.report_errors(aggregated_errors)
            else:
                print("Failed connection to Jira or project does not exist")
        if ado_reporter:
            ado_reporter.report_functional_errors(aggregated_errors)

    @staticmethod
    def report_performance_degradation(performance_degradation_rate, compare_with_baseline, rp_service, jira_service,
                                       ado_reporter):

        if jira_service and jira_service.check_performance_degradation:
            jira_service.connect()
            if jira_service.valid:
                if performance_degradation_rate > jira_service.performance_degradation_rate:
                    jira_service.report_performance_degradation(performance_degradation_rate, compare_with_baseline)
            else:
                print("Failed connection to Jira or project does not exist")
        if ado_reporter and performance_degradation_rate > 20:
            ado_reporter.report_performance_degradation(performance_degradation_rate, compare_with_baseline)

    @staticmethod
    def report_missed_thresholds(missed_threshold_rate, compare_with_thresholds, rp_service, jira_service,
                                 ado_reporter):

        if jira_service and jira_service.check_missed_thresholds:
            jira_service.connect()
            if jira_service.valid:
                if missed_threshold_rate > jira_service.missed_thresholds_rate:
                    jira_service.report_missed_thresholds(missed_threshold_rate, compare_with_thresholds)
            else:
                print("Failed connection to Jira or project does not exist")
        if ado_reporter and missed_threshold_rate > 50:
            ado_reporter.report_missed_thresholds(missed_threshold_rate, compare_with_thresholds)

