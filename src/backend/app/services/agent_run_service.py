from app.schemas import AgentRunResponse, AgentRunStepResponse


class AgentRunService:
    def start_run(self, run_type: str, profile_id: int, course_id: int) -> AgentRunResponse:
        raise NotImplementedError

    def record_step(
        self,
        run_id: int,
        agent_type: str,
        input_summary: str,
        output_summary: str,
        decision_basis: str,
        status: str,
    ) -> AgentRunStepResponse:
        raise NotImplementedError

    def complete_run(self, run_id: int, final_summary: str) -> AgentRunResponse:
        raise NotImplementedError
