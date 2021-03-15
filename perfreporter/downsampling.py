from influxdb import InfluxDBClient
import pandas as pd
from time import sleep, time


SELECT_REQUESTS_DATA = 'select response_time, request_name, method, status, status_code from {} ' \
                       'where time>\'{}\''
SELECT_USERS_DATA = 'select active from "users" where time>\'{}\''


class Downsampler(object):
    def __init__(self, arguments):
        self.args = arguments

    def resample_results(self, requests, aggregation, status):
        downsampled_array = []
        start_time_ = time()
        for req in requests:
            _response_times = [0 if v is None else v for v in requests[req]["response_times"]]
            dti = pd.to_datetime(requests[req]["timestamps"])
            rt_ts = pd.Series(_response_times, index=dti)
            total = rt_ts.resample(aggregation, label='right').count()
            min_ = rt_ts.resample(aggregation, label='right').min()
            max_ = rt_ts.resample(aggregation, label='right').max()
            median = rt_ts.resample(aggregation, label='right').median()
            pct_90 = rt_ts.resample(aggregation, label='right').quantile(0.9)
            pct_95 = rt_ts.resample(aggregation, label='right').quantile(0.95)
            pct_99 = rt_ts.resample(aggregation, label='right').quantile(0.99)
            status_codes = {}
            for status_code in ["1xx", "2xx", "3xx", "4xx", "5xx", "NaN"]:
                sc_ts = pd.Series(requests[req][status_code], index=dti)
                status_codes[status_code] = sc_ts.resample(aggregation, label='right').sum()

            _timestamps = list(total.keys())
            for i in range(len(total)):
                try:
                    if int(total.iloc[i]) != 0:
                        downsampled_array.append({
                            "time": _timestamps[i].to_pydatetime().strftime('%Y-%m-%dT%H:%M:%SZ'),
                            "request_name": requests[req]["request_name"],
                            "method": requests[req]["method"],
                            "status": status,
                            "total": total.iloc[i],
                            "min": int(min_.iloc[i]),
                            "max": int(max_.iloc[i]),
                            "median": int(median.iloc[i]),
                            "pct90": int(pct_90.iloc[i]),
                            "pct95": int(pct_95.iloc[i]),
                            "pct99": int(pct_99.iloc[i]),
                            "1xx": status_codes["1xx"].iloc[i],
                            "2xx": status_codes["2xx"].iloc[i],
                            "3xx": status_codes["3xx"].iloc[i],
                            "4xx": status_codes["4xx"].iloc[i],
                            "5xx": status_codes["5xx"].iloc[i],
                            "NaN": status_codes["NaN"].iloc[i],
                        })
                except Exception:
                    pass
        print(f"Downsampling time for {aggregation} -  {round(time() - start_time_, 2)} seconds")
        return downsampled_array

    def resample_and_send_to_influx(self, client, args, ok_requests, ko_requests, aggregation, iteration):
        requests = self.resample_results(ok_requests, aggregation, "OK")
        requests.extend(self.resample_results(ko_requests, aggregation, "KO"))
        points = []
        for req in requests:
            sampler_type = "TRANSACTION" if req['method'] == "TRANSACTION" else "REQUEST"
            influx_record = {
                "measurement": f"{args['simulation']}_{aggregation.replace('T', 'm').lower()}",
                "tags": {
                    "iteration": iteration,
                    "simulation": args['simulation'],
                    "env": args['env'],
                    "test_type": args['type'],
                    "build_id": args['build_id'],
                    "lg_id": args['lg_id'],
                    "request_name": req['request_name'],
                    "method": req['method'],
                    "sampler_type": sampler_type,
                },
                "time": req["time"],
                "fields": {
                    "total": req["total"],
                    "status": req["status"],
                    "1xx": req["1xx"],
                    "2xx": req["2xx"],
                    "3xx": req["3xx"],
                    "4xx": req["4xx"],
                    "5xx": req["5xx"],
                    "NaN": req["NaN"],
                    "min": req["min"],
                    "max": req["max"],
                    "median": req["median"],
                    "pct90": req["pct90"],
                    "pct95": req["pct95"],
                    "pct99": req["pct99"],
                }
            }
            points.append(influx_record)
        client.write_points(points)

    def resample_users_and_send_to_influx(self, client, args, users_data, aggregation):
        downsampled_array = []
        users_ts = pd.Series(users_data["active"], index=pd.to_datetime(users_data["timestamps"]))
        active = users_ts.resample(aggregation, label='right').max()
        _timestamps = list(active.keys())
        for i in range(len(active)):
            try:
                downsampled_array.append({
                    "time": _timestamps[i].to_pydatetime().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "active": int(active.iloc[i]),
                })
            except Exception:
                pass
        points = []
        for _each in downsampled_array:
            influx_record = {
                "measurement": f"users_{aggregation.replace('T', 'm').lower()}",
                "tags": {
                    "simulation": args['simulation'],
                    "env": args['env'],
                    "test_type": args['type'],
                    "build_id": args['build_id'],
                    "lg_id": args['lg_id'],
                },
                "time": _each["time"],
                "fields": {
                    "active": _each["active"],
                }
            }
            points.append(influx_record)
        client.write_points(points)

    def aggregate_results(self, _results):
        _ok_requests = {}
        _ko_requests = {}
        for each in _results:
            if each["status"] == "OK":
                self.append_request(_ok_requests, each)
            else:
                self.append_request(_ko_requests, each)
        return _ok_requests, _ko_requests

    def append_request(self, requests, req):
        key = f"{req['request_name']}_{req['method']}"
        if key not in requests:
            requests[key] = {
                "timestamps": [req["time"]],
                "request_name": req["request_name"],
                "method": req["method"],
                "response_times": [req["response_time"]],
                "1xx": [],
                "2xx": [],
                "3xx": [],
                "4xx": [],
                "5xx": [],
                'NaN': []
            }

            if "{}xx".format(str(req['status_code'])[0]) in requests[key]:
                requests[key]["NaN"].append(0)
                for status_code in ["1xx", "2xx", "3xx", "4xx", "5xx"]:
                    if status_code[0] == str(req['status_code'])[0]:
                        requests[key][status_code].append(1)
                    else:
                        requests[key][status_code].append(0)
            else:
                requests[key]["NaN"].append(1)
                for status_code in ["1xx", "2xx", "3xx", "4xx", "5xx"]:
                    requests[key][status_code].append(0)
        else:
            requests[key]["timestamps"].append(req["time"])
            requests[key]["response_times"].append(req["response_time"])
            if "{}xx".format(str(req['status_code'])[0]) in requests[key]:
                requests[key]["NaN"].append(0)
                for status_code in ["1xx", "2xx", "3xx", "4xx", "5xx"]:
                    if status_code[0] == str(req['status_code'])[0]:
                        requests[key][status_code].append(1)
                    else:
                        requests[key][status_code].append(0)
            else:
                requests[key]["NaN"].append(1)
                for status_code in ["1xx", "2xx", "3xx", "4xx", "5xx"]:
                    requests[key][status_code].append(0)

    def append_to_batch(self, batch, requests):
        for key in requests:
            if key not in list(batch.keys()):
                batch[key] = requests[key]
            else:
                for each in ["timestamps", "response_times", "1xx", "2xx", "3xx", "4xx", "5xx", "NaN"]:
                    batch[key][each].extend(requests[key][each])

    def run(self):
        external_client = InfluxDBClient(self.args["influx_host"], self.args["influx_port"], self.args["influx_user"],
                                         self.args["influx_password"], self.args["influx_db"])
        local_client = InfluxDBClient("localhost", "8086", "", "", "local")
        requests_last_read_time = '1970-01-01T19:25:26.005Z'
        users_last_read_time = '1970-01-01T19:25:26.005Z'
        iteration = 0
        processing_time = 0
        ok_requests_10min_batch, ko_requests_10min_batch, ok_requests_5min_batch, ko_requests_5min_batch = {}, {}, {}, {}
        users_10min_batch, users_5min_batch = {"timestamps": [], "active": []}, {"timestamps": [], "active": []}
        while True:
            iteration += 1
            pause = 60 - processing_time if processing_time < 60 else 1
            sleep(pause)
            tik = time()
            requests_data = list(local_client.query(SELECT_REQUESTS_DATA.format(self.args["simulation"],
                                                                                requests_last_read_time)).get_points())
            users_data = list(local_client.query(SELECT_USERS_DATA.format(users_last_read_time)).get_points())
            if requests_data:
                requests_last_read_time = requests_data[-1]['time']
                users_last_read_time = users_data[-1]['time']
                ok_requests, ko_requests = self.aggregate_results(requests_data)
                self.append_to_batch(ok_requests_5min_batch, ok_requests)
                self.append_to_batch(ko_requests_5min_batch, ko_requests)
                self.resample_and_send_to_influx(external_client, self.args, ok_requests, ko_requests, "1S", iteration)
                self.resample_and_send_to_influx(external_client, self.args, ok_requests, ko_requests, "5S", iteration)
                self.resample_and_send_to_influx(external_client, self.args, ok_requests, ko_requests, "30S", iteration)

                # Resample users data
                users = {"timestamps": [], "active": []}
                for each in users_data:
                    users["timestamps"].append(each["time"])
                    users["active"].append(each["active"])
                users_5min_batch["timestamps"].extend(users["timestamps"])
                users_5min_batch["active"].extend(users["active"])
                self.resample_users_and_send_to_influx(external_client, self.args, users, "1S")
                self.resample_users_and_send_to_influx(external_client, self.args, users, "5S")
                self.resample_users_and_send_to_influx(external_client, self.args, users, "30S")

            if iteration in [5, 10]:
                self.resample_and_send_to_influx(external_client, self.args, ok_requests_5min_batch,
                                                 ko_requests_5min_batch, "1T", iteration)
                self.resample_and_send_to_influx(external_client, self.args, ok_requests_5min_batch,
                                                 ko_requests_5min_batch, "5T", iteration)
                self.append_to_batch(ok_requests_10min_batch, ok_requests_5min_batch)
                self.append_to_batch(ko_requests_10min_batch, ko_requests_5min_batch)
                del ok_requests_5min_batch
                del ko_requests_5min_batch
                ok_requests_5min_batch, ko_requests_5min_batch = {}, {}

                # Resample users data
                self.resample_users_and_send_to_influx(external_client, self.args, users_5min_batch, "1T")
                self.resample_users_and_send_to_influx(external_client, self.args, users_5min_batch, "5T")
                users_10min_batch["timestamps"].extend(users_5min_batch["timestamps"])
                users_10min_batch["active"].extend(users_5min_batch["active"])
                del users_5min_batch
                users_5min_batch = {"timestamps": [], "active": []}
            if iteration == 10:
                self.resample_and_send_to_influx(external_client, self.args, ok_requests_10min_batch,
                                                 ko_requests_10min_batch, "10T", iteration)
                del ok_requests_10min_batch
                del ko_requests_10min_batch
                ok_requests_10min_batch, ko_requests_10min_batch = {}, {}
                # Resample users data
                self.resample_users_and_send_to_influx(external_client, self.args, users_10min_batch, "10T")
                del users_10min_batch
                users_10min_batch = {"timestamps": [], "active": []}
                iteration = 0

            processing_time = round(time() - tik, 2)
            print(f"Total time - {processing_time} sec")




