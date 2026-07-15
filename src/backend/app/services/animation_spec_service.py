from collections.abc import Sequence

from app.schemas import (
    AnimationEdge,
    AnimationNode,
    AnimationSceneData,
    AnimationSpecResponse,
    AnimationTimelineStep,
)


TEMPLATE_BY_CONCEPT: dict[str, str] = {
    "complexity-analysis": "complexity_visualizer",
    "asymptotic-notation": "complexity_visualizer",
    "recurrence-analysis": "complexity_visualizer",
    "complexity-practice": "complexity_visualizer",
    "array-list": "linear_structure",
    "linked-list": "linear_structure",
    "linear-list-comparison": "linear_structure",
    "stack": "stack_queue_operations",
    "queue": "stack_queue_operations",
    "recursion": "stack_queue_operations",
    "tree-basics": "tree_visualizer",
    "binary-tree": "tree_visualizer",
    "binary-tree-traversal": "binary_tree_traversal",
    "search-tree": "tree_visualizer",
    "graph-representation": "graph_visualizer",
    "bfs-dfs": "graph_visualizer",
    "shortest-path": "graph_visualizer",
    "search-basics": "search_visualizer",
    "hash-table": "search_visualizer",
    "sorting-basics": "sorting_visualizer",
    "simple-sorts": "sorting_visualizer",
    "efficient-sorts": "sorting_visualizer",
    "algorithm-design": "algorithm_workflow",
    "data-structure-project": "algorithm_workflow",
}


class AnimationSpecService:
    """Build validated, server-owned animation scenes for every course concept."""

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

        template_id = TEMPLATE_BY_CONCEPT.get(concept_slug, "concept_fallback")
        if template_id == "binary_tree_traversal":
            return self._binary_tree_traversal(concept_name, concept_slug, objective)
        builders = {
            "complexity_visualizer": self._complexity,
            "linear_structure": self._linear_structure,
            "stack_queue_operations": self._stack_queue,
            "tree_visualizer": self._tree,
            "graph_visualizer": self._graph,
            "search_visualizer": self._search,
            "sorting_visualizer": self._sorting,
            "algorithm_workflow": self._workflow,
            "concept_fallback": self._fallback,
        }
        return builders[template_id](concept_name, concept_slug, objective)

    def _complexity(self, name: str, slug: str, objective: str) -> AnimationSpecResponse:
        labels = {
            "recurrence-analysis": ["T(1)", "T(n/2)", "T(n)", "合并"],
            "complexity-practice": ["常数项", "单循环", "嵌套循环", "优化后"],
        }.get(slug, ["O(1)", "O(log n)", "O(n)", "O(n²)"])
        values = [18, 34, 58, 88]
        nodes = [
            AnimationNode(id=f"c{i}", label=label, x=100 + i * 140, y=290 - value * 2, value=value, kind="bar")
            for i, (label, value) in enumerate(zip(labels, values, strict=True))
        ]
        return self._spec("complexity_visualizer", name, objective, slug, nodes, [], "compare")

    def _linear_structure(self, name: str, slug: str, objective: str) -> AnimationSpecResponse:
        labels = ["head", "12", "26", "39", "null"] if slug == "linked-list" else ["0:12", "1:26", "2:39", "3:空", "容量4"]
        nodes = [AnimationNode(id=f"l{i}", label=label, x=82 + i * 118, y=172, kind="cell") for i, label in enumerate(labels)]
        edges = [AnimationEdge(source=f"l{i}", target=f"l{i + 1}") for i in range(len(nodes) - 1)] if slug != "array-list" else []
        return self._spec("linear_structure", name, objective, slug, nodes, edges, "visit")

    def _stack_queue(self, name: str, slug: str, objective: str) -> AnimationSpecResponse:
        if slug == "queue":
            labels, action, positions = ["队首 8", "13", "21", "队尾 34"], "dequeue", [(110 + i * 135, 172) for i in range(4)]
        elif slug == "recursion":
            labels, action, positions = ["f(1)", "f(2)", "f(3)", "f(4)"], "push", [(320, 270 - i * 62) for i in range(4)]
        else:
            labels, action, positions = ["底 8", "13", "21", "栈顶 34"], "push", [(320, 270 - i * 62) for i in range(4)]
        nodes = [AnimationNode(id=f"s{i}", label=label, x=x, y=y, kind=slug) for i, (label, (x, y)) in enumerate(zip(labels, positions, strict=True))]
        return self._spec("stack_queue_operations", name, objective, slug, nodes, [], action)

    def _tree(self, name: str, slug: str, objective: str) -> AnimationSpecResponse:
        labels = ["8", "4", "12", "2", "6"] if slug == "search-tree" else ["根", "左子树", "右子树", "叶 A", "叶 B"]
        nodes, edges = _tree_scene(labels)
        return self._spec("tree_visualizer", name, objective, slug, nodes, edges, "visit")

    def _binary_tree_traversal(self, name: str, slug: str, objective: str) -> AnimationSpecResponse:
        traversal_type, order = _traversal_order(" ".join([name, slug, objective]).lower())
        nodes, edges = _tree_scene(["A", "B", "C", "D", "E"])
        captions = {
            "A": "从根节点 A 开始",
            "B": "进入 A 的左子树，访问 B",
            "C": "左子树完成后访问右子树 C",
            "D": "继续访问 B 的左孩子 D",
            "E": "再访问 B 的右孩子 E",
        }
        timeline = [AnimationTimelineStep(at_ms=i * 1100, action="visit", target=node_id, caption=captions[node_id]) for i, node_id in enumerate(order)]
        return AnimationSpecResponse(
            template_id="binary_tree_traversal",
            title=f"{name} · {_traversal_label(traversal_type)}",
            description=objective,
            duration_ms=len(timeline) * 1100,
            data=AnimationSceneData(mode=slug, traversal_type=traversal_type, nodes=nodes, edges=edges, sequence=order),
            timeline=timeline,
        )

    def _graph(self, name: str, slug: str, objective: str) -> AnimationSpecResponse:
        nodes = [
            AnimationNode(id="gA", label="A", x=110, y=165), AnimationNode(id="gB", label="B", x=255, y=72),
            AnimationNode(id="gC", label="C", x=255, y=258), AnimationNode(id="gD", label="D", x=430, y=105),
            AnimationNode(id="gE", label="E", x=520, y=230),
        ]
        edges = [AnimationEdge(source=a, target=b, label=w) for a, b, w in [("gA", "gB", "2"), ("gA", "gC", "4"), ("gB", "gD", "3"), ("gC", "gD", "1"), ("gD", "gE", "2")]]
        action = "relax" if slug == "shortest-path" else "visit"
        return self._spec("graph_visualizer", name, objective, slug, nodes, edges, action)

    def _search(self, name: str, slug: str, objective: str) -> AnimationSpecResponse:
        labels = ["0:18", "1:空", "2:42", "3:27", "4:空", "5:35"] if slug == "hash-table" else ["3", "8", "12", "19", "27", "35"]
        nodes = [AnimationNode(id=f"q{i}", label=label, x=66 + i * 96, y=170, value=i, kind="bucket") for i, label in enumerate(labels)]
        return self._spec("search_visualizer", name, objective, slug, nodes, [], "select")

    def _sorting(self, name: str, slug: str, objective: str) -> AnimationSpecResponse:
        values = [46, 18, 72, 31, 58, 24]
        nodes = [AnimationNode(id=f"b{i}", label=str(value), x=72 + i * 95, y=300 - value * 2, value=value, kind="bar") for i, value in enumerate(values)]
        return self._spec("sorting_visualizer", name, objective, slug, nodes, [], "compare")

    def _workflow(self, name: str, slug: str, objective: str) -> AnimationSpecResponse:
        labels = ["问题建模", "结构选择", "算法实现", "测试验证"] if slug == "data-structure-project" else ["分解问题", "选择策略", "证明正确", "分析复杂度"]
        nodes = [AnimationNode(id=f"w{i}", label=label, x=95 + i * 145, y=172, kind="stage") for i, label in enumerate(labels)]
        edges = [AnimationEdge(source=f"w{i}", target=f"w{i + 1}") for i in range(len(nodes) - 1)]
        return self._spec("algorithm_workflow", name, objective, slug, nodes, edges, "complete")

    def _fallback(self, name: str, slug: str, objective: str) -> AnimationSpecResponse:
        labels = [name[:18], "核心概念", "典型示例", "自我检查"]
        nodes = [
            AnimationNode(id="f0", label=labels[0], x=320, y=165, kind="focus"),
            AnimationNode(id="f1", label=labels[1], x=120, y=80),
            AnimationNode(id="f2", label=labels[2], x=520, y=80),
            AnimationNode(id="f3", label=labels[3], x=320, y=280),
        ]
        edges = [AnimationEdge(source="f0", target=f"f{i}") for i in range(1, 4)]
        return self._spec("concept_fallback", name, objective, slug, nodes, edges, "highlight")

    @staticmethod
    def _spec(
        template_id: str,
        name: str,
        objective: str,
        mode: str,
        nodes: list[AnimationNode],
        edges: list[AnimationEdge],
        action: str,
    ) -> AnimationSpecResponse:
        timeline = [
            AnimationTimelineStep(at_ms=i * 1000, action=action, target=node.id, caption=f"步骤 {i + 1}：观察 {node.label}")
            for i, node in enumerate(nodes)
        ]
        return AnimationSpecResponse(
            template_id=template_id,
            title=f"{name} · 交互演示",
            description=objective,
            duration_ms=max(1000, len(timeline) * 1000),
            data=AnimationSceneData(mode=mode, nodes=nodes, edges=edges, sequence=[node.id for node in nodes]),
            timeline=timeline,
        )


def _tree_scene(labels: Sequence[str]) -> tuple[list[AnimationNode], list[AnimationEdge]]:
    positions = [(320, 54), (188, 148), (452, 148), (122, 254), (254, 254)]
    ids = ["A", "B", "C", "D", "E"]
    nodes = [AnimationNode(id=node_id, label=label, x=x, y=y, kind="tree") for node_id, label, (x, y) in zip(ids, labels, positions, strict=True)]
    edges = [AnimationEdge(source=a, target=b) for a, b in [("A", "B"), ("A", "C"), ("B", "D"), ("B", "E")]]
    return nodes, edges


def _traversal_order(topic: str) -> tuple[str, list[str]]:
    orders = {
        "PRE_ORDER": (("前序", "pre-order", "preorder"), ["A", "B", "D", "E", "C"]),
        "IN_ORDER": (("中序", "in-order", "inorder"), ["D", "B", "E", "A", "C"]),
        "POST_ORDER": (("后序", "post-order", "postorder"), ["D", "E", "B", "C", "A"]),
        "LEVEL_ORDER": (("层序", "level-order", "levelorder"), ["A", "B", "C", "D", "E"]),
    }
    matched = [(name, order) for name, (tokens, order) in orders.items() if any(token in topic for token in tokens)]
    return matched[0] if len(matched) == 1 else ("PRE_ORDER", orders["PRE_ORDER"][1])


def _traversal_label(traversal_type: str) -> str:
    return {"PRE_ORDER": "前序遍历", "IN_ORDER": "中序遍历", "POST_ORDER": "后序遍历", "LEVEL_ORDER": "层序遍历"}[traversal_type]
