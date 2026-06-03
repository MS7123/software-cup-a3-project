import { expect, test } from "@playwright/test";

test("student UI completes the current MVP learning loop", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Data structures learning loop" })).toBeVisible();

  await page.getByTestId("load-demo-button").click();
  await expect(page.getByText("Loaded").first()).toBeVisible();

  const profiles = page.getByTestId("profile-option");
  await expect(profiles).toHaveCount(3);
  await profiles.nth(1).click();

  await page.getByTestId("create-path-button").click();
  const pathItems = page.getByTestId("path-item-card");
  await expect(pathItems).toHaveCount(5);
  await expect(pathItems.first()).toContainText("Step 1");
  await pathItems.nth(1).click();
  await expect(page.getByTestId("current-node")).toBeVisible();

  await page.getByTestId("generate-resource-button").click();
  await expect(page.getByTestId("output-block").filter({ hasText: "guided_note" })).toBeVisible();

  await page.getByTestId("tutor-question").fill("How should I compare BFS and DFS before a quiz?");
  await page.getByTestId("ask-tutor-button").click();
  await expect(page.getByTestId("output-block").filter({ hasText: "Tutor answer" })).toBeVisible();

  await page.getByTestId("generate-quiz-button").click();
  await expect(page.getByTestId("quiz-question")).toBeVisible();
  await page.getByTestId("quiz-answer").fill("Use BFS for level-order exploration and DFS for depth-first traversal.");
  await page.getByTestId("submit-answer-button").click();
  await expect(page.getByText("Score")).toBeVisible();
  await expect(page.getByTestId("evaluator-feedback")).toBeVisible();

  await expect(page.getByTestId("run-card")).toHaveCount(5);
  await expect(page.getByText("Agent run trace")).toBeVisible();
});
