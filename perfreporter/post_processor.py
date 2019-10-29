from perfreporter.data_manager import DataManager
from perfreporter.reporter import Reporter


class PostProcessor:

    def __init__(self, args, aggregated_errors, comparison_data=None, config_file=None):
        self.aggregated_errors = aggregated_errors
        self.comparison_data = comparison_data
        self.args = args
        self.config_file = config_file
        self.data_manager = DataManager(args)

    def post_processing(self):
        self.data_manager.write_comparison_data_to_influx()
        if self.config_file:
            with open("/tmp/config.yaml", "w") as f:
                f.write(self.config_file)
        reporter = Reporter()
        loki, rp_service, jira_service = reporter.parse_config_file(self.args)
        performance_degradation_rate, compare_with_baseline = self.data_manager.compare_with_baseline()
        missed_threshold_rate, compare_with_thresholds = self.data_manager.compare_with_thresholds()
        reporter.report_errors(self.aggregated_errors, rp_service, jira_service)
        reporter.report_performance_degradation(performance_degradation_rate, compare_with_baseline, rp_service,
                                                jira_service)
        reporter.report_missed_thresholds(missed_threshold_rate, compare_with_thresholds, rp_service, jira_service)
