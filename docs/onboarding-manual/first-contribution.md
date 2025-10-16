# Your First Contribution

**A step-by-step guide to making your first code contribution to SomaAgentHub.**

This guide will walk you through the entire process of finding a task, making a code change, and submitting it for review. The goal is to help you successfully merge your first pull request.

---

## 🎯 Goal

By the end of this guide, you will have:
- Found a suitable first issue to work on.
- Created a feature branch for your changes.
- Made a small code change.
- Run tests to verify your change.
- Submitted a pull request (PR) for review.

---

## 🚀 Step 1: Find a "Good First Issue"

We curate a list of issues that are perfect for new contributors.

1.  **Go to the GitHub Issues tab** of the SomaAgentHub repository.
2.  **Filter by the `good first issue` label.**
3.  **Read through the issues** and find one that seems interesting to you. They are usually small, well-defined tasks.
4.  **Leave a comment** on the issue you've chosen, saying something like "I'd like to work on this!" This lets the team know you've picked it up.

---

## 🌿 Step 2: Create a Branch

Before you start coding, create a new branch for your changes.

1.  **Make sure you are on the `main` branch** and have the latest changes:
    ```bash
    git checkout main
    git pull upstream main
    ```
2.  **Create a new branch**. Name it descriptively.
    ```bash
    # Example for a feature
    git checkout -b feat/update-welcome-message

    # Example for a bug fix
    git checkout -b fix/login-button-color
    ```

---

## 💻 Step 3: Make Your Code Change

Now it's time to code!

1.  **Open the project** in your favorite editor (like VS Code).
2.  **Make the necessary code changes** to address the issue.
3.  **Don't forget to add a test!** If you fix a bug, write a test that would have failed before your fix. If you add a feature, write a test that verifies the new functionality.

---

## ✅ Step 4: Test Your Change

Before you submit your work, make sure it hasn't broken anything.

1.  **Run the tests** for the service you changed:
    ```bash
    # Example if you changed the gateway-api
    make test-service SERVICE=gateway-api
    ```
2.  **Run the linters** to check for style issues:
    ```bash
    make lint
    ```
    *Tip: The linter can fix many issues automatically with `ruff check . --fix`.*

---

## 💾 Step 5: Commit Your Work

Commit your changes with a clear, descriptive message. We follow the **Conventional Commits** standard.

```bash
# Stage your changes
git add .

# Commit them
git commit -m "feat(ui): update welcome message on homepage"
```

---

## ⬆️ Step 6: Submit a Pull Request

It's time to share your work with the team.

1.  **Push your branch** to your fork on GitHub:
    ```bash
    git push origin feat/update-welcome-message
    ```
2.  **Go to the SomaAgentHub repository** on GitHub. You should see a prompt to "Compare & pull request". Click it.
3.  **Fill out the PR template**:
    - **Title**: Your commit message is usually a good title.
    - **Description**: Briefly explain what you changed and why.
    - **Link the issue**: Add a line like `Closes #123` to automatically link and close the issue when your PR is merged.
4.  **Click "Create pull request"**.

---

## 🎉 Step 7: Code Review

- A team member will be automatically assigned to review your PR.
- They may leave comments or request changes. This is a normal and healthy part of the process!
- To make changes, just push new commits to your branch. The PR will update automatically.
- Once your PR is approved and all checks pass, a maintainer will merge it.

**Congratulations! You've made your first contribution to SomaAgentHub!**
```