import { expect, test } from "@playwright/test";

test("学生端界面可以完成主要学习闭环", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "个性化学习资源生成与多智能体协同工作台" })).toBeVisible();

  await page.getByTestId("load-demo-button").click();
  await expect(page.getByText("已加载").first()).toBeVisible();

  await page.getByTestId("knowledge-title").fill("广度优先与深度优先测试资料.md");
  await page
    .getByTestId("knowledge-content")
    .fill("广度优先搜索使用队列逐层扩展节点，适合无权图最短路径；深度优先搜索使用递归或栈深入遍历，适合回溯和连通性分析。");
  await page.getByTestId("import-knowledge-button").click();
  await expect(page.getByTestId("knowledge-import-result")).toContainText("广度优先与深度优先测试资料.md");
  await expect(page.getByTestId("knowledge-import-result")).toContainText("已导入");
  await expect(page.getByTestId("document-list")).toBeVisible();
  await expect(page.getByTestId("document-row").first()).toContainText("广度优先与深度优先测试资料.md");

  await page.getByTestId("profile-dialogue").fill("我基础比较薄弱，想每天 1 小时复习二叉树遍历和图搜索，希望多给例题、图解和代码实操。");
  await page.getByTestId("build-profile-button").click();
  await expect(page.getByTestId("profile-dimensions")).toContainText("六维学生画像");

  await page.getByTestId("create-path-button").click();
  await expect(page.getByTestId("planner-loading")).toBeVisible();
  const pathItems = page.getByTestId("path-item-card");
  await expect(pathItems.first()).toContainText("第");
  await pathItems.nth(1).click();
  await expect(page.getByTestId("current-node")).toBeVisible();

  await page.getByTestId("generate-resource-button").click();
  await expect(page.getByTestId("resource-loading")).toBeVisible();
  await expect(page.getByTestId("output-block").first()).toBeVisible();

  await page.getByTestId("tutor-question").fill("我应该怎样区分广度优先搜索和深度优先搜索？");
  await page.getByTestId("ask-tutor-button").click();
  await expect(page.getByTestId("tutor-loading")).toBeVisible();
  await expect(page.getByTestId("output-block").filter({ hasText: "辅导答复" })).toBeVisible();

  await page.getByTestId("generate-quiz-button").click();
  await expect(page.getByTestId("quiz-loading")).toBeVisible();
  await expect(page.getByTestId("quiz-question")).toBeVisible();
  await expect(page.getByTestId("auto-profile-update-toggle")).toBeChecked();
  await page.getByTestId("quiz-answer").fill("广度优先搜索按层推进，深度优先搜索优先向深处探索。");
  await page.getByTestId("submit-answer-button").click();
  await expect(page.getByTestId("evaluator-loading")).toBeVisible();
  await expect(page.getByRole("heading", { name: "学习效果评估" })).toBeVisible();
  await expect(page.getByTestId("evaluator-feedback")).toBeVisible();

  await expect(page.getByTestId("run-card").first()).toBeVisible();
});
