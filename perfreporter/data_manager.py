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
from os import environ


SELECT_LAST_BUILDS_ID = "select distinct(id) from (select build_id as id, pct95 from api_comparison where " \
                        "simulation=\'{}\' and test_type=\'{}\' and \"users\"=\'{}\' " \
                        "and build_id!~/audit_{}_/ order by time DESC) GROUP BY time(1s) order by DESC limit {}"

SELECT_LAST_BUILD_DATA = "select * from api_comparison where build_id=\'{}\'"

SELECT_USERS_COUNT = "select sum(\"max\") from (select max(\"user_count\") from \"users\" where " \
                     "build_id='{}' group by lg_id)"

SELECT_TEST_DATA = "select response_time from {} where build_id='{}' and request_name='{}' and method='{}'"

SELECT_TEST_DATA_OFFSET = "select response_time from {} where build_id='{}' and request_name='{}' and method='{}'" \
                          " and time>'{}' limit {}"

GET_REQUEST_NAMES = "show tag values on {} from {} with key=\"request_name\" where build_id='{}'"

GET_REQUEST_METHODS = "show tag values on {} from {} with key=\"method\" where build_id='{}' and request_name='{}'"

TOTAL_REQUEST_COUNT = "select count(\"response_time\") from {} where build_id='{}'"

FIRST_REQUEST = "select first(\"response_time\") from {} where build_id='{}'"

LAST_REQUEST = "select last(\"response_time\") from {} where build_id='{}'"

REQUEST_COUNT = "select count(\"response_time\") from {} where build_id='{}' and request_name='{}' and method='{}'"

REQUEST_MIN = "select min(\"response_time\") from {} where build_id='{}' and request_name='{}' and method='{}'"

REQUEST_MAX = "select max(\"response_time\") from {} where build_id='{}' and request_name='{}' and method='{}'"

REQUEST_MEAN = "select mean(\"response_time\") from {} where build_id='{}' and request_name='{}' and method='{}'"

SELECT_PERCENTILE = "select percentile(\"response_time\", {}) as \"pct\" from {} where build_id='{}' and" \
                    " request_name='{}' and method='{}'"

REQUEST_STATUS = "select count(\"response_time\") from {} where build_id='{}' and request_name='{}' and method='{}'" \
                 " and status='{}'"

REQUEST_STATUS_CODE = "select count(\"response_time\") from {} where build_id='{}' and request_name='{}' " \
                      "and method='{}' and status_code=~/^{}/"

REQUEST_STATUS_CODE_NAN = "select count(\"response_time\") from {} where build_id='{}' and request_name='{}' " \
                          "and method='{}' and status_code!~/1/ and status_code!~/2/ and status_code!~/3/ " \
                          "and status_code!~/4/ and status_code!~/5/"

CALCULATE_TOTAL_THROUGHPUT = "select  sum(throughput) as \"throughput\", sum(ko) as \"ko\", " \
                             "sum(total) as \"total\" from api_comparison where build_id='{}'"

CALCULATE_ALL_AGGREGATION = "select max(response_time), min(response_time), ROUND(MEAN(response_time)) " \
                            "as avg, PERCENTILE(response_time, 95) as pct95, PERCENTILE(response_time, 50) " \
                            "as pct50 from {} where build_id='{}'"

DELETE_TEST_DATA = "delete from {} where build_id='{}'"

DELETE_USERS_DATA = "delete from \"users\" where build_id='{}'"

COMPARISON_RULES = {"gte": "ge", "lte": "le", "gt": "gt", "lt": "lt", "eq": "eq"}

BATCH_SIZE = int(environ.get("BATCH_SIZE", 5000000))


class DataManager(object):
    def __init__(self, arguments, galloper_url, token, project_id):
        self.args = arguments
        self.galloper_url = galloper_url
        self.token = token
        self.project_id = project_id
        self.last_build_data = None
        self.client = InfluxDBClient(self.args["influx_host"], self.args['influx_port'],
                                     username=self.args['influx_user'], password=self.args['influx_password'])

    def delete_test_data(self):
        self.client.switch_database(self.args['influx_db'])
        self.client.query(DELETE_TEST_DATA.format(self.args["simulation"], self.args["build_id"]))
        self.client.query(DELETE_USERS_DATA.format(self.args["build_id"]))

    def write_comparison_data_to_influx(self):
        timestamp = time()
        user_count = self.get_user_count()
        print(f"build_id={self.args['build_id']}")
        self.client.switch_database(self.args['influx_db'])
        total_requests_count = int(list(self.client.query(TOTAL_REQUEST_COUNT
                                                          .format(self.args['simulation'],
                                                                  self.args['build_id'])).get_points())[0]["count"])
        print(f"Total requests count = {total_requests_count}")

        # Get request names and methods
        request_names = list(self.client.query(GET_REQUEST_NAMES.format(self.args['influx_db'], self.args['simulation'],
                                                                        self.args['build_id'])).get_points())
        request_names = list(each['value'] for each in request_names)
        reqs = []
        for request_name in request_names:
            methods = list(self.client.query(GET_REQUEST_METHODS.format(self.args['influx_db'], self.args['simulation'],
                                                                        self.args['build_id'],
                                                                        request_name)).get_points())
            for method in methods:
                reqs.append({
                    "request_name": request_name,
                    "method": method["value"]
                })

        # calculate test duration and throughput
        first_request = self.client.query(FIRST_REQUEST.format(self.args['simulation'], self.args['build_id']))
        first_request = list(first_request.get_points())
        last_request = self.client.query(LAST_REQUEST.format(self.args['simulation'], self.args['build_id']))
        last_request = list(last_request.get_points())
        start_time = int(str(datetime.datetime.strptime(first_request[0]['time'],
                                                        "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()).split(".")[0]) \
                     - int(int(first_request[0]['first']) / 1000)
        end_time = int(str(datetime.datetime.strptime(last_request[0]['time'],
                                                      "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()).split(".")[0])
        duration = end_time - start_time
        _throughput = round(float(total_requests_count / duration), 3)
        print(f"duration = {duration}")
        print(f"throughput = {_throughput}")

        data = np.array([])
        for req in reqs:
            req['simulation'] = self.args['simulation']
            req['test_type'] = self.args['type']
            req['env'] = self.args['env']
            req['build_id'] = self.args['build_id']
            req["total"] = int(list(self.client.query(REQUEST_COUNT.format(self.args['simulation'],
                                                                           self.args['build_id'], req['request_name'],
                                                                           req['method'])).get_points())[0]["count"])
            req["throughput"] = round(float(req["total"]) / float(duration), 3)
            req["times"] = np.array([])

            # calculate response time metrics per request
            response_time_q = SELECT_TEST_DATA.format(self.args['simulation'], self.args['build_id'],
                                                      req["request_name"], req["method"])
            if req["total"] <= BATCH_SIZE:
                _data = list(self.client.query(response_time_q).get_points())
                req["times"] = np.append(req["times"], list(int(each["response_time"]) for each in _data))
            else:
                shards = req["total"] // BATCH_SIZE
                last_read_time = '1970-01-01T19:25:26.005Z'
                for i in range(shards):
                    response_time_q = SELECT_TEST_DATA_OFFSET.format(self.args['simulation'], self.args['build_id'],
                                                                     req['request_name'], req['method'],
                                                                     last_read_time, BATCH_SIZE)
                    _data = list(self.client.query(response_time_q).get_points())
                    last_read_time = _data[-1]['time']
                    req["times"] = np.append(req["times"], list(int(each["response_time"]) for each in _data))

                if req["total"] % BATCH_SIZE != 0:
                    response_time_q = SELECT_TEST_DATA_OFFSET.format(self.args['simulation'], self.args['build_id'],
                                                                     req['request_name'], req['method'],
                                                                     last_read_time, BATCH_SIZE)
                    _data = list(self.client.query(response_time_q).get_points())
                    req["times"] = np.append(req["times"], list(int(each["response_time"]) for each in _data))
            data = np.append(data, req["times"])

            req["min"] = req.get("times").min()
            req["max"] = req.get("times").max()
            req["mean"] = req.get("times").mean()

            for pct in ["50", "75", "90", "95", "99"]:
                req[f"pct{pct}"] = int(np.percentile(req.get("times"), int(pct), interpolation="linear"))

            del req["times"]

            # calculate status and status codes per request
            ok_count = list(self.client.query(REQUEST_STATUS.format(self.args['simulation'],
                                                                    self.args['build_id'], req['request_name'],
                                                                    req['method'], "OK")).get_points())
            req["OK"] = ok_count[0]["count"] if len(ok_count) > 0 else 0
            ko_count = list(self.client.query(REQUEST_STATUS.format(self.args['simulation'],
                                                                    self.args['build_id'], req['request_name'],
                                                                    req['method'], "KO")).get_points())
            req["KO"] = ko_count[0]["count"] if len(ko_count) > 0 else 0
            for code in ["1", "2", "3", "4", "5"]:
                _tmp = list(self.client.query(REQUEST_STATUS_CODE.format(self.args['simulation'],
                                                                         self.args['build_id'], req['request_name'],
                                                                         req['method'], code)).get_points())
                req[f"{code}xx"] = _tmp[0]["count"] if len(_tmp) > 0 else 0

            _NaN = list(self.client.query(REQUEST_STATUS_CODE_NAN.format(self.args['simulation'],
                                                                         self.args['build_id'], req['request_name'],
                                                                         req['method'])).get_points())
            req["NaN"] = _NaN[0]["count"] if len(_NaN) > 0 else 0

        # calculate overall response time metrics
        response_times = {
            "min": round(float(data.min()), 2),
            "max": round(float(data.max()), 2),
            "mean": round(float(data.mean()), 2),
            "pct50": int(np.percentile(data, 50, interpolation="linear")),
            "pct75": int(np.percentile(data, 75, interpolation="linear")),
            "pct90": int(np.percentile(data, 90, interpolation="linear")),
            "pct95": int(np.percentile(data, 95, interpolation="linear")),
            "pct99": int(np.percentile(data, 99, interpolation="linear"))
        }

        # Write data to comparison db
        if not reqs:
            print("No requests in the test")
            raise Exception("No requests in the test")
        points = []
        for req in reqs:
            influx_record = {
                "measurement": "api_comparison",
                "tags": {
                    "simulation": req['simulation'],
                    "env": req['env'],
                    "users": user_count,
                    "test_type": req['test_type'],
                    "build_id": req['build_id'],
                    "request_name": req['request_name'],
                    "method": req['method'],
                    "duration": duration
                },
                "time": datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ'),
                "fields": {
                    "throughput": round(float(req["total"]) / float(duration), 3),
                    "total": req["total"],
                    "ok": req["OK"],
                    "ko": req["KO"],
                    "1xx": req["1xx"],
                    "2xx": req["2xx"],
                    "3xx": req["3xx"],
                    "4xx": req["4xx"],
                    "5xx": req["5xx"],
                    "NaN": req["NaN"],
                    "min": float(req["min"]),
                    "max": float(req["max"]),
                    "mean": round(float(req["mean"]), 2),
                    "pct50": req["pct50"],
                    "pct75": req["pct75"],
                    "pct90": req["pct90"],
                    "pct95": req["pct95"],
                    "pct99": req["pct99"],
                }
            }
            points.append(influx_record)

        # Summary
        points.append({"measurement": "api_comparison", "tags": {"simulation": self.args['simulation'],
                                                                 "env": self.args['env'], "users": user_count,
                                                                 "test_type": self.args['type'], "duration": duration,
                                                                 "build_id": self.args['build_id'],
                                                                 "request_name": "All", "method": "All"},
                       "time": datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%SZ'),
                       "fields": {"throughput": _throughput, "total": total_requests_count,
                                  "ok": sum(point['fields']['ok'] for point in points),
                                  "ko": sum(point['fields']['ko'] for point in points),
                                  "1xx": sum(point['fields']['1xx'] for point in points),
                                  "2xx": sum(point['fields']['2xx'] for point in points),
                                  "3xx": sum(point['fields']['3xx'] for point in points),
                                  "4xx": sum(point['fields']['4xx'] for point in points),
                                  "5xx": sum(point['fields']['5xx'] for point in points),
                                  "NaN": sum(point['fields']['NaN'] for point in points),
                                  "min": response_times["min"], "max": response_times["max"],
                                  "mean": response_times["mean"], "pct50": response_times["pct50"],
                                  "pct75": response_times["pct75"], "pct90": response_times["pct90"],
                                  "pct95": response_times["pct95"], "pct99": response_times["pct99"]}})
        try:
            self.client.switch_database(self.args['comparison_db'])
            self.client.write_points(points)
        except Exception as e:
            print(e)
            print("Failed connection to " + self.args["influx_host"] + ", database - comparison")
        return user_count, duration, response_times

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

    def compare_with_baseline(self, baseline=None, last_build=None):
        if not baseline:
            baseline = self.get_baseline()
        if not last_build:
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
            metric = request[threshold['aggregation']] if threshold['aggregation'] != "avg" else request["mean"]
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