from perfreporter.data_manager import DataManager
from perfreporter.reporter import Reporter
from perfreporter.jtl_parser import JTLParser
from perfreporter.junit_reporter import JUnit_reporter
import requests
import re
import shutil
from os import remove, environ
from json import JSONDecodeError, loads, dumps
from datetime import datetime
from time import time
from centry_loki import log_loki


class PostProcessor:

    def __init__(self, config_file=None):
        self.config_file = config_file

    def post_processing(self, args, aggregated_errors, galloper_url=None, project_id=None,
                        results_bucket=None, prefix=None, token=None, integration=None):
        if not integration:
            integration = {}      
        if not galloper_url:
            galloper_url = environ.get("galloper_url")
        if not project_id:
            project_id = environ.get("project_id")
        if not token:
            token = environ.get("token")
        headers = {'Authorization': f'bearer {token}'} if token else {}

        loki_context = {"url": f"http://{args['influx_host']}:3100/loki/api/v1/push",
                        "hostname": "post-processor", "labels": {"build_id": args['build_id'],
                                                                 "project": project_id,
                                                                 "report_id": args['report_id']}}

        logger = log_loki.get_logger(loki_context)

        status = ""
        # TODO add post processing API
        # try:
        #     if galloper_url and project_id and args.get("build_id"):
        #         url = f'{galloper_url}/api/v1/backend_performance/{project_id}/processing?build_id={args.get("build_id")}'
        #         r = requests.get(url, headers={**headers, 'Content-type': 'application/json'}).json()
        #         status = r["test_status"]["status"]
        #     if status == "Finished":
        #         logger.warning("Post processing has already finished")
        #         raise Exception("Post processing has already finished")
        # except:
        #     logger.error("Failed to check test status")
        start_post_processing = time()
        data_manager = DataManager(args, galloper_url, token, project_id, logger)
        if self.config_file:
            with open("/tmp/config.yaml", "w") as f:
                f.write(self.config_file)
        reporter = Reporter(logger)
        rp_service, jira_service = reporter.parse_config_file(args)
        
        if integration.get('processing', {}).get('quality_gate'):
            quality_gate_config = reporter.parse_quality_gate(integration['processing']['quality_gate'])
        else:
            quality_gate_config = {}

        if not jira_service and integration.get('reporters', {}).get('reporter_jira'):
            if galloper_url and token and project_id:
                jira_core_config = {}
                jira_core_config["jira_url"] = integration["reporters"]["reporter_jira"]["integration_settings"]["url"]
                jira_core_config["jira_login"] = integration["reporters"]["reporter_jira"]["integration_settings"]["login"]
                jira_core_config["jira_password"] = integration["reporters"]["reporter_jira"]["integration_settings"]["passwd"]
                jira_core_config["jira_project"] = integration["reporters"]["reporter_jira"]["integration_settings"]["project"]
                jira_core_config["issue_type"] = integration["reporters"]["reporter_jira"]["integration_settings"]["issue_type"]
                jira_additional_config = {k: v for k, v in integration["reporters"]["reporter_jira"].items() if k != "integration_settings"}
                jira_service = reporter.get_jira_service(args, jira_core_config, jira_additional_config, quality_gate_config)

        if not rp_service and "report_portal" in integration:
            if galloper_url and token and project_id:
                secrets_url = f"{galloper_url}/api/v1/secrets/secret/{project_id}/"
                try:
                    rp_core_config = loads(requests.get(secrets_url + "rp",
                                                        headers={**headers, 'Content-type': 'application/json'}).json()[
                                               "secret"])
                except (AttributeError, JSONDecodeError):
                    rp_core_config = {}
                try:
                    rp_additional_config = loads(requests.get(secrets_url + "rp_perf_api",
                                                              headers={**headers, 'Content-type': 'application/json'}
                                                              ).json()["secret"])
                except (AttributeError, JSONDecodeError):
                    rp_additional_config = {}
                rp_service = reporter.get_rp_service(args, rp_core_config, rp_additional_config)
                
        ado_config = integration.get('reporters', {}).get('azure_devops')
        ado_reporter = reporter.get_ado_reporter(args, ado_config, quality_gate_config) if ado_config else None


        engagement_reporter = None
        if integration and integration.get("reporters") and "reporter_engagement" in integration['reporters'].keys():
            if galloper_url and token and project_id:
                payload = integration['reporters']['reporter_engagement']
                engagement_reporter = reporter.get_engagement_rp_service(args, galloper_url, token, payload, project_id)

        performance_degradation_rate, missed_threshold_rate = 0, 0
        users_count, duration = 0, 0
        total_checked_thresholds = 0
        response_times = {}
        compare_with_baseline, compare_with_thresholds = [], []
        if args['influx_host']:
            try:
                users_count, duration, response_times = data_manager.write_comparison_data_to_influx()
            except Exception as e:
                logger.error("Failed to aggregate results")
                logger.error(e)
            try:
                performance_degradation_rate, compare_with_baseline = data_manager.compare_with_baseline()
            except Exception as e:
                logger.error("Failed to compare with baseline")
                logger.error(e)
            try:
                total_checked_thresholds, missed_threshold_rate, compare_with_thresholds = data_manager.compare_with_thresholds()
            except Exception as e:
                logger.error("Failed to compare with thresholds")
                logger.error(e)
            try:
                reporter.report_performance_degradation(performance_degradation_rate, compare_with_baseline, rp_service,
                                                        jira_service, ado_reporter, engagement_reporter)
                reporter.report_missed_thresholds(missed_threshold_rate, compare_with_thresholds, rp_service,
                                                  jira_service, ado_reporter, engagement_reporter)
            except Exception as e:
                logger.error(e)
            if quality_gate_config:
            # if integration and integration.get("reporters") and "quality_gate" in integration["reporters"].keys():
                try:
                    last_build = data_manager.get_last_build()
                    total_checked, violations, thresholds = data_manager.get_thresholds(last_build, True)
                    report = JUnit_reporter.create_report(thresholds, prefix)
                    files = {'file': open(report, 'rb')}
                    upload_url = f'{galloper_url}/api/v1/artifacts/artifacts/{project_id}/{results_bucket}'
                    requests.post(upload_url, allow_redirects=True, files=files, headers=headers)
                except Exception as e:
                    logger.error("Failed to create junit report")
                    logger.error(e)
            if galloper_url:
                # try:
                #     thresholds_quality_gate = int(quality_gate_config["missed_thresholds_rate"])
                #     # thresholds_quality_gate = int(integration["reporters"]["quality_gate"]["failed_thresholds_rate"])
                # except:
                #     thresholds_quality_gate = 20
                if total_checked_thresholds:
                    if quality_gate_config.get('check_missed_thresholds') and missed_threshold_rate > quality_gate_config["missed_thresholds_rate"]:
                        thresholds_quality_gate = quality_gate_config["missed_thresholds_rate"]
                        test_status = {"status": "Failed", "percentage": 100,
                                       "description": f"Missed more then {thresholds_quality_gate}% thresholds"}
                    else:
                        test_status = {"status": "Success", "percentage": 100,
                                       "description": f"Successfully met more than {100 - thresholds_quality_gate}% of thresholds"}
                else:
                    test_status = {"status": "Finished", "percentage": 100, "description": "Test is finished"}
                lg_type = args["influx_db"].split("_")[0] if "_" in args["influx_db"] else args["influx_db"]
                data = {'build_id': args["build_id"], 'test_name': args["simulation"], 'lg_type': lg_type,
                        'missed': int(missed_threshold_rate),
                        'test_status': test_status,
                        'vusers': users_count,
                        'duration': duration, 'response_times': dumps(response_times)}
                url = f'{galloper_url}/api/v1/backend_performance/reports/{project_id}'
                r = requests.put(url, json=data, headers={**headers, 'Content-type': 'application/json'})
                logger.info(r.text)
                try:
                    if r.json()["message"] == "updated" and self.str2bool(environ.get("remove_row_data")):
                        data_manager.delete_test_data()
                except:
                    logger.error("Failed update report")
                    data = {"test_status": {"status": "ERROR", "percentage": 100, "description": "Failed update report"}}
                    headers = {'content-type': 'application/json', 'Authorization': f'bearer {token}'}
                    url = f'{galloper_url}/api/v1/backend_performance/report_status/{project_id}/{args["report_id"]}'
                    response = requests.put(url, json=data, headers=headers)
                    try:
                        logger.info(response.json()["message"])
                    except:
                        logger.error(response.text)
        try:
            reporter.report_errors(aggregated_errors, rp_service, jira_service, performance_degradation_rate,
                                   compare_with_baseline, missed_threshold_rate, compare_with_thresholds, ado_reporter,
                                   engagement_reporter)
        except Exception as e:
            logger.error(e)

        logger.info("Total time -  %s seconds" % (round(time() - start_post_processing, 2)))
        # if junit_report:
        #     parser = JTLParser()
        #     results = parser.parse_jtl()
        #     aggregated_requests = results['requests']
        #     thresholds = self.calculate_thresholds(results)
        #     JUnit_reporter.process_report(aggregated_requests, thresholds)
        if integration and integration.get("reporters") and "reporter_email" in integration["reporters"].keys():
            if galloper_url and token and project_id:
                email_notification_id = integration["reporters"]["reporter_email"].get("task_id")
                if email_notification_id:
                    emails = integration["reporters"]["reporter_email"].get("recipients", [])
                    if emails:
                        task_url = f"{galloper_url}/api/v1/tasks/task/{project_id}/{email_notification_id}"
                        event = {
                            "galloper_url": galloper_url,
                            "token": token,
                            "project_id": project_id,
                            "influx_host": args["influx_host"],
                            "influx_port": args["influx_port"],
                            "influx_user": args["influx_user"],
                            "influx_password": args["influx_password"],
                            "influx_db": args['influx_db'],
                            "comparison_db": args['comparison_db'],
                            "test": args['simulation'],
                            "user_list": emails,
                            "notification_type": "api",
                            "test_type": args["type"],
                            "env": args["env"],
                            "users": users_count,
                            "smtp_host": integration["reporters"]["reporter_email"]["integration_settings"]["host"],
                            "smtp_port": integration["reporters"]["reporter_email"]["integration_settings"]["port"],
                            "smtp_user": integration["reporters"]["reporter_email"]["integration_settings"]["user"],
                            "smtp_sender": integration["reporters"]["reporter_email"]["integration_settings"]["sender"],
                            "smtp_password": integration["reporters"]["reporter_email"]["integration_settings"]["passwd"],
                        }
                        if quality_gate_config.get('check_functional_errors'):
                            event["error_rate"] = quality_gate_config['error_rate']
                        if quality_gate_config.get('check_performance_degradation'):
                            event["performance_degradation_rate"] = quality_gate_config['performance_degradation_rate']
                        if quality_gate_config.get('check_missed_thresholds'):
                            event["missed_thresholds"] = quality_gate_config['missed_thresholds_rate']
                        
                        res = requests.post(task_url, json=event, headers={'Authorization': f'bearer {token}',
                                                                           'Content-type': 'application/json'})
                        logger.info("Email notification")
                        logger.info(res.text)

    def distributed_mode_post_processing(self, galloper_url, project_id, results_bucket, prefix,
                                         token=None, integration={}, report_id=None,
                                         influx_host=None, influx_user='', influx_password=''):

        headers = {'Authorization': f'bearer {token}'} if token else {}
        if project_id and galloper_url and report_id:
            r = requests.get(f'{galloper_url}/api/v1/backend_performance/reports/{project_id}?report_id={report_id}',
                             headers={**headers, 'Content-type': 'application/json'}).json()
            start_time = r["start_time"]
            end_time = str(datetime.now()).replace(" ", "T") + "Z"
            args = {
                'type': r['type'],
                'simulation': r['name'],
                'build_id': r['build_id'],
                'report_id': report_id,
                'env': r['environment'],
                'influx_host': environ.get(f"influx_host"),
                'influx_port': '8086',
                'influx_user': environ.get(f"influx_user"),
                'influx_password': environ.get(f"influx_password"),
                'comparison_metric': 'pct95',
                'influx_db': environ.get(f"{r['lg_type']}_db") if environ.get(f"{r['lg_type']}_db") else r["lg_type"],
                'comparison_db': environ.get("comparison_db") if environ.get("comparison_db") else "comparison",
                'test_limit': 5
            }
            aggregated_errors = {}
            r = requests.get(
                f'{galloper_url}/api/v1/backend_performance/charts/errors/table?test_name={args["simulation"]}&'
                f'start_time={start_time}&end_time={end_time}&low_value=0.00&high_value=100.00&'
                f'status=all&order=asc',
                headers={**headers, 'Content-type': 'application/json'}).json()

            for each in r:
                aggregated_errors[each['Error key']] = {
                    'Request name': each['Request name'],
                    'Method': each['Method'],
                    'Request headers': each['Headers'],
                    'Error count': each['count'],
                    'Response code': each['Response code'],
                    'Request URL': each['URL'],
                    'Request_params': [each['Request params']],
                    'Response': [each['Response body']],
                    'Error_message': [each['Error message']],
                }
            self.post_processing(args, aggregated_errors, galloper_url, project_id, results_bucket, prefix,
                                 token, integration)

        # else:
        #     errors = []
        #     args = {}
        #     # get list of files
        #     r = requests.get(f'{galloper_url}/api/v1/artifacts/artifacts/{project_id}/{results_bucket}',
        #                      headers={**headers, 'Content-type': 'application/json'})
        #     files = []
        #     for each in r.json()["rows"]:
        #         if each["name"].startswith(prefix):
        #             files.append(each["name"])
        #
        #     # download and unpack each file
        #     bucket_path = f'{galloper_url}/api/v1/artifacts/artifact/{project_id}/{results_bucket}'
        #     for file in files:
        #         downloaded_file = requests.get(f'{bucket_path}/{file}', headers=headers)
        #         with open(f"/tmp/{file}", 'wb') as f:
        #             f.write(downloaded_file.content)
        #         shutil.unpack_archive(f"/tmp/{file}", "/tmp/" + file.replace(".zip", ""), 'zip')
        #         remove(f"/tmp/{file}")
        #         with open(f"/tmp/{file}/".replace(".zip", "") + "aggregated_errors.json", "r") as f:
        #             errors.append(loads(f.read()))
        #         if not args:
        #             with open(f"/tmp/{file}/".replace(".zip", "") + "args.json", "r") as f:
        #                 args = loads(f.read())
        #
        #         # delete file from minio
        #         requests.delete(f'{bucket_path}/file?fname[]={file}', headers=headers)
        #
        #     # aggregate errors from each load generator
        #     aggregated_errors = self.aggregate_errors(errors)
        #     self.post_processing(args, aggregated_errors, galloper_url, project_id, results_bucket, prefix,
        #                          token, integration)

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

    @staticmethod
    def str2bool(v):
        if v is None:
            return False
        if isinstance(v, bool):
            return v
        if v.lower() in ('yes', 'true', 't', 'y', '1'):
            return True
        elif v.lower() in ('no', 'false', 'f', 'n', '0'):
            return False
        else:
            raise Exception('Boolean value expected.')
