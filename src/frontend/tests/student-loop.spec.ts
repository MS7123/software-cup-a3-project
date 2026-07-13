import { expect, test } from "@playwright/test";

test("学生端界面可以完成主要学习闭环", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "个性化学习资源生成与教师协同工作台" })).toBeVisible();

  await page.getByRole("button", { name: "打开设置与调试" }).click();
  await page.getByTestId("load-demo-button").click();
  await expect(page.getByTestId("load-demo-button")).toBeEnabled();
  const demoStatus = await page.request.get("/api/v1/demo-data/status");
  expect(demoStatus.ok()).toBeTruthy();
  const demoBody = await demoStatus.json();
  expect(demoBody.concept_count).toBe(24);
  expect(demoBody.document_count).toBeGreaterThanOrEqual(8);
  expect(demoBody.chunk_count).toBeGreaterThanOrEqual(24);
  await page.locator('[role="dialog"]').getByRole("button", { name: "关闭设置与调试" }).click();

  await page.getByRole("button", { name: "知识库", exact: true }).click();
  await page.getByRole("button", { name: "+ 录入资料" }).click();
  await page.getByTestId("knowledge-file").setInputFiles({
    name: "bfs-dfs-smoke.md",
    mimeType: "text/markdown",
    buffer: Buffer.from(
      "# BFS 与 DFS\nBFS 使用队列逐层扩展节点，适合无权图最短路径；DFS 使用递归或栈深入遍历，适合回溯和连通性分析。"
    )
  });
  await page.getByTestId("upload-knowledge-button").click();
  await expect(page.getByTestId("knowledge-import-result")).toContainText("bfs-dfs-smoke.md");
  await expect(page.getByTestId("knowledge-import-result")).toContainText("已导入");
  await expect(page.getByTestId("document-list")).toContainText("bfs-dfs-smoke.md");
  await page.locator('[role="dialog"][aria-label="新建资料"]').getByRole("button", { name: "关闭资料录入" }).click();

  await page.getByRole("button", { name: "学生画像", exact: true }).click();
  await page
    .getByTestId("profile-dialogue")
    .fill("我基础比较薄弱，想每天 1 小时复习二叉树遍历和图搜索，希望多给例题、图解和代码实操。");
  await page.getByTestId("build-profile-button").click();
  await expect(page.getByTestId("profile-dimensions")).toContainText("六维动态学生画像");
  await expect(page.getByTestId("profile-history")).toContainText("画像变化历史");
  await expect(page.getByTestId("profile-latest-change")).toBeVisible();

  await page.getByRole("button", { name: "学习路径", exact: true }).click();
  await page.getByTestId("create-path-button").click();
  await expect(page.getByTestId("path-item-card").first()).toBeVisible();
  await expect(page.getByTestId("path-intent-summary")).toContainText("本次重点");
  await expect(page.getByTestId("path-intent-summary")).toContainText("二叉树遍历");
  await expect(page.getByTestId("path-intent-summary")).toContainText("BFS/DFS");
  await expect(page.getByTestId("path-intent-summary")).toContainText("课程小测准备");
  await expect(page.getByTestId("path-intent-summary")).toContainText("重点巩固");
  await expect(page.getByTestId("path-milestone")).toContainText("课程小测模拟检验");
  await page.getByTestId("path-item-card").nth(1).click();
  await page.getByTestId("complete-path-item-button").click();
  await expect(page.getByTestId("complete-path-item-button")).toContainText("当前节点已完成");

  await page.getByRole("button", { name: "资源生成", exact: true }).click();
  await expect(page.getByTestId("current-node")).toBeVisible();
  await page.getByTestId("generate-resource-button").click();
  await expect(page.getByTestId("output-block")).toBeVisible();

  await page.getByRole("button", { name: "教师答疑", exact: true }).click();
  await page.getByTestId("tutor-question").fill("我应该怎样区分广度优先搜索和深度优先搜索？");
  await page.getByTestId("ask-tutor-button").click();
  await expect(page.getByTestId("markdown-body").last()).toBeVisible();

  await page.getByRole("button", { name: "智能测验", exact: true }).click();
  await page.getByTestId("generate-quiz-button").click();
  await expect(page.getByTestId("quiz-question")).toBeVisible();
  await expect(page.getByTestId("auto-profile-update-toggle")).toBeChecked();
  await page.getByTestId("quiz-answer").fill("广度优先搜索按层推进，深度优先搜索优先向深处探索。");
  await page.getByTestId("submit-answer-button").click();
  await expect(page.getByTestId("evaluator-feedback")).toBeVisible();
  await expect(page.getByRole("button", { name: "学习评估" })).toHaveAttribute("aria-current", "page");
  await page.getByRole("button", { name: "学生画像", exact: true }).click();
  await expect(page.getByTestId("profile-latest-change")).toBeVisible();
  await expect(page.getByTestId("profile-history")).toContainText("quiz");
  await expect(page.getByTestId("profile-history")).toContainText("证据");
});

test("低置信度目标保留输入并显示中文改写提示", async ({ page }) => {
  const loaded = await page.request.post("/api/v1/demo-data/load");
  expect(loaded.ok()).toBeTruthy();
  await page.goto("/");
  await page.getByRole("button", { name: "学习路径", exact: true }).click();
  const goalInput = page.getByLabel("学习目标");
  await goalInput.fill("把这个再弄扎实一点");
  await page.getByTestId("create-path-button").click();
  await expect(page.locator(".error-note")).toContainText("知识点、学习目的或时间要求");
  await expect(goalInput).toHaveValue("把这个再弄扎实一点");
});
