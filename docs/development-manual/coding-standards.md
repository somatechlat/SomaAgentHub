# SomaAgentHub Coding Standards

**A guide to the coding conventions, style, and best practices for the SomaAgentHub codebase.**

This document outlines the coding standards that all contributors must follow. Consistency in our code is crucial for readability, maintainability, and collaboration.

---

## 🎯 Guiding Principles

- **Readability Counts**: Write code for humans first, machines second.
- **Be Consistent**: Adhere to the established style of the codebase.
- **Keep It Simple**: Prefer clear, straightforward code over overly complex solutions.
- **Automate Enforcement**: We use tools like Ruff and Prettier to automate formatting and linting.

---

## 🐍 Python Style Guide

We follow **PEP 8** as our base style guide, with specific configurations enforced by **Ruff**.

### Configuration
- The Ruff configuration is defined in `pyproject.toml`.
- **Line Length**: 120 characters.
- **Formatting**: We use Ruff's integrated formatter, which is compatible with Black.

### Key Conventions
- **Imports**:
    - Imports should be grouped in the following order: standard library, third-party, and then local application imports.
    - Ruff's `organize-imports` handles this automatically.
- **Type Hinting**:
    - All function signatures must include type hints.
    - Use modern type hints (e.g., `list[str]` instead of `List[str]`).
    ```python
    def get_user(user_id: int) -> User | None:
        # function body
    ```
- **Docstrings**:
    - All public modules, classes, and functions must have a docstring.
    - We use the **Google Style** for docstrings.
    ```python
    """A brief summary of the module.

    A more detailed description of the module's contents and purpose.
    """

    def my_function(arg1: str, arg2: int) -> bool:
        """Does something interesting.

        Args:
            arg1: The first argument.
            arg2: The second argument.

        Returns:
            True if successful, False otherwise.
        """
        return True
    ```
- **Naming**:
    - `snake_case` for variables, functions, and modules.
    - `PascalCase` for classes.
    - `UPPER_SNAKE_CASE` for constants.

### Automated Checks
Before committing, always run the linter and formatter.

```bash
# Check for linting errors
ruff check .

# Automatically fix what can be fixed
ruff check . --fix

# Format the code
ruff format .
```

---

## 📜 TypeScript/JavaScript Style Guide

For our frontend code (React), we use **Prettier** for formatting and **ESLint** for linting.

### Configuration
- Prettier configuration is in `.prettierrc`.
- ESLint configuration is in `.eslintrc.js`.

### Key Conventions
- **Formatting**: Prettier handles all formatting automatically.
- **Naming**:
    - `camelCase` for variables and functions.
    - `PascalCase` for components and types.
- **Components**:
    - Use functional components with hooks.
    - Define props using TypeScript interfaces.
    ```tsx
    import React from 'react';

    interface MyComponentProps {
      title: string;
    }

    const MyComponent: React.FC<MyComponentProps> = ({ title }) => {
      return <div>{title}</div>;
    };

    export default MyComponent;
    ```

### Automated Checks
```bash
# Run ESLint
npm run lint

# Fix ESLint errors
npm run lint:fix

# Run Prettier
npm run format
```

---

## 📝 General Best Practices

### Git Commits
- Follow the **Conventional Commits** specification.
- **Format**: `<type>(<scope>): <subject>`
- **Examples**:
    - `feat(gateway): add user authentication endpoint`
    - `fix(orchestrator): correct workflow timeout logic`
    - `docs(api): update OpenAPI specification for users`
    - `test(memory): add unit tests for semantic search`

### Error Handling
- **Be Specific**: Catch specific exceptions, not generic `Exception`.
- **Provide Context**: Log errors with useful context for debugging.
- **Consistent Error Responses**: APIs should return a standardized JSON error format.

### API Design
- Follow **RESTful** principles.
- Use nouns for resource URLs (e.g., `/users`, `/workflows`).
- Use verbs for actions in the HTTP method (e.g., `GET`, `POST`, `DELETE`).
- Version your APIs (e.g., `/v1/users`).

---
## 🔗 Related Documentation
- **[Contribution Process](contribution-process.md)**: For the full development workflow.
- **[Testing Guidelines](testing-guidelines.md)**: For how to write and run tests.
