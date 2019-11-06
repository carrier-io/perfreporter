from time import time
import datetime
from influxdb import InfluxDBClient
import numpy as np

SELECT_LAST_BUILD_DATA = "select * from api_comparison where build_id=\'{}\'"

SELECT_BASELINE_BUILD_ID = "select last(pct95), build_id from api_comparison where simulation=\'{}\' and " \
                           "test_type=\'{}\' and \"users\"=\'{}\' and build_id=~/audit_{}_/"

SELECT_BASELINE_DATA = "select * from api_comparison where build_id=\'{}\'"

SELECT_THRESHOLDS = "select last(red) as red, last(yellow) as yellow from threshold where request_name=\'{}\' " \
                    "and simulation=\'{}\'"

SELECT_USERS_COUNT = "select sum(\"max\") from (select max(\"user_count\") from \"users\" where " \
                     "build_id='{}' group by lg_id)"

SELECT_TEST_DATA = "select * from {} where build_id='{}'"


class DataManager(object):
    def __init__(self, arguments):
        self.args = arguments
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
        start_time = int(str(datetime.datetime.strptime(data[0]['time'],
                                                        "%Y-%m-%dT%H:%M:%S.%fZ").timestamp()).split(".")[0]) \
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
        last_build = self.append_thresholds_to_test_data(last_build)
        compare_with_thresholds = []
        comparison_metric = self.args['comparison_metric']
        for request in last_build:
            if request[comparison_metric + '_threshold'] is not 'green':
                compare_with_thresholds.append({"request_name": request['request_name'],
                                                "response_time": request[comparison_metric],
                                                "threshold": request[comparison_metric + '_threshold'],
                                                "yellow": request['yellow_threshold_value'],
                                                "red": request["red_threshold_value"]})
        missed_threshold_rate = round(float(len(compare_with_thresholds) / len(last_build)) * 100, 2)
        return missed_threshold_rate, compare_with_thresholds

    def get_baseline(self):
        self.client.switch_database(self.args['comparison_db'])
        baseline_build_id = self.client.query(
            SELECT_BASELINE_BUILD_ID.format(self.args['simulation'], self.args['type'],
                                            str(self.get_user_count()), self.args['simulation']))
        result = list(baseline_build_id.get_points())
        if len(result) == 0:
            return None
        _id = result[0]['build_id']
        baseline_data = self.client.query(SELECT_BASELINE_DATA.format(_id))
        return list(baseline_data.get_points())

    def get_last_build(self):
        if self.last_build_data:
            return self.last_build_data
        self.client.switch_database(self.args['comparison_db'])
        test_data = self.client.query(SELECT_LAST_BUILD_DATA.format(self.args['build_id']))
        self.last_build_data = list(test_data.get_points())
        return self.last_build_data

    def append_thresholds_to_test_data(self, test):
        self.client.switch_database(self.args['thresholds_db'])
        test_data_with_thresholds = []
        comparison_metric = self.args['comparison_metric']
        for request in test:
            request_data = {}
            threshold = self.client.query(SELECT_THRESHOLDS.format(str(request['request_name']),
                                                                   str(request['simulation'])))
            if len(list(threshold.get_points())) == 0:
                red_threshold = 3000
                yellow_threshold = 2000
            else:
                red_threshold = int(list(threshold.get_points())[0]['red'])
                yellow_threshold = int(list(threshold.get_points())[0]['yellow'])

            request_data['yellow_threshold_value'] = yellow_threshold
            request_data['red_threshold_value'] = red_threshold
            request_data['request_name'] = request['request_name']
            request_data[comparison_metric] = request[comparison_metric]

            if int(request[comparison_metric]) > red_threshold:
                request_data[comparison_metric + '_threshold'] = 'red'
            elif int(request[comparison_metric]) > yellow_threshold:
                request_data[comparison_metric + '_threshold'] = 'yellow'
            else:
                request_data[comparison_metric + '_threshold'] = 'green'

            test_data_with_thresholds.append(request_data)
        return test_data_with_thresholds
