from dataclasses import dataclass

@dataclass
class MetricStore:
    requests_total: int = 0
    errors_total: int = 0
    latency_ms_sum: float = 0.0
    latency_ms_p95: float = 0.0
    breaker_open_total: int = 0

    def prometheus(self) -> str:
        return "\n".join([
            f"agentic_firewall_requests_total {self.requests_total}",
            f"agentic_firewall_errors_total {self.errors_total}",
            f"agentic_firewall_latency_ms_sum {self.latency_ms_sum}",
            f"agentic_firewall_latency_ms_p95 {self.latency_ms_p95}",
            f"agentic_firewall_breaker_open_total {self.breaker_open_total}",
        ]) + "\n"
