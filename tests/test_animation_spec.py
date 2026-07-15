import unittest

from app.services.animation_spec_service import AnimationSpecService


class AnimationSpecServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = AnimationSpecService()

    def test_builds_binary_tree_traversal_spec_for_teaching_video(self) -> None:
        spec = self.service.build(
            concept_name="二叉树遍历",
            concept_slug="binary-tree-traversal",
            objective="掌握前序遍历的访问顺序",
            resource_type="teaching_video",
        )

        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertEqual(spec.version, "1.0")
        self.assertEqual(spec.template_id, "binary_tree_traversal")
        self.assertEqual(spec.data.traversal_type, "PRE_ORDER")
        self.assertEqual([node.id for node in spec.data.nodes], ["A", "B", "C", "D", "E"])
        self.assertEqual(
            [step.target for step in spec.timeline if step.action == "visit"],
            ["A", "B", "D", "E", "C"],
        )

    def test_timeline_targets_are_declared_nodes(self) -> None:
        spec = self.service.build(
            concept_name="二叉树遍历",
            concept_slug="binary-tree-traversal",
            objective="理解前序遍历",
            resource_type="teaching_video",
        )

        assert spec is not None
        node_ids = {node.id for node in spec.data.nodes}
        self.assertTrue(all(step.target in node_ids for step in spec.timeline))

    def test_non_video_resource_does_not_receive_animation_spec(self) -> None:
        spec = self.service.build(
            concept_name="二叉树遍历",
            concept_slug="binary-tree-traversal",
            objective="理解前序遍历",
            resource_type="guided_note",
        )

        self.assertIsNone(spec)

    def test_unsupported_video_topic_falls_back_without_raw_svg(self) -> None:
        spec = self.service.build(
            concept_name="红黑树旋转",
            concept_slug="red-black-tree",
            objective="理解旋转",
            resource_type="teaching_video",
        )

        self.assertIsNone(spec)


if __name__ == "__main__":
    unittest.main()
