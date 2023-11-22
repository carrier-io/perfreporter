from jira import JIRA
import hashlib
import io

from perfreporter.base_reporter import Reporter
from perfreporter.utils import calculate_appendage

class JiraReporter(Reporter):
    JIRA_REQUEST = 'project={} AND labels in ({})'

    def __init__(self, args, config, quality_gate_config):
        super().__init__(**quality_gate_config)
        self.args = args
        self.config = config["reporter_jira"]
        self.url = self.config["integration_settings"]["url"]
        self.user = self.config["integration_settings"]["login"]
        self.password = self.config["integration_settings"]["passwd"]
        self.connect()
        self.projects = [project.key for project in self.client.projects()]
        self.project = self.config["integration_settings"]["project"]
        if self.project not in self.projects:
            self.client.close()
            return
        self.assignee = self.config.get("assignee", self.user)
        self.issue_type = self.config["integration_settings"].get("issue_type", "Bug")
        self.labels = self.config.get("jira_labels", list())
        if self.labels:
            self.labels = [label.strip() for label in self.config["jira_labels"].split(",")]
        self.watchers = self.config.get("jira_watchers", list())
        if self.watchers:
            self.watchers = [watcher.strip() for watcher in self.config["jira_watchers"].split(",")]
        self.jira_epic_key = self.config.get("jira_epic_key", None)
        print("JIRA self.args")
        print(self.args)

    @staticmethod
    def is_valid_config(config: dict) -> bool:
        print("JIRA config ************************")
        print(config)
        if not "reporter_jira" in config:
            return False
        for each in ("url", "login", "passwd", "project"):
            if not config["reporter_jira"]["integration_settings"].get(each):
                return False
        return True

    def connect(self):
        self.client = JIRA(self.url, basic_auth=(self.user, self.password))

    def create_issue(self, title, priority, description, issue_hash, attachments=None, get_or_create=True,
                     additional_labels=None):
        _labels = [issue_hash]
        if additional_labels and isinstance(additional_labels, list):
            _labels.extend(additional_labels)
        _labels.extend(self.labels)
        issue_data = {
            'project': {'key': self.project},
            'summary': title,
            'description': description,
            'issuetype': {'name': self.issue_type},
            'assignee': {'name': self.assignee},
            'priority': {'name': priority},
            'labels': _labels
        }
        jira_request = self.JIRA_REQUEST.format(issue_data["project"]["key"], issue_hash)
        if get_or_create:
            issue, created = self.get_or_create_issue(jira_request, issue_data)
        else:
            issue = self.post_issue(issue_data)
            created = True
        if attachments:
            for attachment in attachments:
                if 'binary_content' in attachment:
                    self.add_attachment(issue.key,
                                        attachment=attachment['binary_content'],
                                        filename=attachment['message'])
        for watcher in self.watchers:
            self.client.add_watcher(issue.id, watcher)
        if self.jira_epic_key:
            self.client.add_issues_to_epic(self.jira_epic_key, [issue.id])
        return issue, created

    def add_attachment(self, issue_key, attachment, filename=None):
        issue = self.client.issue(issue_key)
        for _ in issue.fields.attachment:
            if _.filename == filename:
                return
        self.client.add_attachment(issue, attachment, filename)

    def post_issue(self, issue_data):
        issue = self.client.create_issue(fields=issue_data)
        print("Issue " + issue.key + " created." + " Description - " + issue_data['summary'])
        return issue

    def get_or_create_issue(self, search_string, issue_data):
        issuetype = issue_data['issuetype']['name']
        created = False
        jira_results = self.client.search_issues(search_string)
        issues = []
        for each in jira_results:
            if each.fields.summary == issue_data.get('summary', None):
                issues.append(each)
        if len(issues) == 1:
            issue = issues[0]
            if len(issues) > 1:
                print('  more then 1 issue with the same summary')
            else:
                print(issuetype + 'issue already exists:' + issue.key)
        else:
            issue = self.post_issue(issue_data)
            created = True
        return issue, created

    @staticmethod
    def create_functional_error_description(error, arguments):
        title = "Functional error in test: " + str(arguments['name']) + ". Request \"" \
                + str(error['Request name']) + "\"." + f"Enviroment: {arguments['environment']}, type: {arguments['type']}."
        description = "{panel:title=" + title + \
                      "|borderStyle=solid|borderColor=#ccc|titleBGColor=#23b7c9|bgColor=#d7f0f3} \n"
        description += "h3. Request description\n"
        if error['Request name']:
            description += "*Request name*: " + error['Request name'] + "\n"
        if error['Method']:
            description += "*HTTP Method*: " + error['Method'] + "\n"
        if error['Request URL']:
            description += "*Request URL*: " + error['Request URL'] + "\n"
        if error['Request_params'] and str(error['Request_params']) != " ":
            description += "*Request params*: " + str(error['Request_params'])[2:-2].replace(" ", "\n") + "\n"
        if error['Request headers']:
            description += "*Request headers*: {code}"
            headers = str(error['Request headers']).replace(": ", ":")
            for header in headers.split(" "):
                description += header + "\n"
            description += "{code}\n"
        description += "---- \n h3. Error description\n"
        if error['Error count']:
            description += "*Error count*: " + str(error['Error count']) + ";\n"
        if error['Response code']:
            description += "*Response code*: " + error['Response code'] + ";\n"
        if error['Error_message']:
            description += "*Error message*: {color:red}" + str(error['Error_message']) + "{color}\n"
        if error['Response']:
            if len(str(error['Response'])) < 55000:
                description += "---- \n h3. Response body {code:html}" + str(error['Response']) + "{code}"
            else:
                description += "---- \n See response body attached.\n"
        description += "{panel}"
        return description

    @staticmethod
    def get_functional_error_hash_code(error, arguments):
        error_str = arguments['name'] + "_" + error['Request URL'] + "_" + str(error['Error_message']) + "_" \
                    + error['Request name']
        return hashlib.sha256(error_str.strip().encode('utf-8')).hexdigest()

    @staticmethod
    def create_performance_degradation_description(compare_baseline, report_data, arguments):
        title = f"Performance degradation in test: {arguments['name']}. \
                Enviroment: {arguments['environment']}, type: {arguments['type']}."
        description = "{panel:title=" + title + \
                      "|borderStyle=solid|borderColor=#ccc|titleBGColor=#23b7c9|bgColor=#d7f0f3} \n"
        # description += "{color:red}" + "Test performance degradation is {}% compared to the baseline."\
        #     .format(performance_degradation_rate) + "{color} \n"
        for report in report_data:
            description += "{color:red}" + report["message"] + "{color} \n"
        description += "h3. The following requests are slower than baseline:\n"
        for request in compare_baseline:
            appendage = calculate_appendage(request['target'])
            description += "\"{}\" {} reached {} {} by {}. Baseline {} {}.\n".format(request['request_name'],
                                                                                     request['target'],
                                                                                     request['metric'],
                                                                                     appendage,
                                                                                     arguments['comparison_metric'],
                                                                                     request['baseline'],
                                                                                     appendage
                                                                                    )
        description += "{panel}"
        return description

    @staticmethod
    def create_missed_thresholds_description(compare_with_thresholds, report_data, arguments):
        title = f"Missed thresholds in test: {arguments['name']}. \
                Enviroment: {arguments['environment']}, type: {arguments['type']}."
        description = "{panel:title=" + title + \
                      "|borderStyle=solid|borderColor=#ccc|titleBGColor=#23b7c9|bgColor=#d7f0f3} \n"
        # description += "{color:red}" + "Percentage of requests exceeding the threshold was {}%." \
        #     .format(missed_threshold_rate) + "{color} \n"
        for report in report_data:
            description += "{color:red}" + report["message"] + "{color} \n"
        for color in ['yellow', 'red']:
            colored = False
            for th in compare_with_thresholds:
                if th['threshold'] == color:
                    if not colored:
                        description += f"h3. The following {color} thresholds were exceeded:\n"
                        colored = True
                    appendage = calculate_appendage(th['target'])
                    description += f"\"{th['request_name']}\" {th['target']}{appendage} " \
                                   f"with value {th['metric']}{appendage} " \
                                   f"exceeded threshold of {th['value']}{appendage}\n"
        description += "{panel}"
        return description

    def report_errors(self, aggregated_errors):
        for error in aggregated_errors:
            issue_hash = self.get_functional_error_hash_code(aggregated_errors[error], self.args)
            title = "Functional error in test: " + str(self.args['name']) + ". Request \"" \
                    + str(aggregated_errors[error]['Request name']) + "\" failed with error message: " \
                    + str(aggregated_errors[error]['Error_message'])[0:100]
            description = self.create_functional_error_description(aggregated_errors[error], self.args)
            if len(str(aggregated_errors[error]['Response'])) < 55000:
                self.create_issue(title, 'Major', description, issue_hash,
                                  additional_labels=[self.args['environment'], self.args['type']])
            else:
                content = io.StringIO()
                content.write(str(aggregated_errors[error]['Response']))
                attachment = {"binary_content": content, "message": "response_body.txt"}
                self.create_issue(title, 'Major', description, issue_hash, attachments=[attachment],
                                  additional_labels=[self.args['environment'], self.args['type']])

    def report_performance_degradation(self, compare_baseline, report_data):
        issue_hash = hashlib.sha256("{} performance degradation".format(self.args['name']).strip()
                                    .encode('utf-8')).hexdigest()
        title = "Performance degradation in test: " + str(self.args['name'])
        description = self.create_performance_degradation_description(compare_baseline,
                                                                      report_data, self.args)
        self.create_issue(title, 'Major', description, issue_hash,
                          additional_labels=[self.args['environment'], self.args['type']])

    def report_missed_thresholds(self, compare_with_thresholds, report_data):
        issue_hash = hashlib.sha256("{} missed thresholds".format(self.args['name']).strip()
                                    .encode('utf-8')).hexdigest()
        title = "Missed thresholds in test: " + str(self.args['name'])
        description = self.create_missed_thresholds_description(compare_with_thresholds, report_data, self.args)
        self.create_issue(title, 'Major', description, issue_hash,
                          additional_labels=[self.args['environment'], self.args['type']])
