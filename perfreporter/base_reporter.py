from abc import ABC, abstractmethod

class Reporter(ABC):
    def __init__(self, **quality_gate_config):
        self.check_functional_errors = quality_gate_config.get("check_functional_errors", False)
        self.check_performance_degradation = quality_gate_config.get("check_performance_degradation", False)
        self.check_missed_thresholds = quality_gate_config.get("check_missed_thresholds", False)
        self.performance_degradation_rate = quality_gate_config.get("performance_degradation_rate", 20)
        self.missed_thresholds_rate = quality_gate_config.get("missed_thresholds_rate", 50)
        
    @abstractmethod  
    def is_valid_config(config: dict) -> bool:
        raise NotImplementedError

    @abstractmethod
    def report_errors(self, aggregated_errors):
        raise NotImplementedError

    @abstractmethod
    def report_performance_degradation(self, performance_degradation_rate, compare_with_baseline):
        raise NotImplementedError

    @abstractmethod
    def report_missed_thresholds(self, missed_threshold_rate, compare_with_thresholds):
        raise NotImplementedError
