from app.core.enums import ProcessingStatus, ProfileType, RelationType


DEMO_COURSE = {
    "title": "数据结构",
    "description": "面向 MVP 演示的数据结构课程，覆盖复杂度分析、线性结构、树遍历和图搜索基础。",
    "is_demo": True,
}

DEMO_CONCEPTS = [
    {
        "slug": "complexity-analysis",
        "name": "复杂度分析",
        "chapter": "第 1 章 绪论",
        "description": "理解时间复杂度、空间复杂度和常见 Big-O 量级。",
        "difficulty": "basic",
    },
    {
        "slug": "linked-list",
        "name": "链表",
        "chapter": "第 2 章 线性表",
        "description": "掌握单链表节点结构、插入、删除和遍历。",
        "difficulty": "basic",
    },
    {
        "slug": "stack-queue",
        "name": "栈/队列",
        "chapter": "第 3 章 栈和队列",
        "description": "理解 LIFO/FIFO 约束及其典型应用。",
        "difficulty": "basic",
    },
    {
        "slug": "binary-tree-traversal",
        "name": "二叉树遍历",
        "chapter": "第 5 章 树和二叉树",
        "description": "掌握前序、中序、后序和层序遍历。",
        "difficulty": "medium",
    },
    {
        "slug": "bfs-dfs",
        "name": "BFS/DFS",
        "chapter": "第 6 章 图",
        "description": "理解广度优先搜索和深度优先搜索的过程、适用场景和复杂度。",
        "difficulty": "medium",
    },
]

DEMO_RELATIONS = [
    ("complexity-analysis", "linked-list", RelationType.prerequisite),
    ("linked-list", "stack-queue", RelationType.related),
    ("stack-queue", "binary-tree-traversal", RelationType.prerequisite),
    ("binary-tree-traversal", "bfs-dfs", RelationType.prerequisite),
    ("complexity-analysis", "bfs-dfs", RelationType.prerequisite),
]

DEMO_PROFILES = [
    {
        "profile_type": ProfileType.weak_foundation,
        "goal": "补齐数据结构基础，重点理解链表、栈队列和树遍历的基本操作。",
        "level": "beginner",
        "preferences": {"style": "step_by_step", "resource": "例题讲解", "pace": "slow"},
        "time_budget": "每天 1 小时，持续 2 周",
    },
    {
        "profile_type": ProfileType.exam_sprint,
        "goal": "面向近期小测快速复习复杂度、二叉树遍历和 BFS/DFS。",
        "level": "intermediate",
        "preferences": {"style": "summary_first", "resource": "高频题", "pace": "fast"},
        "time_budget": "每天 2 小时，持续 5 天",
    },
    {
        "profile_type": ProfileType.algorithm_practice,
        "goal": "通过编程练习强化链表、栈队列和搜索算法的实现能力。",
        "level": "practice_oriented",
        "preferences": {"style": "code_driven", "resource": "编程练习", "pace": "normal"},
        "time_budget": "每周 6 小时",
    },
]

DEMO_DOCUMENT = {
    "title": "数据结构 MVP 模拟课程资料",
    "source_type": "seed",
    "status": ProcessingStatus.completed,
}

DEMO_CHUNKS = [
    {
        "concept_slug": "complexity-analysis",
        "content": "复杂度分析用于估算算法随输入规模增长的资源消耗。常见时间复杂度包括 O(1)、O(log n)、O(n)、O(n log n) 和 O(n^2)。",
        "source_ref": "demo://data-structures/complexity#overview",
    },
    {
        "concept_slug": "linked-list",
        "content": "链表由节点组成，每个节点保存数据和指向后继节点的引用。插入和删除通常只需要修改相邻节点指针。",
        "source_ref": "demo://data-structures/linked-list#node",
    },
    {
        "concept_slug": "stack-queue",
        "content": "栈遵循后进先出，常用于函数调用和表达式求值；队列遵循先进先出，常用于层序遍历和任务调度。",
        "source_ref": "demo://data-structures/stack-queue#rules",
    },
    {
        "concept_slug": "binary-tree-traversal",
        "content": "二叉树遍历包括前序、中序、后序和层序。递归遍历关注根节点访问顺序，层序遍历通常借助队列完成。",
        "source_ref": "demo://data-structures/binary-tree#traversal",
    },
    {
        "concept_slug": "bfs-dfs",
        "content": "BFS 按层扩展节点，适合最短步数类问题；DFS 沿路径深入探索，适合连通性、回溯和拓扑结构分析。",
        "source_ref": "demo://data-structures/graph-search#bfs-dfs",
    },
]
