import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.adapters.protocols import LLMResult
from app.db.session import get_engine
from app.models import AgentRun, AgentRunStep
from app.services.demo_data_service import DemoDataService
from app.services.profile_service import ProfileService
from app.services.profile_updater_service import ProfileUpdaterService


class FakeProfileUpdaterProvider:
    def __init__(self, content: str | None = None, fail: bool = False) -> None:
        self.content = content
        self.fail = fail

    def generate(self, messages, response_schema=None) -> LLMResult:
        if self.fail:
            raise RuntimeError("profile updater provider unavailable")
        return LLMResult(
            content=self.content
            or """
            {
              "weak_points": ["链表", "BFS/DFS"],
              "resource_preference": "代码实操案例",
              "learning_preference": "code_driven",
              "foundation_level": "intermediate",
              "reason": "Resource 与 Tutor trace 显示学生正在通过代码实操理解链表和 BFS。"
            }
            """,
            metadata={"provider": "fake"},
        )


class ProfileUpdaterLLMTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "profile-updater-llm-test.sqlite3"
        self.database_url = f"sqlite:///{self.database_path.as_posix()}"
        os.environ["APP_DATABASE_URL"] = self.database_url

    def tearDown(self) -> None:
        get_engine().dispose()
        get_engine(self.database_url).dispose()
        get_engine.cache_clear()
        os.environ.pop("APP_DATABASE_URL", None)
        self.temp_dir.cleanup()

    def test_llm_profile_updater_uses_fixed_json_analysis(self) -> None:
        profile_id = self._seed_trace()
        with patch(
            "app.services.profile_updater_service.build_llm_provider",
            return_value=FakeProfileUpdaterProvider(),
        ):
            updated = ProfileUpdaterService(database_url=self.database_url).update_from_trace(profile_id)

        preferences = updated.preferences
        self.assertEqual(preferences["weak_points"], "链表、BFS/DFS")
        self.assertEqual(preferences["resource_preference"], "代码实操案例")
        self.assertEqual(preferences["learning_preference"], "code_driven")
        self.assertEqual(preferences["foundation_level"], "intermediate")
        self.assertIn("LLM ProfileUpdater", preferences["last_profile_update_reason"])
        self.assertIn("Resource 与 Tutor trace", preferences["last_profile_update_reason"])

    def test_profile_updater_falls_back_to_rule_based_when_llm_fails(self) -> None:
        profile_id = self._seed_trace()
        with patch(
            "app.services.profile_updater_service.build_llm_provider",
            return_value=FakeProfileUpdaterProvider(fail=True),
        ):
            updated = ProfileUpdaterService(database_url=self.database_url).update_from_trace(profile_id)

        preferences = updated.preferences
        self.assertIn("链表", preferences["weak_points"])
        self.assertIn("代码实操案例", preferences["resource_preference"])
        self.assertIn("LLM 分析不可用，已回退到 rule-based", preferences["last_profile_update_reason"])
        self.assertIn("provider unavailable", preferences["last_profile_update_reason"])

    def _seed_trace(self) -> int:
        demo = DemoDataService(database_url=self.database_url).load_demo_data().demo_data
        profile_id = ProfileService(database_url=self.database_url).list_demo_profiles()[0].id
        from app.db.session import session_scope

        with session_scope(self.database_url) as session:
            run = AgentRun(
                student_profile_id=profile_id,
                course_id=demo.course_id,
                run_type="profile_update_test",
                status="completed",
                input_summary="Profile updater LLM test input.",
                output_summary="Profile updater LLM test output.",
                final_summary="Profile updater LLM test run.",
            )
            session.add(run)
            session.flush()
            session.add(
                AgentRunStep(
                    agent_run_id=run.id,
                    agent_type="resource",
                    step_order=1,
                    status="completed",
                    input_summary="学生请求用代码实操理解链表。",
                    output_summary="生成 coding_case，包含链表插入和 BFS 对比练习。",
                    decision_basis="根据学生偏好选择代码实操案例。",
                )
            )
        return profile_id


if __name__ == "__main__":
    unittest.main()
