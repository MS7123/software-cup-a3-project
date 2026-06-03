from dataclasses import dataclass


@dataclass(frozen=True)
class LearningFlowResult:
    agent_run_id: int
    final_summary: str


class AgentOrchestrator:
    def run_learning_flow(self, profile_id: int, course_id: int, goal: str) -> LearningFlowResult:
        raise NotImplementedError
