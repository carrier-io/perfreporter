def calculate_appendage(metric):
    if metric == "throughput":
        return " RPS"
    elif metric == "response_time":
        return " ms"
    else:
        return ""