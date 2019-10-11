import traceback
from time import time
import warnings
import requests
import contextlib
from reportportal_client import ReportPortalServiceAsync
from functools import partial
import hashlib


class partialmethod(partial):
    def __get__(self, instance, owner):
        if instance is None:
            return self

        return partial(self.func, instance, *(self.args or ()),
                       **(self.keywords or {}))


class ReportPortal:
    def __init__(self, arguments, rp_url, rp_token, rp_project, rp_launch_name, check_functional_errors,
                 check_performance_degradation, check_missed_thresholds, performance_degradation_rate,
                 missed_thresholds_rate):
        self.args = arguments
        self.rp_url = rp_url
        self.rp_token = rp_token
        self.rp_project = rp_project
        self.rp_launch_name = rp_launch_name
        self.check_functional_errors = check_functional_errors
        self.check_performance_degradation = check_performance_degradation
        self.check_missed_thresholds = check_missed_thresholds
        self.performance_degradation_rate = performance_degradation_rate
        self.missed_thresholds_rate = missed_thresholds_rate

    @contextlib.contextmanager
    def no_ssl_verification(self):
        old_request = requests.Session.request
        requests.Session.request = partialmethod(old_request, verify=False)

        warnings.filterwarnings('ignore', 'Unverified HTTPS request')
        yield
        warnings.resetwarnings()

        requests.Session.request = old_request

    def timestamp(self):
        return str(int(time() * 1000))

    def create_project(self):
        headers = {'authorization': 'bearer ' + self.rp_token}
        post_data = {'entryType': 'INTERNAL', 'projectName': self.rp_project}
        r = requests.get(self.rp_url + '/' + self.rp_project, headers=headers)
        if r.status_code == 404 or r.text.find(self.rp_project) == -1:
            p = requests.post(self.rp_url, json=post_data, headers=headers)

    def my_error_handler(self, exc_info):
        """
        This callback function will be called by async service client when error occurs.
        Return True if error is not critical and you want to continue work.
        :param exc_info: result of sys.exc_info() -> (type, value, traceback)
        :return:
        """
        print("Error occurred: {}".format(exc_info[1]))
        traceback.print_exception(*exc_info)

    def html_decode(self, s):
        html_codes = (
            ("'", '&#39;'),
            ("/", '&#47;'),
            ('"', '&quot;'),
            (':', '%3A'),
            ('/', '%2F'),
            ('.', '%2E'),
            ('&', '&amp;'),
            ('>', '&gt;'),
            ('|', '%7C'),
            ('<', '&lt;'),
            ('\\"', '"')
        )
        for code in html_codes:
            s = s.replace(code[1], code[0])
        return s

    def log_message(self, service, message, errors, level='WARN'):
        if errors[message] is not 'undefined':
            if isinstance(errors[message], list):
                if len(errors[message]) > 1:
                    log = ''
                    for i, error in enumerate(errors[message]):
                        log += message + ' ' + str(i + 1) + ': ' + error + ';;\n'
                    service.log(time=self.timestamp(),
                                message="{}".format(self.html_decode(log)),
                                level="{}".format(level))
                elif not str(errors[message])[2:-2].__contains__('undefined'):
                    service.log(time=self.timestamp(),
                                message="{}: {}".format(message, self.html_decode(str(errors[message])[2:-2])),
                                level="{}".format(level))
            else:
                service.log(time=self.timestamp(),
                            message="{}: {}".format(message, self.html_decode(str(errors[message]))),
                            level="{}".format(level))

    def log_unique_error_id(self, service, request_name, method, response_code):
        error_id = ""
        if method is not 'undefined':
            error_id += method + '_' + request_name
        else:
            error_id += request_name
        if response_code is not 'undefined':
            error_id += '_' + response_code
        service.log(time=self.timestamp(), message=error_id, level='ERROR')

    def get_item_name(self, entry):
        if entry['Method'] is not 'undefined' and entry['Response code'] is not 'undefined':
            return "{} {} {}".format(str(entry['Request name']),
                                     str(entry['Method']),
                                     str(entry['Response code']))
        else:
            return str(entry['Request name'])

    def report_errors(self, errors):
        with self.no_ssl_verification():
            self.create_project()
            service = ReportPortalServiceAsync(endpoint=self.rp_url, project=self.rp_project,
                                               token=self.rp_token, error_handler=self.my_error_handler)

            errors_len = len(errors)
            if errors_len > 0:
                # Start launch.
                service.start_launch(name=self.rp_launch_name + ": functional errors",
                                     start_time=self.timestamp(),
                                     description='This simulation has {} fails'.format(errors_len))
                for key in errors:
                    # Start test item.
                    item_name = self.get_item_name(errors[key])
                    service.start_test_item(name=item_name,
                                            description="This request was failed {} times".format(
                                                errors[key]['Error count']),
                                            tags=[self.args['type'], errors[key]['Request URL'], 'gatling_test'],
                                            start_time=self.timestamp(),
                                            item_type="STEP",
                                            parameters={"simulation": self.args['simulation'],
                                                        'duration': int(self.args['end_time'])/1000
                                                        - int(self.args['start_time'])/1000,
                                                        'test type': self.args['type']})

                    self.log_message(service, 'Request name', errors[key], 'WARN')
                    self.log_message(service, 'Method', errors[key], 'WARN')
                    self.log_message(service, 'Request URL', errors[key], 'WARN')
                    self.log_message(service, 'Request_params', errors[key], 'WARN')
                    self.log_message(service, 'Request headers', errors[key], 'INFO')
                    self.log_message(service, 'Error count', errors[key], 'WARN')
                    self.log_message(service, 'Error_message', errors[key], 'WARN')
                    self.log_message(service, 'Response code', errors[key], 'WARN')
                    self.log_message(service, 'Response', errors[key], 'WARN')
                    self.log_unique_error_id(service, errors[key]['Request name'], errors[key]['Method'],
                                             errors[key]['Response code'])

                    service.finish_test_item(end_time=self.timestamp(), status="FAILED")
            else:
                service.start_launch(name=self.rp_launch_name + ": functional errors",
                                     start_time=self.timestamp(),
                                     description='This simulation has no fails')

            # Finish launch.
            service.finish_launch(end_time=self.timestamp())

            service.terminate()

    def report_performance_degradation(self, performance_degradation_rate, compare_with_baseline):
        with self.no_ssl_verification():
            self.create_project()
            service = ReportPortalServiceAsync(endpoint=self.rp_url, project=self.rp_project,
                                               token=self.rp_token, error_handler=self.my_error_handler)
            if performance_degradation_rate > self.performance_degradation_rate:
                service.start_launch(name=self.rp_launch_name + ": compare with baseline",
                                     start_time=self.timestamp(),
                                     description='Performance degradation in Test: {}'.format(self.args['simulation']))
                service.start_test_item(name="Test \"{}\" failed with performance degradation rate {}"
                                        .format(self.args['simulation'], performance_degradation_rate),
                                        description='Performance degradation in Test: {}'.format(self.args['simulation']),
                                        tags=[self.args['type'], 'performance degradation', 'gatling_test'],
                                        start_time=self.timestamp(),
                                        item_type="STEP",
                                        parameters={'simulation': self.args['simulation'],
                                                    'test type': self.args['type']})

                service.log(time=self.timestamp(),
                            message="The following requests are slower than baseline:",
                            level="{}".format('INFO'))
                for request in compare_with_baseline:
                    service.log(time=self.timestamp(), message="\"{}\" reached {} ms by {}. Baseline {} ms."
                                .format(request['request_name'], request['response_time'],
                                        self.args['comparison_metric'], request['baseline']),
                                level="{}".format('WARN'))

                service.log(time=self.timestamp(), message=hashlib.sha256(
                    "{} performance degradation".format(self.args['simulation']).strip().encode('utf-8')).hexdigest(),
                            level='ERROR')
                service.finish_test_item(end_time=self.timestamp(), status="FAILED")
            else:
                service.start_launch(name=self.rp_launch_name + ": compare with baseline",
                                     start_time=self.timestamp(),
                                     description='Performance degradation rate less than {}'
                                     .format(self.performance_degradation_rate))

                # Finish launch.
            service.finish_launch(end_time=self.timestamp())

            service.terminate()

    def report_missed_thresholds(self, missed_threshold_rate, compare_with_thresholds):
        with self.no_ssl_verification():
            self.create_project()
            service = ReportPortalServiceAsync(endpoint=self.rp_url, project=self.rp_project,
                                               token=self.rp_token, error_handler=self.my_error_handler)
            if missed_threshold_rate > self.missed_thresholds_rate:
                service.start_launch(name=self.rp_launch_name + ": compare with thresholds",
                                     start_time=self.timestamp(),
                                     description='Missed thresholds in Test: {}'.format(self.args['simulation']))
                service.start_test_item(name="Test \"{}\" failed with missed thresholds rate {}"
                                        .format(self.args['simulation'], missed_threshold_rate),
                                        description='Missed thresholds in Test: {}'.format(self.args['simulation']),
                                        tags=[self.args['type'], 'missed thresholds', 'gatling_test'],
                                        start_time=self.timestamp(),
                                        item_type="STEP",
                                        parameters={'simulation': self.args['simulation'],
                                                    'test type': self.args['type']})

                service.log(time=self.timestamp(),
                            message="The following requests exceeded the yellow threshold:",
                            level="{}".format('INFO'))
                for request in compare_with_thresholds:
                    if request['threshold'] == 'yellow':
                        service.log(time=self.timestamp(), message="\"{}\" reached {} ms by {}. Threshold {} ms."
                                    .format(request['request_name'], request['response_time'],
                                            self.args['comparison_metric'], request['yellow']),
                                    level="{}".format('WARN'))

                service.log(time=self.timestamp(),
                            message="The following requests exceeded the red threshold:",
                            level="{}".format('INFO'))
                for request in compare_with_thresholds:
                    if request['threshold'] == 'red':
                        service.log(time=self.timestamp(), message="\"{}\" reached {} ms by {}. Threshold {} ms."
                                    .format(request['request_name'], request['response_time'],
                                            self.args['comparison_metric'], request['red']),
                                    level="{}".format('WARN'))

                service.log(time=self.timestamp(), message=hashlib.sha256(
                    "{} missed thresholds".format(self.args['simulation']).strip().encode('utf-8')).hexdigest(),
                            level='ERROR')
                service.finish_test_item(end_time=self.timestamp(), status="FAILED")
            else:
                service.start_launch(name=self.rp_launch_name + ": compare with thresholds",
                                     start_time=self.timestamp(),
                                     description='Missed thresholds rate less than {}'
                                     .format(self.missed_thresholds_rate))

                # Finish launch.
            service.finish_launch(end_time=self.timestamp())

            service.terminate()
