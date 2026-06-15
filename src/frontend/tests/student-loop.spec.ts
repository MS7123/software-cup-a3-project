import { expect, test } from "@playwright/test";

test("student UI completes the current MVP learning loop", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Data structures learning loop" })).toBeVisible();

  await page.getByTestId("load-demo-button").click();
  await expect(page.getByText("Loaded").first()).toBeVisible();

  await page.getByTestId("knowledge-title").fill("bfs-dfs-smoke.md");
  await page
    .getByTestId("knowledge-content")
    .fill(
      "# BFS and DFS\nBFS uses a queue to expand nodes level by level, so in an unweighted graph the first time a node is reached represents the fewest edges. DFS uses a stack or recursion to go deep first."
    );
  await page.getByTestId("import-knowledge-button").click();
  await expect(page.getByTestId("knowledge-import-result")).toContainText("Document #");
  await expect(page.getByTestId("knowledge-import-result")).toContainText("document:");
  await page.getByTestId("knowledge-query").fill("BFS shortest path queue DFS stack");
  await page.getByTestId("search-knowledge-button").click();
  await expect(page.getByTestId("knowledge-search-results")).toContainText("document:");
  await expect(page.getByTestId("knowledge-search-results")).toContainText("matched");
  await expect(page.getByTestId("knowledge-search-results")).toContainText("BFS uses");

  const profiles = page.getByTestId("profile-option");
  await expect(profiles).toHaveCount(3);
  await page
    .getByTestId("profile-dialogue")
    .fill("我基础薄弱，想每天 1 小时复习二叉树遍历和 BFS/DFS，希望用例题和练习题准备小测");
  await page.getByTestId("build-profile-button").click();
  await expect(page.getByTestId("profile-dimensions")).toContainText("6-dimension profile");
  await expect(profiles).toHaveCount(4);

  await page.route("**/api/v1/learning-paths", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 120));
    await route.continue();
  });
  await page.getByTestId("create-path-button").click();
  await expect(page.getByTestId("planner-loading")).toBeVisible();
  const pathItems = page.getByTestId("path-item-card");
  await expect(pathItems).toHaveCount(5);
  await expect(pathItems.first()).toContainText("Step 1");
  await pathItems.nth(1).click();
  await expect(page.getByTestId("current-node")).toBeVisible();

  let resourceGenerateCalls = 0;
  await page.route("**/api/v1/resources/generate", async (route) => {
    resourceGenerateCalls += 1;
    await new Promise((resolve) => setTimeout(resolve, 120));
    if (resourceGenerateCalls === 1) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 9001,
          path_item_id: 1,
          resource_type: "guided_note",
          content: "guided_note\n\n**Math check**: $O(1)$ and $O(n \\log n)$ should render.",
          source_refs: [{ source_ref: "document:smoke#chunk:math", chunk_id: 1, score: 1 }],
          agent_run_id: null
        })
      });
      return;
    }
    await route.continue();
  });
  await page.getByTestId("generate-resource-button").click();
  await expect(page.getByTestId("resource-loading")).toBeVisible();
  await expect(page.getByTestId("output-block").filter({ hasText: "guided_note" })).toBeVisible();
  await expect(page.locator(".katex").first()).toBeVisible();
  await page.getByTestId("resource-type-coding_case").click();
  await page.getByTestId("generate-resource-button").click();
  await expect(page.getByTestId("coding-case-card")).toBeVisible();

  await page.route("**/api/v1/tutor/ask", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 250));
    await route.continue();
  });
  await page.getByTestId("tutor-question").fill("How should I compare BFS and DFS shortest path queue stack before a quiz?");
  await page.getByTestId("ask-tutor-button").click();
  await expect(page.getByTestId("tutor-loading")).toBeVisible();
  await expect(page.getByTestId("output-block").filter({ hasText: "Tutor answer" })).toBeVisible();
  await expect(page.getByTestId("output-block").filter({ hasText: "Tutor answer" })).toContainText("document:");
  await expect(page.getByTestId("output-block").filter({ hasText: "Tutor answer" }).getByTestId("markdown-body")).toBeVisible();

  await page.route("**/api/v1/quizzes/generate", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 120));
    await route.continue();
  });
  await page.getByTestId("generate-quiz-button").click();
  await expect(page.getByTestId("quiz-loading")).toBeVisible();
  await expect(page.getByTestId("quiz-question")).toBeVisible();
  await expect(page.getByTestId("auto-profile-update-toggle")).toBeChecked();
  await page.getByTestId("auto-profile-update-toggle").uncheck();
  await expect(page.getByTestId("auto-profile-update-toggle")).not.toBeChecked();
  await page.getByTestId("auto-profile-update-toggle").check();
  await expect(page.getByTestId("auto-profile-update-toggle")).toBeChecked();
  await page.getByTestId("quiz-answer").fill("Use BFS for level-order exploration and DFS for depth-first traversal.");
  await page.route("**/api/v1/quizzes/*/attempts", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 120));
    await route.continue();
  });
  await page.route("**/api/v1/student-profiles/*/update-from-trace", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 120));
    await route.continue();
  });
  await page.getByTestId("submit-answer-button").click();
  await expect(page.getByTestId("evaluator-loading")).toBeVisible();
  await expect(page.getByTestId("profile-update-loading")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Evaluator feedback" })).toBeVisible();
  await expect(page.getByTestId("evaluator-feedback")).toBeVisible();
  await expect(page.getByTestId("auto-profile-update")).toContainText("Agent step");
  await expect(page.getByTestId("profile-update-reason")).toContainText("Agent step");

  await expect(page.getByTestId("run-card")).toHaveCount(5);
  await expect(page.getByText("Agent run trace")).toBeVisible();

  await page.getByTestId("reset-demo-button").click();
  await expect(page.getByTestId("profile-option")).toHaveCount(3);
  await expect(page.getByTestId("delete-profile-button")).toHaveCount(0);
});
