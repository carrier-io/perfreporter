from perfreporter.comparison import Comparison
from perfreporter.reporter import Reporter


class DistributedModePostProcessor:

    def __init__(self, args, aggregated_errors, errors, comparison_data, config_file=None):
        self.aggregated_errors = aggregated_errors
        self.errors = errors
        self.comparison_data = comparison_data
        self.args = args
        self.config_file = config_file

    def post_processing(self):
        influx_comparison = Comparison(self.args)
        influx_comparison.write_comparison_data_to_influx(self.comparison_data)
        performance_degradation_rate, compare_with_baseline = influx_comparison.compare_with_baseline()
        missed_threshold_rate, compare_with_thresholds = influx_comparison.compare_with_thresholds()
        if self.config_file:
            with open("/tmp/config.yaml", "w") as f:
                f.write(self.config_file)
        reporter = Reporter()
        loki, rp_service, jira_service = reporter.parse_config_file(self.args)
        reporter.report_errors(self.aggregated_errors, self.errors, self.args, loki, rp_service, jira_service)
        reporter.report_performance_degradation(performance_degradation_rate, compare_with_baseline, rp_service,
                                                jira_service)
        reporter.report_missed_thresholds(missed_threshold_rate, compare_with_thresholds, rp_service, jira_service)
