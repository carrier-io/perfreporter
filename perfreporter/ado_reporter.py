from requests import post
import hashlib

from perfreporter.utils import calculate_appendage
from perfreporter.base_reporter import Reporter


CREATE_ISSUE_URL = 'https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/' \
                   '${type}?bypassRules={rules}&suppressNotifications={notify}&api-version=5.1'
QUERY_ISSUE_URL = "https://dev.azure.com/{organization}/{project}/_apis/wit/wiql?api-version=5.1"


class ADOConnector():
    def __init__(self, organization, project, personal_access_token, issue_type, team=None):
        self.auth = ('', personal_access_token)
        self.project = f"{project}"
        self.team = f"{project}"
        if team:
            self.team = f"{project}\\{team}"
        issue_type = "task" if issue_type is None else issue_type
        self.url = CREATE_ISSUE_URL.format(organization=organization, project=project, type=issue_type, rules="false",
                                           notify="false")
        self.query_url = QUERY_ISSUE_URL.format(organization=organization, project=project)

    def create_finding(self, title, description=None, assignee=None, issue_hash=None, custom_fields=None, tags=None):
        if not custom_fields:
            custom_fields = dict()
        if tags:
            if '/fields/System.Tags' not in custom_fields:
                custom_fields['/fields/System.Tags'] = ""
            elif not custom_fields['/fields/System.Tags'].endswith(";"):
                custom_fields['/fields/System.Tags'] += ';'
            custom_fields['/fields/System.Tags'] += ";".join(tags)
        body = []
        fields_mapping = {
            "/fields/System.Title": title,
            "/fields/Microsoft.VSTS.Common.Priority": 2,
            "/fields/System.Description": description,
            "/fields/System.AssignedTo": assignee,
            "/fields/System.AreaPath": self.team,
            "/fields/System.IterationPath": self.project
        }
        for key, value in {**fields_mapping, **custom_fields}.items():
            if value:
                _piece = {"op": "add", "path": key, "from": None, "value": value}
                body.append(_piece)
        if not self.search_for_issue(issue_hash):
            return post(self.url, auth=self.auth, json=body,
                        headers={'content-type': 'application/json-patch+json'})

        return {}

    def search_for_issue(self, issue_hash=None):
        q = f"SELECT [System.Id] From WorkItems Where [System.Description] Contains \"{issue_hash}\""
        data = post(self.query_url, auth=self.auth, json={"query": q},
                    headers={'content-type': 'application/json'}).json()
        if len(data["workItems"]):
            return True
        return False


class ADOReporter(Reporter):

    def __init__(self, args, config, quality_gate_config):
        super().__init__(**quality_gate_config)
        self.config = config['azure_devops']
        self.args = args
        organization = self.config.get("org")
        project = self.config.get("project")
        personal_access_token = self.config.get("pat")
        team = self.config.get("team", None)
        issue_type = self.config.get("issue_type")
        self.other_fields = self.config.get("custom_fields", {})
        self.assignee = self.config.get("assignee", None)
        self.ado = ADOConnector(organization, project, personal_access_token, team, issue_type)
        
    @staticmethod
    def is_valid_config(config):
        if not 'azure_devops' in config:
            return False
        for each in ("org", "project", "pat"):
            if not config['azure_devops'].get(each):
                return False
        return True      

    def report_errors(self, errors):
        for each in errors:
            error = errors[each]
            title = "Functional error in test: " + str(self.args['simulation']) + ". Request \"" \
                    + str(error['Request name']) + "\"."
            issue_hash = self.get_functional_error_hash_code(error, self.args)
            details = self.create_functional_error_description(error, issue_hash)
            tags = ["Performance", "Error", self.args["influx_db"]]
            post_result = self.ado.create_finding(title, details, assignee=self.assignee, issue_hash=issue_hash, tags=tags)
            if post_result:
                print(post_result.status_code, post_result.reason)
        print("ADO: functional errors reporting")

    def report_missed_thresholds(self, missed_threshold_rate, compare_with_thresholds):
        title = "Missed thresholds in test: " + str(self.args['simulation'])
        issue_hash = hashlib.sha256("{} missed thresholds".format(self.args['simulation']).strip()
                                    .encode('utf-8')).hexdigest()
        details = self.create_missed_thresholds_description(missed_threshold_rate, compare_with_thresholds, issue_hash)
        tags = ["Performance", "Thresholds", self.args["influx_db"]]
        self.ado.create_finding(title, details, assignee=self.assignee, issue_hash=issue_hash, tags=tags)
        print("ADO: missed thresholds reporting")

    def report_performance_degradation(self, performance_degradation_rate, compare_with_baseline):
        title = "Performance degradation in test: " + str(self.args['simulation'])
        issue_hash = hashlib.sha256("{} performance degradation".format(self.args['simulation']).strip()
                                    .encode('utf-8')).hexdigest()
        details = self.create_performance_degradation_description(performance_degradation_rate, compare_with_baseline,
                                                                  issue_hash, self.args)
        tags = ["Performance", "Baseline", self.args["influx_db"]]
        self.ado.create_finding(title, details, assignee=self.assignee, issue_hash=issue_hash, tags=tags)
        print("ADO: performance degradation reporting")

    @staticmethod
    def create_functional_error_description(error, issue_hash):
        description = "<h3>Request description</h3>"
        if error['Request name']:
            description += "<strong>Request name</strong>: " + error['Request name'] + "<br>"
        if error['Method']:
            description += "<strong>HTTP Method</strong>: " + error['Method'] + "<br>"
        if error['Request URL']:
            description += "<strong>Request URL</strong>: " + error['Request URL'] + "<br>"
        if error['Request_params'] and str(error['Request_params']) != " ":
            description += "<strong>Request params</strong>: " + str(error['Request_params'])[2:-2].replace(" ", "<br>") + "<br>"
        if error['Request headers']:
            description += "<strong>Request headers</strong>: <br>"
            headers = str(error['Request headers']).replace(", ", ",").replace(": ", ":")
            for header in headers.split(" "):
                description += header + "<br>"
        description += "<h3>Error description</h3>"
        if error['Error count']:
            description += "<strong>Error count</strong>: " + str(error['Error count']) + ";<br>"
        if error['Response code']:
            description += "<strong>Response code</strong>: " + error['Response code'] + ";<br>"
        if error['Error_message']:
            description += "<strong>Error message</strong>: " + str(error['Error_message']) + "<br>"
        if error['Response']:
            description += "<h3>Response body</h3><code>" +\
                           str(error['Response']).replace("<", "&lt;").replace(">", "&gt;") + "</code>"
        description += "<br><strong>Issue hash: </strong>" + str(issue_hash)
        return description

    @staticmethod
    def get_functional_error_hash_code(error, arguments):
        error_str = arguments['simulation'] + "_" + error['Request URL'] + "_" + str(error['Error_message']) + "_" \
                    + error['Request name']
        return hashlib.sha256(error_str.strip().encode('utf-8')).hexdigest()

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
