from requests import post, get
from json import dumps
import hashlib
from perfreporter.utils import calculate_appendage


class IssuesConnector(object):
    def __init__(self, report_url, query_url, token):
        self.report_url = report_url
        self.query_url = query_url
        self.token = token
        self.headers = {
            "Content-type": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def create_issue(self, payload):
        issue_hash = payload['id']
        exists = self.search_for_issue(issue_hash)
        if exists:
            print(f"The issue with {payload['title']} title already exists")
            return
        
        if exists is None:
            print(f"Unable to connect to query url")
            return

        result = post(self.report_url, data=dumps(payload), headers=self.headers)
        return result.content
    
    def search_for_issue(self, issue_hash):
        resp = get(self.query_url, params={'source.id': issue_hash, 'status': 'Open'}, headers=self.headers)

        # if not resp.status_code == 200:
        #     return None

        data = resp.json()
        if not data['total'] == 0:
            return True
        return False


class EngagementReporter:
    def __init__(self, args, report_url, query_url, token):
        self.args = args
        self.issues_connector = IssuesConnector(report_url, query_url, token)

    @staticmethod
    def _prepare_issue_payload(issue_hash, title, description, severity):
        return {
            'id': issue_hash,
            'title': title,
            'description': description,
            'severity': severity,
            'project': None,
            'asset': None,
            'type': 'Bug',
            'source': 'backend_performance'
        }

    def report_errors(self, aggregated_errors):
        for error in aggregated_errors:
            issue_hash = self.get_functional_error_hash_code(aggregated_errors[error], self.args)
            title = "Functional error in test: " + str(self.args['simulation']) + ". Request \"" \
                    + str(aggregated_errors[error]['Request name']) + "\" failed with error message: " \
                    + str(aggregated_errors[error]['Error_message'])[0:100]
            
            description = self.create_functional_error_description(aggregated_errors[error], self.args)
            payload = self._prepare_issue_payload(issue_hash, title, description, severity="High")
            self.issues_connector.create_issue(payload)


    def report_performance_degradation(self, performance_degradation_rate, compare_with_baseline):
        print(performance_degradation_rate)
        print(compare_with_baseline)
        issue_hash = hashlib.sha256("{} performance degradation".format(self.args['simulation']).strip()
                                    .encode('utf-8')).hexdigest()
        title = "Performance degradation in test: " + str(self.args['simulation'])
        description = self.create_performance_degradation_description(performance_degradation_rate,
                                                                      compare_with_baseline, issue_hash, self.args)
        payload = self._prepare_issue_payload(issue_hash, title, description, severity="High")                                                
        self.issues_connector.create_issue(payload)


    def report_missed_thresholds(self, missed_threshold_rate, compare_with_thresholds):
        
        issue_hash = hashlib.sha256("{} missed thresholds".format(self.args['simulation']).strip()
                                    .encode('utf-8')).hexdigest()
        title = "Missed thresholds in test: " + str(self.args['simulation'])
        description = self.create_missed_thresholds_description(missed_threshold_rate,
                                                                compare_with_thresholds, issue_hash)
        payload = self._prepare_issue_payload(issue_hash, title, description, severity="High")                                                
        self.issues_connector.create_issue(payload)

    
    @staticmethod
    def create_functional_error_description(error, arguments):
        title = "Functional error in test: " + str(arguments['simulation']) + ". Request \"" \
                + str(error['Request name']) + "\"."
        description = f"{title}\n"
        if error['Request name']:
            description += "Request name: " + error['Request name'] + "\n"
        if error['Method']:
            description += "HTTP Method: " + error['Method'] + "\n"
        if error['Request URL']:
            description += "Request URL: " + error['Request URL'] + "\n"
        if error['Request_params'] and str(error['Request_params']) != " ":
            description += "Request params: " + str(error['Request_params'])[2:-2].replace(" ", "\n") + "\n"
        if error['Request headers']:
            description += "Request headers: "
            headers = str(error['Request headers']).replace(": ", ":")
            for header in headers.split(" "):
                description += header + "\n"
            description += "\n"
        description += "----\nError description\n"
        if error['Error count']:
            description += "Error count: " + str(error['Error count']) + ";\n"
        if error['Response code']:
            description += "Response code: " + error['Response code'] + ";\n"
        if error['Error_message']:
            description += "Error message: " + str(error['Error_message']) + "\n"
        if error['Response']:
            description += "----\nResponse body " + str(error['Response']) 
        return description

    @staticmethod
    def get_functional_error_hash_code(error, arguments):
        error_str = arguments['simulation'] + "_" + error['Request URL'] + "_" + str(error['Error_message']) + "_" \
                    + error['Request name']
        return hashlib.sha256(error_str.strip().encode('utf-8')).hexdigest()


    @staticmethod
    def create_performance_degradation_description(performance_degradation_rate, compare_with_baseline, issue_hash,
                                                   arguments):
        description = f"Test performance degradation is {performance_degradation_rate}% compared to the baseline.<br>"
        description += "<h3>The following requests are slower than baseline:</h3>"
        for request in compare_with_baseline:
            description += "\"{}\" reached {} ms by {}. Baseline {} ms.<br>".format(request['request_name'],
                                                                                  request['response_time'],
                                                                                  arguments['comparison_metric'],
                                                                                  request['baseline'])
        description += "<br><strong>Issue hash: </strong>" + str(issue_hash)
        return description

    @staticmethod
    def create_missed_thresholds_description(missed_threshold_rate, compare_with_thresholds, issue_hash):
        description = f"Percentage of requests exceeding the threshold was {missed_threshold_rate}%. <br>"
        for color in ['yellow', 'red']:
            colored = False
            for th in compare_with_thresholds:
                if th['threshold'] == color:
                    if not colored:
                        description += f"<h2>The following {color} thresholds were exceeded:</h2>"
                        colored = True
                    appendage = calculate_appendage(th['target'])
                    description += f"\"{th['request_name']}\" {th['target']}{appendage} " \
                                   f"with value {th['metric']}{appendage} " \
                                   f"exceeded threshold of {th['value']}{appendage}<br>"
        description += "<br><strong>Issue hash: </strong>" + str(issue_hash)
        return description
