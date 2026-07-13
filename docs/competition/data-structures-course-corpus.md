# 《数据结构》课程知识库说明

## 课程范围

COMP0001 使用仓库内的版本化课程资料构造完整《数据结构》课程知识库。课程覆盖 **8 个章节**和 **24 个知识点**：

1. 绪论与复杂度分析
2. 线性表与链表
3. 栈、队列与递归
4. 树与二叉树
5. 图与图遍历
6. 查找
7. 排序
8. 综合应用与算法实践

每个章节资料包含核心概念、例题或练习、易错点和 Python 代码案例。知识点图通过 `ConceptRelation` 保存章节内和章节间的 prerequisite / related 关系。

## 资料位置

课程 Markdown 资料位于：

```text
data/course-corpus/data-structures/
```

课程元数据、知识点和关系位于：

```text
src/backend/app/seed/demo_data.py
```

## 自动加载流程

调用现有接口：

```text
POST /api/v1/demo-data/load
```

系统会按以下顺序执行：

1. 创建或补齐《数据结构》课程、知识点和先修关系。
2. 保留原有 MVP seed 资料，确保旧演示兼容。
3. 通过现有 `DocumentIngestionService` 导入 8 份章节 Markdown。
4. 使用现有 parser 和 `ChunkingService` 创建 `DocumentChunk`。
5. 为章节资料写入 `document:{id}#chunk:{index}` 格式的真实 `source_ref`。
6. 为 chunk 补充章节、课程 corpus version 和关联知识点元数据。

重复调用会根据文档标题、来源类型和 chunk 内容复用已有文档，不会重复创建课程资料。

## 验收演示

```text
Load demo data
-> 查看数据结构课程图
-> 搜索“二分查找为什么需要有序序列”
-> 查看 document:* source_ref
-> 向 Tutor 提问同一问题
-> 生成 guided_note 或 practice resource
-> 检查 Tutor / Resource 的 source_refs
```

默认使用 SQLite、keyword retrieval 和 rule-based fallback，不要求 API key、远程 LLM 或向量数据库。
