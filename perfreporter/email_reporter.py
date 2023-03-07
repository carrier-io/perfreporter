import requests


class EmailReporter():

    @staticmethod    
    def process_report(args, test_data, integration, quality_gate_config):
        email_notification_id = integration["reporters"]["reporter_email"].get("task_id")
        if email_notification_id:
            emails = integration["reporters"]["reporter_email"].get("recipients", [])
            if emails:
                task_url = f"{args['base_url']}/api/v1/tasks/run_task/{args['project_id']}/{email_notification_id}"
                event = {
                    "galloper_url": args['base_url'],
                    "token": args['token'],
                    "project_id": args['project_id'],
                    "test_data": test_data,
                    "influx_host": args["influx_host"],
                    "influx_port": args["influx_port"],
                    "influx_user": args["influx_user"],
                    "influx_password": args["influx_password"],
                    "influx_db": args['influx_db'],
                    "comparison_db": args['comparison_db'],
                    "test": args['simulation'],
                    "user_list": emails,
                    "notification_type": "api",
                    "test_type": args["type"],
                    "env": args["env"],
                    "users": args["users"],
                    "smtp_host": integration["reporters"]["reporter_email"]["integration_settings"]["host"],
                    "smtp_port": integration["reporters"]["reporter_email"]["integration_settings"]["port"],
                    "smtp_user": integration["reporters"]["reporter_email"]["integration_settings"]["user"],
                    "smtp_sender": integration["reporters"]["reporter_email"]["integration_settings"]["sender"],
                    "smtp_password": integration["reporters"]["reporter_email"]["integration_settings"]["passwd"],
                }
                if quality_gate_config.get('check_functional_errors'):
                    event["error_rate"] = quality_gate_config['error_rate']
                if quality_gate_config.get('check_performance_degradation'):
                    event["performance_degradation_rate"] = quality_gate_config['performance_degradation_rate']
                if quality_gate_config.get('check_missed_thresholds'):
                    event["missed_thresholds"] = quality_gate_config['missed_thresholds_rate']

                res = requests.post(task_url, json=event, headers={'Authorization': f'bearer {args["token"]}',
                                                                'Content-type': 'application/json'})
                return res.text
