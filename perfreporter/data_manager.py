# Copyright 2019 getcarrier.io

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import operator
import requests
from time import time
from influxdb import InfluxDBClient
import numpy as np


SELECT_LAST_BUILDS_ID = "select distinct(id) from (select build_id as id, pct95 from api_comparison where " \
                        "simulation=\'{}\' and test_type=\'{}\' and \"users\"=\'{}\' " \
                        "and build_id!~/audit_{}_/ order by time DESC) GROUP BY time(1s) order by DESC limit {}"

SELECT_LAST_BUILD_DATA = "select * from api_comparison where build_id=\'{}\'"

SELECT_BASELINE_BUILD_ID = "select last(pct95), build_id from api_comparison where simulation=\'{}\' and " \
                           "test_type=\'{}\' and \"users\"=\'{}\' and build_id=~/audit_{}_/"

SELECT_BASELINE_DATA = "select * from api_comparison where build_id=\'{}\'"

SELECT_THRESHOLDS = "select last(red) as red, last(yellow) as yellow from threshold where request_name=\'{}\' " \
                    "and simulation=\'{}\'"

SELECT_USERS_COUNT = "select sum(\"max\") from (select max(\"user_count\") from \"users\" where " \
                     "build_id='{}' group by lg_id)"

SELECT_TEST_DATA = "select * from {} where build_id='{}'"

SELECT_ALL_THRESHOLDS = "select * from thresholds where simulation='{}' {}"

CALCULATE_TOTAL_THROUGHPUT = "select  sum(throughput) as \"throughput\", sum(ko) as \"ko\", " \
                             "sum(total) as \"total\" from api_comparison where build_id='{}'"

CALCULATE_ALL_AGGREGATION = "select max(response_time), min(response_time), ROUND(MEAN(response_time)) " \
                            "as avg, PERCENTILE(response_time, 95) as pct95, PERCENTILE(response_time, 50) " \
                            "as pct50 from {} where build_id='{}'"

COMPARISON_RULES = {"gte": "ge", "lte": "le", "gt": "gt", "lt": "lt", "eq": "eq"}

SELECT_LAST_UI_BUILD_ID = "select distinct(id) from (select build_id as id, count from uiperf where scenario=\'{}\' " \
                          "and suite=\'{}\' group by start_time order by time DESC limit 1) GROUP BY time(1s) " \
                          "order by DESC limit {}"

SELECT_UI_TEST_DATA = "select build_id, scenario, suite, domain, start_time, page, status, url, latency, tti, ttl," \
                      " onload, total_time, transfer, firstPaint, encodedBodySize, decodedBodySize from uiperf " \
                      "where build_id=\'{}\'"


class DataManager(object):
    def __init__(self, arguments, galloper_url, token, project_id):
        self.args = arguments
        self.galloper_url = galloper_url
        self.token = token
        self.project_id = project_id
        self.last_build_data = None
        self.client = InfluxDBClient(self.args["influx_host"], self.args['influx_port'],
                                     username=self.args['influx_user'], password=self.args['influx_password'])

    def write_comparison_data_to_influx(self):
        reqs = dict()
        timestamp = time()
        user_count = self.get_user_count()

        self.client.switch_database(self.args['influx_db'])
        data = self.client.query(SELECT_TEST_DATA.format(self.args['simulation'], self.args['build_id']))
        data = list(data.get_points())
        start_time = int(
            str(datetime.datetime.strptime(data[0]['time'], "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()).split(".")[0]) \
                     - int(int(data[0]['response_time']) / 1000)
        end_time = int(str(datetime.datetime.strptime(data[len(data) - 1]['time'],
                                                      "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()).split(".")[0])
        duration = end_time - start_time
        for req in data:
            key = '{} {}'.format(req["method"].upper(), req["request_name"])
            if key not in reqs:
                reqs[key] = {
                    "times": [],
                    "KO": 0,
                    "OK": 0,
                    "1xx": 0,
                    "2xx": 0,
                    "3xx": 0,
                    "4xx": 0,
                    "5xx": 0,
                    'NaN': 0,
                    "method": req["method"].upper(),
                    "request_name": req['request_name']
                }
            reqs[key]['times'].append(int(req['response_time']))
            if "{}xx".format(str(req['status_code'])[0]) in reqs[key]:
                reqs[key]["{}xx".format(str(req['status_code'])[0])] += 1
            else:
                reqs[key]["NaN"] += 1
            reqs[key][req['status']] += 1
            reqs[key]['simulation'] = req['simulation']
            reqs[key]['test_type'] = req['test_type']
            reqs[key]['env'] = req['env']
            reqs[key]['build_id'] = req['build_id']

        if not reqs:
            exit(0)
        points = []
        for req in reqs:
            np_arr = np.array(reqs[req]["times"])
            influx_record = {
                "measurement": "api_comparison",
                "tags": {
                    "simulation": reqs[req]['simulation'],
                    "env": reqs[req]['env'],
                    "users": user_count,
                    "test_type": reqs[req]['test_type'],
                    "build_id": reqs[req]['build_id'],
                    "request_name": reqs[req]['request_name'],
                    "method": reqs[req]['method'],
                    "duration": duration
                },
                "time": datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields": {
                    "throughput": round(float(len(reqs[req]["times"])) / float(duration), 3),
                    "total": len(reqs[req]["times"]),
                    "ok": reqs[req]["OK"],
                    "ko": reqs[req]["KO"],
                    "1xx": reqs[req]["1xx"],
                    "2xx": reqs[req]["2xx"],
                    "3xx": reqs[req]["3xx"],
                    "4xx": reqs[req]["4xx"],
                    "5xx": reqs[req]["5xx"],
                    "NaN": reqs[req]["NaN"],
                    "min": round(np_arr.min(), 2),
                    "max": round(np_arr.max(), 2),
                    "mean": round(np_arr.mean(), 2),
                    "pct50": int(np.percentile(np_arr, 50, interpolation="linear")),
                    "pct75": int(np.percentile(np_arr, 75, interpolation="linear")),
                    "pct90": int(np.percentile(np_arr, 90, interpolation="linear")),
                    "pct95": int(np.percentile(np_arr, 95, interpolation="linear")),
                    "pct99": int(np.percentile(np_arr, 99, interpolation="linear"))
                }
            }
            points.append(influx_record)
        try:
            self.client.switch_database(self.args['comparison_db'])
            self.client.write_points(points)
            self.client.close()
        except Exception as e:
            print(e)
            print("Failed connection to " + self.args["influx_host"] + ", database - comparison")
        return user_count, duration

    def get_api_test_info(self):
        tests_data = self.get_last_builds()
        if len(tests_data) == 0:
            raise Exception("No data found for given parameters")
        last_test_data = tests_data[0]
        self.args['build_id'] = tests_data[0][0]['build_id']
        baseline = self.get_baseline()
        violations, thresholds = self.get_thresholds(last_test_data, add_green=True)
        return tests_data, last_test_data, baseline, violations, thresholds

    def get_last_builds(self):
        self.client.switch_database(self.args['comparison_db'])
        tests_data = []
        build_ids = []
        last_builds = self.client.query(SELECT_LAST_BUILDS_ID.format(
            self.args['test'], self.args['test_type'], str(self.args['users']), self.args['test'],
            str(self.args['test_limit'])))
        for test in list(last_builds.get_points()):
            if test['distinct'] not in build_ids:
                build_ids.append(test['distinct'])

        for _id in build_ids:
            test_data = self.client.query(SELECT_LAST_BUILD_DATA.format(_id))
            tests_data.append(list(test_data.get_points()))
        return tests_data

    def get_user_count(self):
        self.client.switch_database(self.args['influx_db'])
        try:
            data = self.client.query(SELECT_USERS_COUNT.format(self.args['build_id']))
            data = list(data.get_points())[0]
            return int(data['sum'])
        except Exception as e:
            print(e)
        return 0

    def compare_with_baseline(self):
        baseline = self.get_baseline()
        last_build = self.get_last_build()
        comparison_metric = self.args['comparison_metric']
        compare_with_baseline = []
        if not baseline:
            print("Baseline not found")
            return 0, []
        for request in last_build:
            for baseline_request in baseline:
                if request['request_name'] == baseline_request['request_name']:
                    if int(request[comparison_metric]) > int(baseline_request[comparison_metric]):
                        compare_with_baseline.append({"request_name": request['request_name'],
                                                      "response_time": request[comparison_metric],
                                                      "baseline": baseline_request[comparison_metric]
                                                      })
        performance_degradation_rate = round(float(len(compare_with_baseline) / len(last_build)) * 100, 2)

        return performance_degradation_rate, compare_with_baseline

    def compare_with_thresholds(self):
        last_build = self.get_last_build()
        return self.get_thresholds(last_build)

    def get_baseline(self):
        headers = {'Authorization': f'bearer {self.token}'} if self.token else {}
        baseline_url = f"{self.galloper_url}/api/v1/baseline/{self.project_id}?" \
                       f"test_name={self.args['simulation']}&env={self.args['env']}"
        res = requests.get(baseline_url, headers={**headers, 'Content-type': 'application/json'}).json()
        return res["baseline"]

    def get_last_build(self):
        if self.last_build_data:
            return self.last_build_data
        self.client.switch_database(self.args['comparison_db'])
        test_data = self.client.query(SELECT_LAST_BUILD_DATA.format(self.args['build_id']))
        self.last_build_data = list(test_data.get_points())
        return self.last_build_data

    def compare_request_and_threhold(self, request, threshold):
        comparison_method = getattr(operator, COMPARISON_RULES[threshold['comparison']])
        if threshold['target'] == 'response_time':
            metric = request[threshold['aggregation']]
        elif threshold['target'] == 'throughput':
            metric = request['throughput']
        else:  # Will be in case error_rate is set as target
            metric = round(float(request['ko'] / request['total']) * 100, 2)
        if comparison_method(metric, threshold['red']):
            return "red", metric
        if comparison_method(metric, threshold['yellow']):
            return "yellow", metric
        return "green", metric

    def aggregate_test(self):
        self.client.switch_database(self.args['influx_db'])
        all_metics: list = list(self.client.query(
            CALCULATE_ALL_AGGREGATION.format(self.args['simulation'], self.args['build_id'])).get_points())
        self.client.switch_database(self.args['comparison_db'])
        tp: list = list(self.client.query(CALCULATE_TOTAL_THROUGHPUT.format(self.args['build_id'])).get_points())
        aggregated_dict = all_metics[0]
        aggregated_dict['throughput'] = round(tp[0]['throughput'], 2)
        aggregated_dict['ko'] = tp[0]['ko']
        aggregated_dict['total'] = tp[0]['total']
        aggregated_dict['request_name'] = 'all'
        return aggregated_dict

    def get_thresholds(self, test, add_green=False):
        compare_with_thresholds = []
        total_checked = 0
        total_violated = 0
        headers = {'Authorization': f'bearer {self.token}'} if self.token else {}
        thresholds_url = f"{self.galloper_url}/api/v1/thresholds/{self.project_id}/backend?" \
                         f"name={self.args['simulation']}&environment={self.args['env']}&order=asc"
        _thresholds = requests.get(thresholds_url, headers={**headers, 'Content-type': 'application/json'}).json()

        def compile_violation(request, th, total_checked, total_violated, compare_with_thresholds, add_green=False):
            total_checked += 1
            color, metric = self.compare_request_and_threhold(request, th)
            if add_green or color is not "green":
                compare_with_thresholds.append({
                    "request_name": request['request_name'],
                    "target": th['target'],
                    "aggregation": th["aggregation"],
                    "metric": metric,
                    "threshold": color,
                    "yellow": th['yellow'],
                    "red": th["red"]
                })
            if color is not "green":
                total_violated += 1
            return total_checked, total_violated, compare_with_thresholds
        self.client.switch_database(self.args['thresholds_db'])
        globaly_applicable: list = list(filter(lambda _th: _th['scope'] == 'all', _thresholds))
        every_applicable: list = list(filter(lambda _th: _th['scope'] == 'every', _thresholds))
        individual: list = list(filter(lambda _th: _th['scope'] != 'every' and _th['scope'] != 'all', _thresholds))
        individual_dict: dict = dict()
        for each in individual:
            if each['scope'] not in individual_dict:
                individual_dict[each['scope']] = []
            individual_dict[each['scope']].append(each)
        for request in test:
            thresholds = []
            targets = []
            if request['request_name'] in individual_dict:
                for ind in individual_dict[request['request_name']]:
                    targets.append(ind['target'])
                thresholds.extend(individual_dict[request['request_name']])
            for th in every_applicable:
                if th['target'] not in targets:
                    thresholds.append(th)
            for th in thresholds:
                total_checked, total_violated, compare_with_thresholds = compile_violation(
                    request, th, total_checked, total_violated, compare_with_thresholds, add_green)
        if globaly_applicable:
            test_data = self.aggregate_test()
            for th in globaly_applicable:
                total_checked, total_violated, compare_with_thresholds = compile_violation(
                    test_data, th, total_checked, total_violated, compare_with_thresholds, add_green)
        violated = 0
        if total_checked:
            violated = round(float(total_violated / total_checked) * 100, 2)
        return violated, compare_with_thresholds