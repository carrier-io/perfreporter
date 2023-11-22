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
                    "performance_degradation_rate": args['performance_degradation_rate'],
                    "missed_threshold_rate": args['missed_threshold_rate'],
                    "reasons_to_fail_report": args['reasons_to_fail_report'],
                    "status": args['status'],
                    "quality_gate_config": quality_gate_config
                }

                if quality_gate_config.get("baseline", {}).get("checked"):
                    event["performance_degradation_rate_qg"] = quality_gate_config.get("settings").get("per_request_results")['percentage_of_failed_requests']
                if quality_gate_config.get("SLA", {}).get("checked"):
                    event["missed_thresholds_qg"] = quality_gate_config.get("settings").get("per_request_results")['percentage_of_failed_requests']




                res = requests.post(task_url, json=event, headers={'Authorization': f'bearer {args["token"]}',
                                                                'Content-type': 'application/json'})
                return res.text
