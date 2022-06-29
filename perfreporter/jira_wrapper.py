from jira import JIRA
import hashlib
import io

from perfreporter.utils import calculate_appendage

class JiraWrapper:
    JIRA_REQUEST = 'project={} AND labels in ({})'

    def __init__(self, args, url, user, password, jira_project, assignee, check_functional_errors,
                 check_performance_degradation, check_missed_thresholds, performance_degradation_rate,
                 missed_thresholds_rate, issue_type='Bug', labels=None, watchers=None, jira_epic_key=None):
        self.valid = True
        self.args = args
        self.url = url
        self.password = password
        self.user = user
        self.check_functional_errors = check_functional_errors
        self.check_performance_degradation = check_performance_degradation
        self.check_missed_thresholds = check_missed_thresholds
        self.performance_degradation_rate = performance_degradation_rate
        self.missed_thresholds_rate = missed_thresholds_rate
        try:
            self.connect()
        except Exception:
            self.valid = False
            return
        self.projects = [project.key for project in self.client.projects()]
        self.project = jira_project
        if self.project not in self.projects:
            self.client.close()
            self.valid = False
            return
        self.assignee = assignee
        self.issue_type = issue_type
        self.labels = list()
        if labels:
            self.labels = [label.strip() for label in labels.split(",")]
        self.watchers = list()
        if watchers:
            self.watchers = [watcher.strip() for watcher in watchers.split(",")]
        self.jira_epic_key = jira_epic_key
        self.client.close()

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
        globals().get("logger").info("Issue " + issue.key + " created." + " Description - " + issue_data['summary'])
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
                globals().get("logger").info('  more then 1 issue with the same summary')
            else:
                globals().get("logger").info(issuetype + 'issue already exists:' + issue.key)
        else:
            issue = self.post_issue(issue_data)
            created = True
        return issue, created

    @staticmethod
    def create_functional_error_description(error, arguments):
        title = "Functional error in test: " + str(arguments['simulation']) + ". Request \"" \
                + str(error['Request name']) + "\"."
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
        error_str = arguments['simulation'] + "_" + error['Request URL'] + "_" + str(error['Error_message']) + "_" \
                    + error['Request name']
        return hashlib.sha256(error_str.strip().encode('utf-8')).hexdigest()

    @staticmethod
    def create_performance_degradation_description(performance_degradation_rate, compare_with_baseline, arguments):
        title = "Performance degradation in test: " + str(arguments['simulation'])
        description = "{panel:title=" + title + \
                      "|borderStyle=solid|borderColor=#ccc|titleBGColor=#23b7c9|bgColor=#d7f0f3} \n"
        description += "{color:red}" + "Test performance degradation is {}% compared to the baseline."\
            .format(performance_degradation_rate) + "{color} \n"
        description += "h3. The following requests are slower than baseline:\n"
        for request in compare_with_baseline:
            description += "\"{}\" reached {} ms by {}. Baseline {} ms.\n".format(request['request_name'],
                                                                                  request['response_time'],
                                                                                  arguments['comparison_metric'],
                                                                                  request['baseline'])
        description += "{panel}"
        return description

    @staticmethod
    def create_missed_thresholds_description(missed_threshold_rate, compare_with_thresholds, arguments):
        title = "Missed thresholds in test: " + str(arguments['simulation'])
        description = "{panel:title=" + title + \
                      "|borderStyle=solid|borderColor=#ccc|titleBGColor=#23b7c9|bgColor=#d7f0f3} \n"
        description += "{color:red}" + "Percentage of requests exceeding the threshold was {}%." \
            .format(missed_threshold_rate) + "{color} \n"
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
                                   f"exceeded threshold of {th[color]}{appendage}\n"
        description += "{panel}"
        return description

    def report_errors(self, aggregated_errors):
        for error in aggregated_errors:
            issue_hash = self.get_functional_error_hash_code(aggregated_errors[error], self.args)
            title = "Functional error in test: " + str(self.args['simulation']) + ". Request \"" \
                    + str(aggregated_errors[error]['Request name']) + "\" failed with error message: " \
                    + str(aggregated_errors[error]['Error_message'])[0:100]
            description = self.create_functional_error_description(aggregated_errors[error], self.args)
            if len(str(aggregated_errors[error]['Response'])) < 55000:
                self.create_issue(title, 'Major', description, issue_hash)
            else:
                content = io.StringIO()
                content.write(str(aggregated_errors[error]['Response']))
                attachment = {"binary_content": content, "message": "response_body.txt"}
                self.create_issue(title, 'Major', description, issue_hash, [attachment])

    def report_performance_degradation(self, performance_degradation_rate, compare_with_baseline):
        issue_hash = hashlib.sha256("{} performance degradation".format(self.args['simulation']).strip()
                                    .encode('utf-8')).hexdigest()
        title = "Performance degradation in test: " + str(self.args['simulation'])
        description = self.create_performance_degradation_description(performance_degradation_rate,
                                                                      compare_with_baseline, self.args)
        self.create_issue(title, 'Major', description, issue_hash)

    def report_missed_thresholds(self, missed_threshold_rate, compare_with_thresholds):
        issue_hash = hashlib.sha256("{} missed thresholds".format(self.args['simulation']).strip()
                                    .encode('utf-8')).hexdigest()
        title = "Missed thresholds in test: " + str(self.args['simulation'])
        description = self.create_missed_thresholds_description(missed_threshold_rate,
                                                                compare_with_thresholds, self.args)
        self.create_issue(title, 'Major', description, issue_hash)

