```markdown
# goal-cli Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the development patterns and coding conventions used in the `goal-cli` Python repository. It covers file naming, import/export styles, commit message conventions, and testing patterns. By following these guidelines, contributors can maintain consistency and quality across the codebase.

## Coding Conventions

### File Naming
- Use **PascalCase** for file names.
  - **Example:**  
    `GoalManager.py`  
    `UserSession.py`

### Import Style
- Use **relative imports** within the package.
  - **Example:**
    ```python
    from .UserSession import UserSession
    from .GoalManager import GoalManager
    ```

### Export Style
- Use **named exports** (explicitly define what is exported).
  - **Example:**
    ```python
    __all__ = ["GoalManager", "UserSession"]
    ```

### Commit Messages
- Follow **conventional commit** style.
- Use prefixes such as `docs`.
- Keep commit messages concise (average 44 characters).
  - **Example:**
    ```
    docs: update README with usage instructions
    ```

## Workflows

### Adding Documentation
**Trigger:** When updating or adding documentation files  
**Command:** `/add-docs`

1. Make your documentation changes in the appropriate `.md` or docstring locations.
2. Use a commit message with the `docs` prefix, e.g., `docs: update usage section`.
3. Push your changes and open a pull request if required.

### Updating Code with New Features or Fixes
**Trigger:** When implementing new features or fixing bugs  
**Command:** `/update-code`

1. Create or update files using PascalCase naming.
2. Use relative imports for internal modules.
3. Explicitly define exports with `__all__`.
4. Write clear, conventional commit messages.
5. Push your changes and create a pull request.

## Testing Patterns

- Test files follow the pattern `*.test.*` (e.g., `GoalManager.test.py`).
- The specific testing framework is not specified; ensure tests are discoverable by your chosen test runner.
- Place test files alongside the modules they test or in a dedicated test directory.
- Example test file name: `GoalManager.test.py`

## Commands
| Command      | Purpose                                   |
|--------------|-------------------------------------------|
| /add-docs    | Add or update documentation               |
| /update-code | Implement new features or bug fixes       |
```