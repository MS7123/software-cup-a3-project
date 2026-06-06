import { expect, test } from "@playwright/test";

test("student UI completes the current MVP learning loop", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Data structures learning loop" })).toBeVisible();

  await page.getByTestId("load-demo-button").click();
  await expect(page.getByText("Loaded").first()).toBeVisible();

  const profiles = page.getByTestId("profile-option");
  await expect(profiles).toHaveCount(3);
  await page
    .getByTestId("profile-dialogue")
    .fill("我基础薄弱，想每天 1 小时复习二叉树遍历和 BFS/DFS，希望用例题和练习题准备小测");
  await page.getByTestId("build-profile-button").click();
  await expect(page.getByTestId("profile-dimensions")).toContainText("6-dimension profile");
  await expect(profiles).toHaveCount(4);

  await page.getByTestId("create-path-button").click();
  const pathItems = page.getByTestId("path-item-card");
  await expect(pathItems).toHaveCount(5);
  await expect(pathItems.first()).toContainText("Step 1");
  await pathItems.nth(1).click();
  await expect(page.getByTestId("current-node")).toBeVisible();

  await page.getByTestId("generate-resource-button").click();
  await expect(page.getByTestId("output-block").filter({ hasText: "guided_note" })).toBeVisible();
  await page.getByTestId("resource-type-coding_case").click();
  await page.getByTestId("generate-resource-button").click();
  await expect(page.getByTestId("coding-case-card")).toBeVisible();

  await page.getByTestId("tutor-question").fill("How should I compare BFS and DFS before a quiz?");
  await page.getByTestId("ask-tutor-button").click();
  await expect(page.getByTestId("output-block").filter({ hasText: "Tutor answer" })).toBeVisible();

  await page.getByTestId("generate-quiz-button").click();
  await expect(page.getByTestId("quiz-question")).toBeVisible();
  await page.getByTestId("quiz-answer").fill("Use BFS for level-order exploration and DFS for depth-first traversal.");
  await page.getByTestId("submit-answer-button").click();
  await expect(page.getByText("Score")).toBeVisible();
  await expect(page.getByTestId("evaluator-feedback")).toBeVisible();
  await expect(page.getByTestId("auto-profile-update")).toContainText("Agent step");
  await expect(page.getByTestId("profile-update-reason")).toContainText("Agent step");

  await expect(page.getByTestId("run-card")).toHaveCount(6);
  await expect(page.getByText("Agent run trace")).toBeVisible();

  await page.getByTestId("reset-demo-button").click();
  await expect(page.getByTestId("profile-option")).toHaveCount(3);
  await expect(page.getByTestId("delete-profile-button")).toHaveCount(0);
});
