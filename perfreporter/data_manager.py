from time import time
import datetime
from influxdb import InfluxDBClient
import numpy as np
import operator

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

CALCULATE_TOTAL_THROUGHPUT = "select  sum(throughput) as \"throughput\", sum(ko) as \"ko\", sum(total) as \"total\" from api_comparison where build_id='{}'"

CALCULATE_ALL_AGGREGATION = "select max(response_time), min(response_time), ROUND(MEAN(response_time)) as avg, PERCENTILE(response_time, 95) as pct95, PERCENTILE(response_time, 50) as pct50 from {} where build_id='{}'"

COMPARISON_RULES = {"gte": "ge", "lte": "le", "gt": "gt", "lt": "lt", "eq": "eq"}

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
        # last_build = self.append_thresholds_to_test_data(last_build)
        # compare_with_thresholds = []
        # comparison_metric = self.args['comparison_metric']
        # for request in last_build:
        #     if request[comparison_metric + '_threshold'] is not 'green':
        #         compare_with_thresholds.append({"request_name": request['request_name'],
        #                                         "response_time": request[comparison_metric],
        #                                         "threshold": request[comparison_metric + '_threshold'],
        #                                         "yellow": request['yellow_threshold_value'],
        #                                         "red": request["red_threshold_value"]})
        # missed_threshold_rate = round(float(len(compare_with_thresholds) / len(last_build)) * 100, 2)
        # return missed_threshold_rate, compare_with_thresholds
        return self.get_thresholds(last_build)

    def get_baseline(self):
        users = str(self.get_user_count())
        self.client.switch_database(self.args['comparison_db'])
        baseline_build_id = self.client.query(
            SELECT_BASELINE_BUILD_ID.format(self.args['simulation'], self.args['type'],
                                            users, self.args['simulation']))
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

    def compare_request_and_threhold(self, request, threshold):
        comparison_method = getattr(operator, COMPARISON_RULES[threshold['comparison']])
        if threshold['target'] == 'response_time':
            metric = request[threshold['aggregation']]
        elif threshold['target'] == 'throughput':
            metric = request['throughput']
        else:  # Will be in case error_rate is set as target
            metric = request['ko'] / request['total']
        if comparison_method(metric, threshold['red']):
            return "red", metric
        if comparison_method(metric, threshold['yellow']):
            return "yellow", metric
        return "green", metric
    
    def aggregate_test(self):
        self.client.switch_database(self.args['influx_db'])
        all_metics: list = list(self.client.query(CALCULATE_ALL_AGGREGATION.format(self.args['simulation'], self.args['build_id'])).get_points())
        self.client.switch_database(self.args['comparison_db'])
        tp: list = list(self.client.query(CALCULATE_TOTAL_THROUGHPUT.format(self.args['build_id'])).get_points())
        aggregated_dict = all_metics[0]
        aggregated_dict['throughput'] = tp[0]['throughput']
        aggregated_dict['ko'] = tp[0]['ko']
        aggregated_dict['total'] = tp[0]['total']
        aggregated_dict['request_name'] = 'all'
        return aggregated_dict        

    def get_thresholds(self, test):
        compare_with_thresholds = []
        total_checked = 0
        def compile_violation(request, th, total_checked, compare_with_thresholds):
            total_checked += 1
            color, metric = self.compare_request_and_threhold(request, th)
            if color is not "green":
                compare_with_thresholds.append({
                    "request_name": request['request_name'],
                    "target": th['target'],
                    "aggregation": th["aggregation"],
                    "metric": metric,
                    "threshold": color,
                    "yellow": th['yellow'],
                    "red": th["red"]
                })
            return total_checked, compare_with_thresholds
        self.client.switch_database(self.args['thresholds_db'])
        globaly_applicable: list = list(self.client.query(SELECT_ALL_THRESHOLDS.format(str(test[0]['simulation']), "AND scope='all'")).get_points())
        every_applicable: list = list(self.client.query(SELECT_ALL_THRESHOLDS.format(str(test[0]['simulation']), "AND scope='every'")).get_points())
        individual: list = list(self.client.query(SELECT_ALL_THRESHOLDS.format(str(test[0]['simulation']), "AND scope!='all' AND scope!='every'")).get_points())
        individual_dict:dict = dict()
        for each in individual:
            if each['scope'] not in individual_dict:
                individual_dict[each['scope']] = []
            individual_dict[each['scope']].append(each)
        for request in test:
            thresholds = every_applicable
            if request['request_name'] in individual_dict:
                thresholds.extend(individual_dict[request['request_name']])
            for th in thresholds:
                total_checked, compare_with_thresholds = compile_violation(request, th, total_checked, compare_with_thresholds)
        if globaly_applicable:
            test_data = self.aggregate_test()
            for th in globaly_applicable:
                total_checked, compare_with_thresholds = compile_violation(test_data, th, total_checked, compare_with_thresholds)
        violation = 0
        if total_checked:
            violation = round(float(len(compare_with_thresholds) / total_checked) * 100, 2)
        return violation, compare_with_thresholds

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


# if __name__ == "__main__":
#     arguments = {
#         "influx_host": "localhost",
#         "influx_port": 8086,
#         "influx_user": "",
#         "influx_password": "",
#         "influx_db": "jmeter",
#         "simulation": "Flood",
#         "comparison_db": "comparison",
#         "thresholds_db": "thresholds",
#         "build_id": "build_8a863dcc-4be6-4853-bdba-29a01e4d11c7"
#     }
#     dm = DataManager(arguments)
#     print(dm.get_thresholds(dm.get_last_build()))