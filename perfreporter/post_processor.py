from perfreporter.jtl_parser import JTLParser
from perfreporter.junit_reporter import JUnit_reporter
from os import remove, environ


class PostProcessor:

    def __init__(self, config_file=None):
        self.config_file = config_file

    def post_processing(self, args, aggregated_errors, galloper_url=None, project_id=None,
                        junit_report=True, results_bucket=None, prefix=None, token=None, integration=[],
                        email_recipients=None):
        if not junit_report:
            junit_report = environ.get("junit_report")

        if junit_report:
            parser = JTLParser()
            results = parser.parse_jtl()
            print("[INFO] results")
            print(results)
            aggregated_requests = results['requests']
            thresholds = self.calculate_thresholds(results)
            JUnit_reporter.process_report(aggregated_requests, thresholds)
            print("[INFO] Thresholds Report GENERATED")

    @staticmethod
    def aggregate_errors(test_errors):
        aggregated_errors = {}
        for errors in test_errors:
            for err in errors:
                if err not in aggregated_errors:
                    aggregated_errors[err] = errors[err]
                else:
                    aggregated_errors[err]['Error count'] = int(aggregated_errors[err]['Error count']) \
                                                            + int(errors[err]['Error count'])

        return aggregated_errors

    @staticmethod
    def calculate_thresholds(results):
        thresholds = []
        tp_threshold = int(environ.get('tp', 10))
        rt_threshold = int(environ.get('rt', 500))
        er_threshold = int(environ.get('er', 5))

        if results['throughput'] < tp_threshold:
            thresholds.append({"target": "throughput", "scope": "all", "value": results['throughput'],
                               "threshold": tp_threshold, "status": "FAILED", "metric": "req/s"})
        else:
            thresholds.append({"target": "throughput", "scope": "all", "value": results['throughput'],
                               "threshold": tp_threshold, "status": "PASSED", "metric": "req/s"})

        if results['error_rate'] > er_threshold:
            thresholds.append({"target": "error_rate", "scope": "all", "value": results['error_rate'],
                               "threshold": er_threshold, "status": "FAILED", "metric": "%"})
        else:
            thresholds.append({"target": "error_rate", "scope": "all", "value": results['error_rate'],
                               "threshold": er_threshold, "status": "PASSED", "metric": "%"})

        for req in results['requests']:

            if results['requests'][req]['response_time'] > rt_threshold:
                thresholds.append({"target": "response_time", "scope": results['requests'][req]['request_name'],
                                   "value": results['requests'][req]['response_time'],
                                   "threshold": rt_threshold, "status": "FAILED", "metric": "ms"})
            else:
                thresholds.append({"target": "response_time", "scope": results['requests'][req]['request_name'],
                                   "value": results['requests'][req]['response_time'],
                                   "threshold": rt_threshold, "status": "PASSED", "metric": "ms"})

        return thresholds
