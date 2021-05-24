ARGS = {"type": "default", "simulation": "Flood", "build_id": "build_a8dda4ba", "env": "demo",
        "influx_host": "localhost", "influx_port": "8086", "influx_user": "admin", "influx_password": "password",
        "comparison_metric": "pct95", "influx_db": "jmeter_1", "comparison_db": "comparison_1",
        "thresholds_db": "thresholds", "test_limit": 5, "lg_id": "Lg_28036_6144", "error_logs": "/tmp/"}

TEST_DATA = [{'time': '2021-05-21T18:48:19Z', '1xx': 0, '2xx': 19, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0,
              'build_id': 'build_286851b9-e5c2-4394-9469-62150a6ad5bd', 'duration': '29', 'env': 'demo', 'ko': 1,
              'max': 1142, 'mean': 415.37, 'method': 'All', 'min': 208, 'ok': 18, 'pct50': 420, 'pct75': 425,
              'pct90': 429, 'pct95': 502, 'pct99': 1014, 'request_name': 'All', 'simulation': 'Flood',
              'test_type': 'default', 'throughput': 0.6551724137931034, 'total': 19, 'users': '1'},
             {'time': '2021-05-21T18:48:19Z', '1xx': 0, '2xx': 2, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0,
              'build_id': 'build_286851b9-e5c2-4394-9469-62150a6ad5bd', 'duration': '29', 'env': 'demo', 'ko': 0,
              'max': 208, 'mean': 208, 'method': 'GET', 'min': 208, 'ok': 2, 'pct50': 208, 'pct75': 208, 'pct90': 208,
              'pct95': 208, 'pct99': 208, 'request_name': 'Step5_Get_Code', 'simulation': 'Flood',
              'test_type': 'default', 'throughput': 0.069, 'total': 2, 'users': '1'},
             {'time': '2021-05-21T18:48:19Z', '1xx': 0, '2xx': 2, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0,
              'build_id': 'build_286851b9-e5c2-4394-9469-62150a6ad5bd', 'duration': '29', 'env': 'demo', 'ko': 1,
              'max': 418, 'mean': 417, 'method': 'GET', 'min': 416, 'ok': 1, 'pct50': 417, 'pct75': 417, 'pct90': 417,
              'pct95': 417, 'pct99': 417, 'request_name': 'Step5', 'simulation': 'Flood', 'test_type': 'default',
              'throughput': 0.069, 'total': 2, 'users': '1'},
             {'time': '2021-05-21T18:48:19Z', '1xx': 0, '2xx': 3, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0,
              'build_id': 'build_286851b9-e5c2-4394-9469-62150a6ad5bd', 'duration': '29', 'env': 'demo', 'ko': 0,
              'max': 421, 'mean': 419.67, 'method': 'GET', 'min': 418, 'ok': 3, 'pct50': 420, 'pct75': 420,
              'pct90': 420, 'pct95': 420, 'pct99': 420, 'request_name': 'Step4', 'simulation': 'Flood',
              'test_type': 'default', 'throughput': 0.103, 'total': 3, 'users': '1'},
             {'time': '2021-05-21T18:48:19Z', '1xx': 0, '2xx': 3, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0,
              'build_id': 'build_286851b9-e5c2-4394-9469-62150a6ad5bd', 'duration': '29', 'env': 'demo', 'ko': 0,
              'max': 426, 'mean': 420.67, 'method': 'GET', 'min': 416, 'ok': 3, 'pct50': 420, 'pct75': 423,
              'pct90': 424, 'pct95': 425, 'pct99': 425, 'request_name': 'Step3', 'simulation': 'Flood',
              'test_type': 'default', 'throughput': 0.103, 'total': 3, 'users': '1'},
             {'time': '2021-05-21T18:48:19Z', '1xx': 0, '2xx': 3, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0,
              'build_id': 'build_286851b9-e5c2-4394-9469-62150a6ad5bd', 'duration': '29', 'env': 'demo', 'ko': 0,
              'max': 432, 'mean': 428, 'method': 'GET', 'min': 425, 'ok': 3, 'pct50': 427, 'pct75': 429, 'pct90': 431,
              'pct95': 431, 'pct99': 431, 'request_name': 'Step2', 'simulation': 'Flood', 'test_type': 'default',
              'throughput': 0.103, 'total': 3, 'users': '1'},
             {'time': '2021-05-21T18:48:19Z', '1xx': 0, '2xx': 3, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0,
              'build_id': 'build_286851b9-e5c2-4394-9469-62150a6ad5bd', 'duration': '29', 'env': 'demo', 'ko': 0,
              'max': 429, 'mean': 424, 'method': 'GET', 'min': 420, 'ok': 3, 'pct50': 423, 'pct75': 426, 'pct90': 427,
              'pct95': 428, 'pct99': 428, 'request_name': 'Step1', 'simulation': 'Flood', 'test_type': 'default',
              'throughput': 0.103, 'total': 3, 'users': '1'},
             {'time': '2021-05-21T18:48:19Z', '1xx': 0, '2xx': 3, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0,
              'build_id': 'build_286851b9-e5c2-4394-9469-62150a6ad5bd', 'duration': '29', 'env': 'demo', 'ko': 0,
              'max': 1142, 'mean': 521.67, 'method': 'GET', 'min': 211, 'ok': 3, 'pct50': 212, 'pct75': 677,
              'pct90': 956, 'pct95': 1049, 'pct99': 1123, 'request_name': 'Home_Page', 'simulation': 'Flood',
              'test_type': 'default', 'throughput': 0.103, 'total': 3, 'users': '1'}]

BASELINE = [{'time': '2021-05-18T14:50:15Z', '1xx': 0, '2xx': 19, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0,
             'build_id': 'build_a8dda4ba-c862-423e-ad4c-62a0480474a0', 'duration': '28', 'env': 'demo', 'ko': 2,
             'max': 1333, 'mean': 421.74, 'method': 'All', 'min': 206, 'ok': 17, 'pct50': 416, 'pct75': 419,
             'pct90': 424, 'pct95': 514, 'pct99': 1169, 'request_name': 'All', 'simulation': 'Flood',
             'test_type': 'default', 'throughput': 0.6785714285714286, 'total': 19, 'users': '1'},
            {'time': '2021-05-18T14:50:15Z', '1xx': 0, '2xx': 2, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0,
             'build_id': 'build_a8dda4ba-c862-423e-ad4c-62a0480474a0', 'duration': '28', 'env': 'demo', 'ko': 0,
             'max': 207, 'mean': 206.5, 'method': 'GET', 'min': 206, 'ok': 2, 'pct50': 206, 'pct75': 206, 'pct90': 206,
             'pct95': 199, 'pct99': 206, 'request_name': 'Step5_Get_Code', 'simulation': 'Flood',
             'test_type': 'default', 'throughput': 0.071, 'total': 2, 'users': '1'},
            {'time': '2021-05-18T14:50:15Z', '1xx': 0, '2xx': 2, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0,
             'build_id': 'build_a8dda4ba-c862-423e-ad4c-62a0480474a0', 'duration': '28', 'env': 'demo', 'ko': 2,
             'max': 419, 'mean': 417, 'method': 'GET', 'min': 415, 'ok': 0, 'pct50': 417, 'pct75': 418, 'pct90': 418,
             'pct95': 418, 'pct99': 418, 'request_name': 'Step5', 'simulation': 'Flood', 'test_type': 'default',
             'throughput': 0.071, 'total': 2, 'users': '1'},
            {'time': '2021-05-18T14:50:15Z', '1xx': 0, '2xx': 3, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0,
             'build_id': 'build_a8dda4ba-c862-423e-ad4c-62a0480474a0', 'duration': '28', 'env': 'demo', 'ko': 0,
             'max': 416, 'mean': 414.67, 'method': 'GET', 'min': 414, 'ok': 3, 'pct50': 414, 'pct75': 415, 'pct90': 415,
             'pct95': 415, 'pct99': 415, 'request_name': 'Step4', 'simulation': 'Flood', 'test_type': 'default',
             'throughput': 0.107, 'total': 3, 'users': '1'},
            {'time': '2021-05-18T14:50:15Z', '1xx': 0, '2xx': 3, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0,
             'build_id': 'build_a8dda4ba-c862-423e-ad4c-62a0480474a0', 'duration': '28', 'env': 'demo', 'ko': 0,
             'max': 417, 'mean': 416.33, 'method': 'GET', 'min': 416, 'ok': 3, 'pct50': 416, 'pct75': 416, 'pct90': 416,
             'pct95': 300, 'pct99': 416, 'request_name': 'Step3', 'simulation': 'Flood', 'test_type': 'default',
             'throughput': 0.107, 'total': 3, 'users': '1'},
            {'time': '2021-05-18T14:50:15Z', '1xx': 0, '2xx': 3, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0,
             'build_id': 'build_a8dda4ba-c862-423e-ad4c-62a0480474a0', 'duration': '28', 'env': 'demo', 'ko': 0,
             'max': 424, 'mean': 421.33, 'method': 'GET', 'min': 420, 'ok': 3, 'pct50': 420, 'pct75': 422, 'pct90': 423,
             'pct95': 423, 'pct99': 423, 'request_name': 'Step2', 'simulation': 'Flood', 'test_type': 'default',
             'throughput': 0.107, 'total': 3, 'users': '1'},
            {'time': '2021-05-18T14:50:15Z', '1xx': 0, '2xx': 3, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0,
             'build_id': 'build_a8dda4ba-c862-423e-ad4c-62a0480474a0', 'duration': '28', 'env': 'demo', 'ko': 0,
             'max': 424, 'mean': 420, 'method': 'GET', 'min': 418, 'ok': 3, 'pct50': 418, 'pct75': 421, 'pct90': 422,
             'pct95': 423, 'pct99': 423, 'request_name': 'Step1', 'simulation': 'Flood', 'test_type': 'default',
             'throughput': 0.107, 'total': 3, 'users': '1'},
            {'time': '2021-05-18T14:50:15Z', '1xx': 0, '2xx': 3, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0,
             'build_id': 'build_a8dda4ba-c862-423e-ad4c-62a0480474a0', 'duration': '28', 'env': 'demo', 'ko': 0,
             'max': 1333, 'mean': 583, 'method': 'GET', 'min': 208, 'ok': 3, 'pct50': 208, 'pct75': 770, 'pct90': 1108,
             'pct95': 1220, 'pct99': 1310, 'request_name': 'Home_Page', 'simulation': 'Flood', 'test_type': 'default',
             'throughput': 0.107, 'total': 3, 'users': '1'}]

THRESHOLDS = [
    {'id': 1, 'project_id': 1, 'test': 'Flood', 'environment': 'demo', 'scope': 'all', 'yellow': 5.0, 'red': 10.0,
     'target': 'throughput', 'aggregation': 'max', 'comparison': 'lte'},
    {'id': 2, 'project_id': 1, 'test': 'Flood', 'environment': 'demo', 'scope': 'Step1', 'yellow': 150.0, 'red': 200.0,
     'target': 'response_time', 'aggregation': 'pct95', 'comparison': 'gte'},
    {'id': 4, 'project_id': 1, 'test': 'Flood', 'environment': 'demo', 'scope': 'every', 'yellow': 5.0, 'red': 10.0,
     'target': 'error_rate', 'aggregation': 'max', 'comparison': 'gte'}]

ALL_METRICS_REQUEST = "http://localhost:8086/query?q=select+max%28response_time%29%2C+min%28response_time%29%2C+ROUND%28MEAN%28response_time%29%29+as+avg%2C+PERCENTILE%28response_time%2C+95%29+as+pct95%2C+PERCENTILE%28response_time%2C+50%29+as+pct50+from+Flood+where+build_id%3D%27build_a8dda4ba%27&db=jmeter_1"

ALL_METRICS_RESPONSE = {'results': [{'statement_id': 0, 'series': [
    {'name': 'Flood', 'columns': ['time', 'max', 'min', 'avg', 'pct95', 'pct50'],
     'values': [['1970-01-01T00:00:00Z', 1142, 208, 415, 432, 420]]}]}]}

TP_REQUEST = "http://localhost:8086/query?q=select++sum%28throughput%29+as+%22throughput%22%2C+sum%28ko%29+as+%22ko%22%2C+sum%28total%29+as+%22total%22+from+api_comparison+where+build_id%3D%27build_a8dda4ba%27&db=comparison_1"

TP_RESPONSE = {'results': [{'statement_id': 0, 'series': [
    {'name': 'api_comparison', 'columns': ['time', 'throughput', 'ko', 'total'],
     'values': [['1970-01-01T00:00:00Z', 1.3081724137931032, 2, 38]]}]}]}

total_requests_count_request = "http://localhost:8086/query?q=select+count%28%22response_time%22%29+from+Flood+where+build_id%3D%27build_a8dda4ba%27&db=jmeter_1"

total_requests_count_response = {'results': [{'statement_id': 0, 'series': [{'name': 'Flood', 'columns': ['time', 'count'], 'values': [['1970-01-01T00:00:00Z', 20]]}]}]}

user_count_request = "http://localhost:8086/query?q=select+sum%28%22max%22%29+from+%28select+max%28%22user_count%22%29+from+%22users%22+where+build_id%3D%27build_a8dda4ba%27+group+by+lg_id%29&db=jmeter_1"

user_count_response = {'results': [{'statement_id': 0, 'series': [{'name': 'users', 'columns': ['time', 'sum'], 'values': [['1970-01-01T00:00:00Z', 1]]}]}]}

request_names_request = "http://localhost:8086/query?q=show+tag+values+on+jmeter_1+from+Flood+with+key%3D%22request_name%22+where+build_id%3D%27build_a8dda4ba%27&db=jmeter_1"

request_names_response = {'results': [{'statement_id': 0, 'series': [{'name': 'Flood', 'columns': ['key', 'value'], 'values': [['request_name', 'Home_Page'], ['request_name', 'Step1'], ['request_name', 'Step2'], ['request_name', 'Step3'], ['request_name', 'Step4'], ['request_name', 'Step5'], ['request_name', 'Step5_Get_Code']]}]}]}

methods_request = "http://localhost:8086/query?q=show+tag+values+on+jmeter_1+from+Flood+with+key%3D%22method%22+where+build_id%3D%27build_a8dda4ba%27+and+request_name%3D%27{}%27&db=jmeter_1"

methods_response = {'results': [{'statement_id': 0, 'series': [{'name': 'Flood', 'columns': ['key', 'value'], 'values': [['method', 'GET']]}]}]}

first_request = "http://localhost:8086/query?q=select+first%28%22response_time%22%29+from+Flood+where+build_id%3D%27build_a8dda4ba%27&db=jmeter_1"

first_response = {'results': [{'statement_id': 0, 'series': [{'name': 'Flood', 'columns': ['time', 'first'], 'values': [['2021-05-24T13:25:58.686Z', 1121]]}]}]}

last_request = "http://localhost:8086/query?q=select+last%28%22response_time%22%29+from+Flood+where+build_id%3D%27build_a8dda4ba%27&db=jmeter_1"

last_response = {'results': [{'statement_id': 0, 'series': [{'name': 'Flood', 'columns': ['time', 'last'], 'values': [['2021-05-24T13:26:26.414Z', 206]]}]}]}

total_request = "http://localhost:8086/query?q=select+count%28%22response_time%22%29+from+Flood+where+build_id%3D%27build_a8dda4ba%27+and+request_name%3D%27{}%27+and+method%3D%27GET%27&db=jmeter_1"

total_response = {'results': [{'statement_id': 0, 'series': [{'name': 'Flood', 'columns': ['time', 'count'], 'values': [['1970-01-01T00:00:00Z', 3]]}]}]}

step5_total_response = {'results': [{'statement_id': 0, 'series': [{'name': 'Flood', 'columns': ['time', 'count'], 'values': [['1970-01-01T00:00:00Z', 2]]}]}]}

response_time_request = "http://localhost:8086/query?q=select+response_time+from+Flood+where+build_id%3D%27build_a8dda4ba%27+and+request_name%3D%27{}%27+and+method%3D%27GET%27&db=jmeter_1"

home_page_response_time_response = {'results': [{'statement_id': 0, 'series': [{'name': 'Flood', 'columns': ['time', 'response_time'], 'values': [['2021-05-24T13:25:58.686Z', 1121], ['2021-05-24T13:26:09.983Z', 207], ['2021-05-24T13:26:19.5Z', 209]]}]}]}

step1_response_time_response = {'results': [{'statement_id': 0, 'series': [{'name': 'Flood', 'columns': ['time', 'response_time'], 'values': [['2021-05-24T13:26:00.111Z', 427], ['2021-05-24T13:26:11.404Z', 421], ['2021-05-24T13:26:20.921Z', 420]]}]}]}

step2_response_time_response = {'results': [{'statement_id': 0, 'series': [{'name': 'Flood', 'columns': ['time', 'response_time'], 'values': [['2021-05-24T13:26:03.233Z', 424], ['2021-05-24T13:26:12.854Z', 420], ['2021-05-24T13:26:22.373Z', 419]]}]}]}

step3_response_time_response = {'results': [{'statement_id': 0, 'series': [{'name': 'Flood', 'columns': ['time', 'response_time'], 'values': [['2021-05-24T13:26:04.653Z', 417], ['2021-05-24T13:26:14.273Z', 416], ['2021-05-24T13:26:23.79Z', 420]]}]}]}

step4_response_time_response = {'results': [{'statement_id': 0, 'series': [{'name': 'Flood', 'columns': ['time', 'response_time'], 'values': [['2021-05-24T13:26:06.075Z', 416], ['2021-05-24T13:26:15.657Z', 417], ['2021-05-24T13:26:25.207Z', 415]]}]}]}

step5_response_time_response = {'results': [{'statement_id': 0, 'series': [{'name': 'Flood', 'columns': ['time', 'response_time'], 'values': [['2021-05-24T13:26:08.774Z', 416], ['2021-05-24T13:26:18.286Z', 415]]}]}]}

step5_get_code_response_time_response = {'results': [{'statement_id': 0, 'series': [{'name': 'Flood', 'columns': ['time', 'response_time'], 'values': [['2021-05-24T13:26:07.355Z', 207], ['2021-05-24T13:26:16.869Z', 207], ['2021-05-24T13:26:26.414Z', 206]]}]}]}

ok_count_request = "http://localhost:8086/query?q=select+count%28%22response_time%22%29+from+Flood+where+build_id%3D%27build_a8dda4ba%27+and+request_name%3D%27{}%27+and+method%3D%27GET%27+and+status%3D%27OK%27&db=jmeter_1"

ko_count_request = "http://localhost:8086/query?q=select+count%28%22response_time%22%29+from+Flood+where+build_id%3D%27build_a8dda4ba%27+and+request_name%3D%27{}%27+and+method%3D%27GET%27+and+status%3D%27KO%27&db=jmeter_1"

empty_response = {'results': [{'statement_id': 0}]}

status_code_request = "http://localhost:8086/query?q=select+count%28%22response_time%22%29+from+Flood+where+build_id%3D%27build_a8dda4ba%27+and+request_name%3D%27{}%27+and+method%3D%27GET%27+and+status_code%3D~%2F%5E{}%2F&db=jmeter_1"

nan_status_code_request = "http://localhost:8086/query?q=select+count%28%22response_time%22%29+from+Flood+where+build_id%3D%27build_a8dda4ba%27+and+request_name%3D%27{}%27+and+method%3D%27GET%27+and+status_code%21~%2F1%2F+and+status_code%21~%2F2%2F+and+status_code%21~%2F3%2F+and+status_code%21~%2F4%2F+and+status_code%21~%2F5%2F&db=jmeter_1"

write_request = "http://localhost:8086/write?db=comparison_1"

last_build_request = "http://localhost:8086/query?q=select+%2A+from+api_comparison+where+build_id%3D%27build_a8dda4ba%27&db=comparison_1"

last_build_response = {'results': [{'statement_id': 0, 'series': [{'name': 'api_comparison', 'columns': ['time', '1xx', '2xx', '3xx', '4xx', '5xx', 'NaN', 'build_id', 'duration', 'env', 'ko', 'max', 'mean', 'method', 'min', 'ok', 'pct50', 'pct75', 'pct90', 'pct95', 'pct99', 'request_name', 'simulation', 'test_type', 'throughput', 'total', 'users'], 'values': [['2021-05-24T17:37:47Z', 0, 20, 0, 0, 0, 0, 'build_4a33854a-1900-47ca-9757-6ca47bf89358', '29', 'demo', 0, 1127, 403.85, 'All', 207, 20, 420, 424, 426, 462, 994, 'All', 'Flood', 'default', 0.6896551724137931, 20, '1'], ['2021-05-24T17:37:47Z', 0, 3, 0, 0, 0, 0, 'build_4a33854a-1900-47ca-9757-6ca47bf89358', '29', 'demo', 0, 208, 207.67, 'GET', 207, 3, 208, 208, 208, 208, 208, 'Step5_Get_Code', 'Flood', 'default', 0.103, 3, '1'], ['2021-05-24T17:37:47Z', 0, 2, 0, 0, 0, 0, 'build_4a33854a-1900-47ca-9757-6ca47bf89358', '29', 'demo', 0, 424, 421, 'GET', 418, 2, 421, 422, 423, 423, 423, 'Step5', 'Flood', 'default', 0.069, 2, '1'], ['2021-05-24T17:37:47Z', 0, 3, 0, 0, 0, 0, 'build_4a33854a-1900-47ca-9757-6ca47bf89358', '29', 'demo', 0, 420, 419.67, 'GET', 419, 3, 420, 420, 420, 420, 420, 'Step4', 'Flood', 'default', 0.103, 3, '1'], ['2021-05-24T17:37:47Z', 0, 3, 0, 0, 0, 0, 'build_4a33854a-1900-47ca-9757-6ca47bf89358', '29', 'demo', 0, 421, 419.33, 'GET', 418, 3, 419, 420, 420, 420, 420, 'Step3', 'Flood', 'default', 0.103, 3, '1'], ['2021-05-24T17:37:47Z', 0, 3, 0, 0, 0, 0, 'build_4a33854a-1900-47ca-9757-6ca47bf89358', '29', 'demo', 0, 426, 425, 'GET', 424, 3, 425, 425, 425, 425, 425, 'Step2', 'Flood', 'default', 0.103, 3, '1'], ['2021-05-24T17:37:47Z', 0, 3, 0, 0, 0, 0, 'build_4a33854a-1900-47ca-9757-6ca47bf89358', '29', 'demo', 0, 428, 424.33, 'GET', 421, 3, 424, 426, 427, 427, 427, 'Step1', 'Flood', 'default', 0.103, 3, '1'], ['2021-05-24T17:37:47Z', 0, 3, 0, 0, 0, 0, 'build_4a33854a-1900-47ca-9757-6ca47bf89358', '29', 'demo', 0, 1127, 515.67, 'GET', 210, 3, 210, 668, 943, 1035, 1108, 'Home_Page', 'Flood', 'default', 0.103, 3, '1']]}]}]}

last_build = [{'time': '2021-05-24T17:37:47Z', '1xx': 0, '2xx': 20, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0, 'build_id': 'build_4a33854a-1900-47ca-9757-6ca47bf89358', 'duration': '29', 'env': 'demo', 'ko': 0, 'max': 1127, 'mean': 403.85, 'method': 'All', 'min': 207, 'ok': 20, 'pct50': 420, 'pct75': 424, 'pct90': 426, 'pct95': 462, 'pct99': 994, 'request_name': 'All', 'simulation': 'Flood', 'test_type': 'default', 'throughput': 0.6896551724137931, 'total': 20, 'users': '1'}, {'time': '2021-05-24T17:37:47Z', '1xx': 0, '2xx': 3, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0, 'build_id': 'build_4a33854a-1900-47ca-9757-6ca47bf89358', 'duration': '29', 'env': 'demo', 'ko': 0, 'max': 208, 'mean': 207.67, 'method': 'GET', 'min': 207, 'ok': 3, 'pct50': 208, 'pct75': 208, 'pct90': 208, 'pct95': 208, 'pct99': 208, 'request_name': 'Step5_Get_Code', 'simulation': 'Flood', 'test_type': 'default', 'throughput': 0.103, 'total': 3, 'users': '1'}, {'time': '2021-05-24T17:37:47Z', '1xx': 0, '2xx': 2, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0, 'build_id': 'build_4a33854a-1900-47ca-9757-6ca47bf89358', 'duration': '29', 'env': 'demo', 'ko': 0, 'max': 424, 'mean': 421, 'method': 'GET', 'min': 418, 'ok': 2, 'pct50': 421, 'pct75': 422, 'pct90': 423, 'pct95': 423, 'pct99': 423, 'request_name': 'Step5', 'simulation': 'Flood', 'test_type': 'default', 'throughput': 0.069, 'total': 2, 'users': '1'}, {'time': '2021-05-24T17:37:47Z', '1xx': 0, '2xx': 3, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0, 'build_id': 'build_4a33854a-1900-47ca-9757-6ca47bf89358', 'duration': '29', 'env': 'demo', 'ko': 0, 'max': 420, 'mean': 419.67, 'method': 'GET', 'min': 419, 'ok': 3, 'pct50': 420, 'pct75': 420, 'pct90': 420, 'pct95': 420, 'pct99': 420, 'request_name': 'Step4', 'simulation': 'Flood', 'test_type': 'default', 'throughput': 0.103, 'total': 3, 'users': '1'}, {'time': '2021-05-24T17:37:47Z', '1xx': 0, '2xx': 3, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0, 'build_id': 'build_4a33854a-1900-47ca-9757-6ca47bf89358', 'duration': '29', 'env': 'demo', 'ko': 0, 'max': 421, 'mean': 419.33, 'method': 'GET', 'min': 418, 'ok': 3, 'pct50': 419, 'pct75': 420, 'pct90': 420, 'pct95': 420, 'pct99': 420, 'request_name': 'Step3', 'simulation': 'Flood', 'test_type': 'default', 'throughput': 0.103, 'total': 3, 'users': '1'}, {'time': '2021-05-24T17:37:47Z', '1xx': 0, '2xx': 3, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0, 'build_id': 'build_4a33854a-1900-47ca-9757-6ca47bf89358', 'duration': '29', 'env': 'demo', 'ko': 0, 'max': 426, 'mean': 425, 'method': 'GET', 'min': 424, 'ok': 3, 'pct50': 425, 'pct75': 425, 'pct90': 425, 'pct95': 425, 'pct99': 425, 'request_name': 'Step2', 'simulation': 'Flood', 'test_type': 'default', 'throughput': 0.103, 'total': 3, 'users': '1'}, {'time': '2021-05-24T17:37:47Z', '1xx': 0, '2xx': 3, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0, 'build_id': 'build_4a33854a-1900-47ca-9757-6ca47bf89358', 'duration': '29', 'env': 'demo', 'ko': 0, 'max': 428, 'mean': 424.33, 'method': 'GET', 'min': 421, 'ok': 3, 'pct50': 424, 'pct75': 426, 'pct90': 427, 'pct95': 427, 'pct99': 427, 'request_name': 'Step1', 'simulation': 'Flood', 'test_type': 'default', 'throughput': 0.103, 'total': 3, 'users': '1'}, {'time': '2021-05-24T17:37:47Z', '1xx': 0, '2xx': 3, '3xx': 0, '4xx': 0, '5xx': 0, 'NaN': 0, 'build_id': 'build_4a33854a-1900-47ca-9757-6ca47bf89358', 'duration': '29', 'env': 'demo', 'ko': 0, 'max': 1127, 'mean': 515.67, 'method': 'GET', 'min': 210, 'ok': 3, 'pct50': 210, 'pct75': 668, 'pct90': 943, 'pct95': 1035, 'pct99': 1108, 'request_name': 'Home_Page', 'simulation': 'Flood', 'test_type': 'default', 'throughput': 0.103, 'total': 3, 'users': '1'}]

error = {"Request name": "Step5", "Method": "GET", "Request headers": "Connection: keep-alive Accept-Language: ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3 Accept-Encoding: gzip, deflate, br ", "Error count": 2, "Response code": "200", "Request URL": "https://challengers.flood.io/done", "Request_params": ["[]"], "Response": ["<!DOCTYPE html> <html lang=en> <head> <link href=/assets/application-83a5b9f2e1580179c228e00b1276d04c.css media=all rel=stylesheet /> <script src=/assets/application-5e48982641645e9e430e258fb10a8f85.js></script> <link href=https://maxcdn.bootstrapcdn.com/bootstrap/3.3.0/css/bootstrap.min.css rel=stylesheet> <title>Flood IO Script Challenge</title> </head> <body class=challengers done> <div class=main> <div class=container> <div class=row> <div class=page-title> <div class=container> <div class=row> <div class=span12> <h4> <img alt=Flood logo black height=50 src=/assets/flood_logo_black-2f37da5375643a3756df3dfe52cdb75a.png width=200 /> </h4> </div> </div> </div> </div> <div class=container> <div class=row> <div class=span12> <h2> Youre Done! </h2> <p class=lead> Thats it. You just walked through the test manually, nows the time to start scripting the steps to get to this point. <h3> Want to enter our Hall of Fame? </h3> <p> <mark> Pay attention to the following details! </mark> </p> <ul> <li> Send us a link to your Flood <a href=https://flood.io/P2oO7ZyU>load test results</a> at <strong> challengers@flood.io </strong> </li> <li> Include a <strong> User-Agent </strong> header with the words <strong> I AM ROBOT </strong> so that we know its not a human attempt. </li> <li> Make sure you only test the target site at <strong> training.flooded.io </strong> </li> <li> Ensure you match our target of <strong> 50 concurrent users </strong> </li> <li> Make sure your transaction rate is between <strong> 8,000 to 10,000 requests per minute </strong> </li> <li> We wont accept results with errors </li> </ul> <p> <a class=btn href=/>Start Again</a> </p> </p> </div> </div> </div> </div> </div> </div> </body> </html> OK"], "Error_message": ["[Test failed: text expected to contain /You're Done!!!/]"]}

compare_with_baseline = [{'request_name': 'Step5_Get_Code', 'response_time': 208, 'baseline': 199}, {'request_name': 'Step4', 'response_time': 420, 'baseline': 415}, {'request_name': 'Step3', 'response_time': 425, 'baseline': 300}, {'request_name': 'Step2', 'response_time': 431, 'baseline': 423}, {'request_name': 'Step1', 'response_time': 428, 'baseline': 423}]

baseline_rate = 62.5

compare_with_thresholds = [{'request_name': 'All', 'target': 'error_rate', 'aggregation': 'max', 'metric': 5.26, 'threshold': 'yellow', 'yellow': 5.0, 'red': 10.0}, {'request_name': 'Step5_Get_Code', 'target': 'error_rate', 'aggregation': 'max', 'metric': 0.0, 'threshold': 'green', 'yellow': 5.0, 'red': 10.0}, {'request_name': 'Step5', 'target': 'error_rate', 'aggregation': 'max', 'metric': 50.0, 'threshold': 'red', 'yellow': 5.0, 'red': 10.0}, {'request_name': 'Step4', 'target': 'error_rate', 'aggregation': 'max', 'metric': 0.0, 'threshold': 'green', 'yellow': 5.0, 'red': 10.0}, {'request_name': 'Step3', 'target': 'error_rate', 'aggregation': 'max', 'metric': 0.0, 'threshold': 'green', 'yellow': 5.0, 'red': 10.0}, {'request_name': 'Step2', 'target': 'error_rate', 'aggregation': 'max', 'metric': 0.0, 'threshold': 'green', 'yellow': 5.0, 'red': 10.0}, {'request_name': 'Step1', 'target': 'response_time', 'aggregation': 'pct95', 'metric': 428, 'threshold': 'red', 'yellow': 150.0, 'red': 200.0}, {'request_name': 'Step1', 'target': 'error_rate', 'aggregation': 'max', 'metric': 0.0, 'threshold': 'green', 'yellow': 5.0, 'red': 10.0}, {'request_name': 'Home_Page', 'target': 'error_rate', 'aggregation': 'max', 'metric': 0.0, 'threshold': 'green', 'yellow': 5.0, 'red': 10.0}, {'request_name': 'all', 'target': 'throughput', 'aggregation': 'max', 'metric': 1.31, 'threshold': 'red', 'yellow': 5.0, 'red': 10.0}]

threshold_rate = 40.0

error_string = "Flood_https://challengers.flood.io/done_[\"[Test failed: text expected to contain /You're Done!!!/]\"]_Step5"

rp_get_project_request = "https://rp.com/my_project"

rp_url = "https://rp.com/"

html_str = "&#39; &#47; %3A %2F %2E &amp; &gt; %7C &lt;"

decoded_html_string = "' / : / . & > | <"
