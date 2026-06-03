from dataclasses import dataclass


@dataclass(frozen=True)
class LearningFlowResult:
    agent_run_id: int
    learning_path_id: int
    final_summary: str


class AgentOrchestrator:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url

    def run_learning_flow(self, profile_id: int, course_id: int, goal: str) -> LearningFlowResult:
        from app.services.agent_run_service import AgentRunService
        from app.services.learning_path_service import LearningPathService

        run_service = AgentRunService(database_url=self.database_url)
        path_service = LearningPathService(database_url=self.database_url)

        path = path_service.create_path(profile_id, course_id, goal)
        run = run_service.start_run(
            "learning_path_planning",
            profile_id,
            course_id,
            input_summary=f"profile_id={profile_id}; course_id={course_id}; goal={goal}",
        )
        run_service.record_step(
            run.id,
            "planner",
            input_summary=f"基于学生画像 {profile_id}、课程 {course_id} 和目标生成学习路径。",
            output_summary=f"生成 {len(path.items)} 个阶段化学习步骤，覆盖数据结构 MVP 知识点。",
            decision_basis=path.rationale or "依据学生画像、课程知识点顺序和先修关系规划路径。",
            status="completed",
        )
        final_summary = f"Planner Agent 已生成学习路径 {path.id}，包含 {len(path.items)} 个步骤。"
        run_service.complete_run(run.id, final_summary)
        return LearningFlowResult(
            agent_run_id=run.id,
            learning_path_id=path.id,
            final_summary=final_summary,
        )
