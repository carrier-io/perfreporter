import sys
import yaml

from perfreporter.report_portal import ReportPortal
from perfreporter.jira_wrapper import JiraWrapper
from perfreporter.ado_reporter import ADOReporter
from perfreporter.engagement_reporter import EngagementReporter


class Reporter(object):
    def __init__(self, logger, config_file="/tmp/config.yaml"):
        self.logger = logger
        self.config_file = config_file

    def parse_config_file(self, args):
        report_types = []
        try:
            with open(self.config_file, "rb") as f:
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
                self.logger.warning("ReportPortal configuration values missing, proceeding "
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
                self.logger.info("Jira configuration values missing, proceeding without Jira")
            else:
                jira_service = JiraWrapper(args, jira_url, jira_user, jira_pwd, jira_project, jira_assignee,
                                           check_functional_errors, check_performance_degradation,
                                           check_missed_thresholds, performance_degradation_rate,
                                           missed_thresholds_rate, jira_issue_type, jira_labels, jira_watchers,
                                           jira_epic_key)

        return rp_service, jira_service

    def parse_quality_gate(self, quality_gate_data: dict) -> dict:
        '''Parse QualityGate configuration from integrations.
        If any of the values in the dictionary is -1, 
        then we set the corresponding flag as False.
        '''
        self.logger.info("Parsing QualityGate configuration")
        try:
            return {
                'check_functional_errors': quality_gate_data['error_rate'] != -1,
                'check_performance_degradation': quality_gate_data['degradation_rate'] != -1,
                'check_missed_thresholds': quality_gate_data['missed_thresholds'] != -1,
                'error_rate': quality_gate_data['error_rate'],
                'performance_degradation_rate': quality_gate_data['degradation_rate'],
                'missed_thresholds_rate': quality_gate_data['missed_thresholds'],
            }
        except Exception as e:
            self.logger.error("Failed to parse QualityGate configuration")
            self.logger.error(e)
            return {}

    def get_jira_service(self, args, jira_config, jira_additional_config, quality_gate_config):
        for each in ["jira_url", "jira_login", "jira_password", "jira_project"]:
            if not jira_config.get(each):
                self.logger.info("Jira configuration values missing, proceeding without Jira")
                return None
        jira_service = JiraWrapper(args, jira_config["jira_url"], jira_config["jira_login"],
                                   jira_config["jira_password"], jira_config["jira_project"],
                                   jira_additional_config.get("assignee", jira_config["jira_login"]),
                                   quality_gate_config.get("check_functional_errors", False),
                                   quality_gate_config.get("check_performance_degradation", False),
                                   quality_gate_config.get("check_missed_thresholds", False),
                                   quality_gate_config.get("performance_degradation_rate", 20),
                                   quality_gate_config.get("missed_thresholds_rate", 50),
                                   jira_config.get("issue_type", "Bug"), 
                                   jira_additional_config.get("jira_labels", ""),
                                   jira_additional_config.get("jira_watchers", ""),
                                   jira_additional_config.get("jira_epic_key", None))
        return jira_service

    def get_rp_service(self, args, rp_config, rp_additional_config):
        for each in ["rp_host", "rp_token", "rp_project"]:
            if not rp_config.get(each):
                self.logger.warning("RP configuration values missing, proceeding without RP")
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
            self.logger.warning("ReportPortal configuration values missing, proceeding "
                  "without report portal integration ")
            return None
        else:
            rp_service = ReportPortal(args, rp_url, rp_token, rp_project, rp_launch_name, check_functional_errors,
                                      check_performance_degradation, check_missed_thresholds,
                                      performance_degradation_rate, missed_thresholds_rate)
            rp_service.my_error_handler(sys.exc_info())
        return rp_service

    def get_ado_reporter(self, args, ado_config, quality_gate_config):
        for each in ["org", "project", "pat"]:
            if not ado_config.get(each):
                self.logger.info("Azure DevOps configuration values missing, proceeding without Azure DevOps")
                return None
        return ADOReporter(args, ado_config, quality_gate_config)


    def get_engagement_rp_service(self, args, galloper_url, token, payload, project_id):
        for field in ('report_url', 'id', 'query_url'):
            if field not in payload:
                self.logger.warning(f"RP configuration missing value for {field}")
                return
        report_url = galloper_url + payload['report_url'] + '/' + project_id
        query_url = galloper_url + payload['query_url'] + '/' + project_id
        engagement_id = payload['id']
        reporter = EngagementReporter(args, report_url, query_url, token, engagement_id)
        return reporter


    def report_errors(self, aggregated_errors, rp_service, jira_service, performance_degradation_rate, compare_with_baseline,
                      missed_threshold_rate, compare_with_thresholds, ado_reporter, engagement_reporter):
        if rp_service:
            rp_service.report_test_results(aggregated_errors, performance_degradation_rate, compare_with_baseline,
                                           missed_threshold_rate, compare_with_thresholds)

        if jira_service and jira_service.check_functional_errors:
            jira_service.connect()
            if jira_service.valid:
                jira_service.report_errors(aggregated_errors)
            else:
                self.logger.error("Failed connection to Jira or project does not exist")
        if ado_reporter and ado_reporter.check_functional_errors:
            ado_reporter.report_functional_errors(aggregated_errors)
        
        if engagement_reporter:
            engagement_reporter.report_errors(aggregated_errors)


    def report_performance_degradation(self, performance_degradation_rate, compare_with_baseline, rp_service, jira_service,
                                       ado_reporter, engagement_reporter):

        if jira_service and jira_service.check_performance_degradation:
            jira_service.connect()
            if jira_service.valid:
                if performance_degradation_rate > jira_service.performance_degradation_rate:
                    jira_service.report_performance_degradation(performance_degradation_rate, compare_with_baseline)
            else:
                self.logger.error("Failed connection to Jira or project does not exist")
        if ado_reporter and ado_reporter.check_performance_degradation:
            if performance_degradation_rate > ado_reporter.performance_degradation_rate:
                ado_reporter.report_performance_degradation(performance_degradation_rate, compare_with_baseline)

        if engagement_reporter:
            engagement_reporter.report_performance_degradation(performance_degradation_rate, compare_with_baseline)


    def report_missed_thresholds(self, missed_threshold_rate, compare_with_thresholds, rp_service, jira_service,
                                 ado_reporter, engagement_reporter):

        if jira_service and jira_service.check_missed_thresholds:
            jira_service.connect()
            if jira_service.valid:
                if missed_threshold_rate > jira_service.missed_thresholds_rate:
                    jira_service.report_missed_thresholds(missed_threshold_rate, compare_with_thresholds)
            else:
                self.logger.error("Failed connection to Jira or project does not exist")
        if ado_reporter and ado_reporter.check_missed_thresholds:
            if missed_threshold_rate > ado_reporter.missed_thresholds_rate:
                ado_reporter.report_missed_thresholds(missed_threshold_rate, compare_with_thresholds)

        if engagement_reporter:
            engagement_reporter.report_missed_thresholds(missed_threshold_rate, compare_with_thresholds)