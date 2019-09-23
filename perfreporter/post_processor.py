from perfreporter.data_manager import DataManager
from perfreporter.reporter import Reporter


class PostProcessor:

    def __init__(self, args, aggregated_errors, errors, comparison_data=None, config_file=None):
        self.aggregated_errors = aggregated_errors
        self.errors = errors
        self.comparison_data = comparison_data
        self.args = args
        self.config_file = config_file
        self.data_manager = DataManager(args)

    def distributed_mode_post_processing(self):
        self.data_manager.write_comparison_data_to_influx(self.comparison_data)
        if self.config_file:
            with open("/tmp/config.yaml", "w") as f:
                f.write(self.config_file)
        self.post_processing()

    def post_processing(self):
        reporter = Reporter()
        loki, rp_service, jira_service = reporter.parse_config_file(self.args)
        performance_degradation_rate, compare_with_baseline = self.data_manager.compare_with_baseline()
        missed_threshold_rate, compare_with_thresholds = self.data_manager.compare_with_thresholds()
        reporter.report_errors(self.aggregated_errors, self.errors, self.args, loki, rp_service, jira_service)
        reporter.report_performance_degradation(performance_degradation_rate, compare_with_baseline, rp_service,
                                                jira_service)
        reporter.report_missed_thresholds(missed_threshold_rate, compare_with_thresholds, rp_service, jira_service)
