from junit_xml import TestSuite, TestCase


class JUnit_reporter(object):

    @staticmethod
    def process_report(requests, thresholds):
        functional_test_cases, threshold_test_cases = [], []
        test_suites = []
        for req in requests:
            if requests[req]['KO'] != 0:
                functional_test_cases.append(TestCase(name=requests[req]['request_name'],
                                                      stdout="PASSED: {}. FAILED: {}".format(str(requests[req]['OK']),
                                                                                             str(requests[req]['KO'])),
                                                      stderr="FAILED: {}".format(str(requests[req]['KO']))))
                functional_test_cases[-1].add_failure_info("Request failed {} times".format(str(requests[req]['KO'])))
            else:
                functional_test_cases.append(
                    TestCase(name=requests[req]['request_name'], stdout="PASSED: {}".format(str(requests[req]['OK'])),
                             stderr="FAILED: {}".format(str(requests[req]['KO']))))

        test_suites.append(TestSuite("Functional errors ", functional_test_cases))

        for th in thresholds:
            threshold_test_cases.append(TestCase(name="Threshold for {}, target - {}".format(th['scope'], th['target']),
                                                 stdout="Value: {} {}. Threshold value: {} {}".format(str(th['value']),
                                                                                                th['metric'],
                                                                                                str(th['threshold']),
                                                                                                th['metric'])))
            if th['status'] == 'FAILED':
                threshold_test_cases[-1].add_failure_info("{} for {} exceeded threshold of {} {}. Test result - {} {}"
                                                          .format(th['target'], th['scope'], str(th['threshold']),
                                                                  th['metric'], str(th['value']), th['metric']))

        test_suites.append(TestSuite("Thresholds ", threshold_test_cases))
        with open("/tmp/reports/jmeter.xml", 'w') as f:
            TestSuite.to_file(f, test_suites, prettyprint=True)
