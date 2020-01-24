from perfreporter.data_manager import DataManager
from perfreporter.reporter import Reporter
from perfreporter.jtl_parser import JTLParser
from perfreporter.junit_reporter import JUnit_reporter
import requests
import re
import shutil
from os import remove, environ
import json


class PostProcessor:

    def __init__(self, config_file=None):
        self.config_file = config_file

    def post_processing(self, args, aggregated_errors):
        data_manager = DataManager(args)
        if self.config_file:
            with open("/tmp/config.yaml", "w") as f:
                f.write(self.config_file)
        reporter = Reporter()
        rp_service, jira_service = reporter.parse_config_file(args)
        performance_degradation_rate, missed_threshold_rate = 0, 0
        compare_with_baseline, compare_with_thresholds = [], []
        if args['influx_host']:
            data_manager.write_comparison_data_to_influx()
            performance_degradation_rate, compare_with_baseline = data_manager.compare_with_baseline()
            missed_threshold_rate, compare_with_thresholds = data_manager.compare_with_thresholds()
            reporter.report_performance_degradation(performance_degradation_rate, compare_with_baseline, rp_service,
                                                    jira_service)
            reporter.report_missed_thresholds(missed_threshold_rate, compare_with_thresholds, rp_service, jira_service)
        else:
            parser = JTLParser()
            results = parser.parse_jtl()
            aggregated_requests = results['requests']
            thresholds = self.calculate_thresholds(results)
            JUnit_reporter.process_report(aggregated_requests, thresholds)
        reporter.report_errors(aggregated_errors, rp_service, jira_service, performance_degradation_rate,
                               compare_with_baseline, missed_threshold_rate, compare_with_thresholds)

    def distributed_mode_post_processing(self, galloper_url, results_bucket, prefix):
        errors = []
        args = {}
        # get list of files
        r = requests.get(f'{galloper_url}/artifacts?q={results_bucket}')
        pattern = '<a href="/artifacts/{}/({}.+?)"'.format(results_bucket, prefix)
        files = re.findall(pattern, r.text)

        # download and unpack each file
        for file in files:
            downloaded_file = requests.get(f'{galloper_url}/artifacts/{results_bucket}/{file}')
            with open(f"/tmp/{file}", 'wb') as f:
                f.write(downloaded_file.content)
            shutil.unpack_archive(f"/tmp/{file}", "/tmp/" + file.replace(".zip", ""), 'zip')
            remove(f"/tmp/{file}")
            with open(f"/tmp/{file}/".replace(".zip", "") + "aggregated_errors.json", "r") as f:
                errors.append(json.loads(f.read()))
            if not args:
                with open(f"/tmp/{file}/".replace(".zip", "") + "args.json", "r") as f:
                    args = json.loads(f.read())

            # delete file from minio
            requests.get(f'{galloper_url}/artifacts/{results_bucket}/{file}/delete')

        # aggregate errors from each load generator
        aggregated_errors = self.aggregate_errors(errors)
        self.post_processing(args, aggregated_errors)

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

