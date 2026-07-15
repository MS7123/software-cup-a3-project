from app.schemas import (
    AnimationEdge,
    AnimationNode,
    AnimationSpecResponse,
    AnimationTimelineStep,
    BinaryTreeAnimationData,
)


class AnimationSpecService:
    """Builds validated animation data from a small server-owned template whitelist."""

    def build(
        self,
        *,
        concept_name: str,
        concept_slug: str,
        objective: str,
        resource_type: str,
    ) -> AnimationSpecResponse | None:
        if resource_type != "teaching_video":
            return None

        topic = " ".join([concept_name, concept_slug, objective]).lower()
        if not any(token in topic for token in ("二叉树", "binary-tree", "binary_tree")):
            return None

        traversal_type, order = _traversal_order(topic)
        nodes = [
            AnimationNode(id="A", label="A", x=320, y=54),
            AnimationNode(id="B", label="B", x=188, y=148),
            AnimationNode(id="C", label="C", x=452, y=148),
            AnimationNode(id="D", label="D", x=122, y=254),
            AnimationNode(id="E", label="E", x=254, y=254),
        ]
        edges = [
            AnimationEdge(source="A", target="B"),
            AnimationEdge(source="A", target="C"),
            AnimationEdge(source="B", target="D"),
            AnimationEdge(source="B", target="E"),
        ]
        captions = {
            "A": "从根节点 A 开始",
            "B": "进入 A 的左子树，访问 B",
            "C": "左子树完成后访问右子树 C",
            "D": "继续访问 B 的左孩子 D",
            "E": "再访问 B 的右孩子 E",
        }
        timeline = [
            AnimationTimelineStep(
                at_ms=index * 1100,
                action="visit",
                target=node_id,
                caption=captions[node_id],
            )
            for index, node_id in enumerate(order)
        ]
        traversal_label = {
            "PRE_ORDER": "前序遍历",
            "IN_ORDER": "中序遍历",
            "POST_ORDER": "后序遍历",
            "LEVEL_ORDER": "层序遍历",
        }[traversal_type]
        return AnimationSpecResponse(
            template_id="binary_tree_traversal",
            title=f"{concept_name} · {traversal_label}",
            description=objective,
            duration_ms=len(timeline) * 1100,
            data=BinaryTreeAnimationData(
                traversal_type=traversal_type,
                nodes=nodes,
                edges=edges,
            ),
            timeline=timeline,
        )


def _traversal_order(topic: str) -> tuple[str, list[str]]:
    orders = {
        "PRE_ORDER": (("前序", "pre-order", "preorder"), ["A", "B", "D", "E", "C"]),
        "IN_ORDER": (("中序", "in-order", "inorder"), ["D", "B", "E", "A", "C"]),
        "POST_ORDER": (("后序", "post-order", "postorder"), ["D", "E", "B", "C", "A"]),
        "LEVEL_ORDER": (("层序", "level-order", "levelorder"), ["A", "B", "C", "D", "E"]),
    }
    matched = [
        (name, order)
        for name, (tokens, order) in orders.items()
        if any(token in topic for token in tokens)
    ]
    if len(matched) == 1:
        return matched[0]
    return "PRE_ORDER", orders["PRE_ORDER"][1]
