from requests import post, get
from json import dumps
import hashlib

from perfreporter.utils import calculate_appendage
from perfreporter.base_reporter import Reporter


class IssuesConnector():
    def __init__(self, report_url, query_url, token):
        self.report_url = report_url
        self.query_url = query_url
        self.token = token
        self.headers = {
            "Content-type": "application/json",
            "Authorization": f"Bearer {token}",
        }

    def create_issue(self, payload):
        issue_hash = payload['issue_id']
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

        if not resp.status_code == 200:
            return None

        data = resp.json()
        if not data['total'] == 0:
            return True
        return False


class EngagementReporter(Reporter):
    def __init__(self, args, config, quality_gate_config):
        super().__init__(**quality_gate_config)
        self.args = args
        self.config = config["reporter_engagement"]
        self.engagement_id = self.config["id"]
        self.token = args['token']
        self.report_url = args['base_url'] + self.config['report_url'] + '/' + args['project_id']
        self.query_url = args['base_url'] + self.config['query_url'] + '/' + args['project_id']
        self.issues_connector = IssuesConnector(self.report_url, self.query_url, self.token)

    @staticmethod
    def is_valid_config(config: dict) -> bool:
        if not "reporter_engagement" in config:
            return False
        for each in ('report_url', 'id', 'query_url'):
            if not config["reporter_engagement"].get(each):
                return False
        return True    

    def _prepare_issue_payload(self, issue_hash, title, description):
        return {
            'issue_id': issue_hash,
            'title': title,
            'description': description,
            'severity': "High",
            'project': None,
            'asset': None,
            'type': 'Issue',
            'source': 'backend_performance',
            'engagement': self.engagement_id,
            'report_id': self.args['report_id'],
        }

    def report_errors(self, aggregated_errors):
        for error in aggregated_errors:
            issue_hash = self.get_functional_error_hash_code(aggregated_errors[error], self.args)
            title = "Functional error in test: " + str(self.args['simulation']) + ". Request \"" \
                    + str(aggregated_errors[error]['Request name']) + "\" failed with error message: " \
                    + str(aggregated_errors[error]['Error_message'])[0:100]
            
            description = self.create_functional_error_description(aggregated_errors[error], self.args)
            payload = self._prepare_issue_payload(issue_hash, title, description)
            self.issues_connector.create_issue(payload)


    def report_performance_degradation(self, compare_baseline, report_data):
        issue_hash = hashlib.sha256("{} performance degradation".format(self.args['simulation']).strip()
                                    .encode('utf-8')).hexdigest()
        title = "Performance degradation in test: " + str(self.args['simulation'])
        description = self.create_performance_degradation_description(compare_baseline, report_data, 
                                                                      issue_hash, self.args)
        payload = self._prepare_issue_payload(issue_hash, title, description)                                                
        self.issues_connector.create_issue(payload)


    def report_missed_thresholds(self, compare_with_thresholds, report_data):
        issue_hash = hashlib.sha256("{} missed thresholds".format(self.args['simulation']).strip()
                                    .encode('utf-8')).hexdigest()
        title = "Missed thresholds in test: " + str(self.args['simulation'])
        description = self.create_missed_thresholds_description(compare_with_thresholds, report_data, issue_hash)
        payload = self._prepare_issue_payload(issue_hash, title, description)                                                
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
    def create_performance_degradation_description(compare_baseline, report_data, issue_hash, arguments):
        description = ""
        for report in report_data:
            description += '<strong>' + report["message"] + "</strong><br>"
        description += "<h3>The following requests are slower than baseline:</h3>"
        for request in compare_baseline:
            appendage = calculate_appendage(request['target'])
            description += "\"{}\" {} reached {} {} by {}. Baseline {} {}.<br>".format(request['request_name'],
                                                                                       request['target'],
                                                                                       request['metric'],
                                                                                       appendage,
                                                                                       arguments['comparison_metric'],
                                                                                       request['baseline'],
                                                                                       appendage
                                                                                      )
        description += "<br><strong>Issue hash: </strong>" + str(issue_hash)
        return description

    @staticmethod
    def create_missed_thresholds_description(compare_with_thresholds, report_data, issue_hash):
        description = ""
        for report in report_data: 
            description += '<strong>' + report["message"] + "</strong><br>"
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
