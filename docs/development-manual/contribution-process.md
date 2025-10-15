# SomaAgentHub Contribution Process

**A step-by-step guide for contributing code, documentation, and improvements to SomaAgentHub.**

We welcome and encourage contributions from the community. This guide outlines the entire process, from finding an issue to getting your pull request merged.

---

## 🎯 Contribution Workflow

We follow a standard GitHub fork-and-pull model.

```
1. Find an Issue to Work On
   (GitHub Issues)
       │
       ▼
2. Fork the Repository
   (Your GitHub Account)
       │
       ▼
3. Create a Feature Branch
   (git checkout -b ...)
       │
       ▼
4. Make Changes & Write Tests
   (Your Local Machine)
       │
       ▼
5. Run Quality Checks
   (make lint && make test)
       │
       ▼
6. Submit a Pull Request
   (GitHub UI)
       │
       ▼
7. Code Review & Discussion
   (GitHub PR Comments)
       │
       ▼
8. Merge to Main
   (Maintainers)
```

---

## 🚀 Step-by-Step Guide

### 1. Find an Issue
- **Good First Issues**: Look for issues tagged `good first issue`. These are great for new contributors.
- **Help Wanted**: Issues tagged `help wanted` are well-defined tasks that we'd love community help with.
- **Bugs**: Feel free to pick up any issue tagged `bug`.
- **Propose a New Feature**: If you have an idea, please open a "Feature Request" issue first to discuss it with the maintainers.

Once you decide to work on an issue, please leave a comment to let others know.

### 2. Fork and Branch
1.  **Fork the repository** to your own GitHub account.
2.  **Clone your fork** to your local machine:
    ```bash
    git clone https://github.com/<your-username>/somaAgentHub.git
    cd somaAgentHub
    ```
3.  **Add the upstream remote** to keep your fork in sync:
    ```bash
    git remote add upstream https://github.com/somatechlat/somaAgentHub.git
    ```
4.  **Create a descriptive feature branch** off the `main` branch:
    ```bash
    git checkout -b feat/add-new-feature # For features
    git checkout -b fix/resolve-bug-123  # For bug fixes
    ```

### 3. Code and Test
- **Write your code**: Follow the [Coding Standards](coding-standards.md).
- **Write tests**: All new code must be accompanied by tests. Follow the [Testing Guidelines](testing-guidelines.md).
- **Update documentation**: If your change affects user-facing behavior, please update the relevant documentation.

### 4. Run Quality Checks
Before submitting your changes, ensure all quality checks pass locally.

```bash
# Run all checks
make lint
make test
```

### 5. Commit Your Changes
- We use the **Conventional Commits** standard.
- Your commit messages must be in the format `<type>(<scope>): <description>`.

```bash
# Example commit
git add .
git commit -m "feat(gateway): add rate limiting to chat endpoint"
```

### 6. Submit a Pull Request (PR)
1.  **Push your branch** to your fork:
    ```bash
    git push origin feat/add-new-feature
    ```
2.  **Open a Pull Request** from your fork to the `main` branch of the upstream repository.
3.  **Fill out the PR template**:
    - Provide a clear title and description.
    - Link to the issue you are resolving (e.g., `Closes #123`).
    - Include screenshots or GIFs for UI changes.

### 7. Code Review
- A maintainer will be assigned to review your PR.
- Be responsive to feedback and questions.
- Make any requested changes by pushing new commits to your branch. The PR will update automatically.

### 8. Merge
- Once your PR is approved and all CI checks pass, a maintainer will merge it.
- Congratulations, and thank you for your contribution!

---

## ✍️ Contribution Areas

We welcome contributions of all kinds:

- **Code**: New features, bug fixes, performance improvements.
- **Documentation**: Improving guides, tutorials, and API references.
- **Testing**: Adding new tests and improving test coverage.
- **Bug Reports**: Submitting well-documented bug reports.
- **Feature Requests**: Proposing and discussing new ideas.

---
## 🔗 Related Documentation
- **[Local Setup Guide](local-setup.md)**: To get your environment ready.
- **[Coding Standards](coding-standards.md)**: For code style and best practices.
- **[Testing Guidelines](testing-guidelines.md)**: For how to write and run tests.
```
