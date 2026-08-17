# Repository Guidelines

## Project Structure & Module Organization

This repository is currently an instruction-only project. The top level contains:

- `Student_Project_Instructions.pdf` — the seven-page project brief and primary source of requirements.
- `AGENTS.md` — contributor and agent guidance.

There are no source, test, asset, or generated-output directories at present. If implementation files are added, keep application code in a clearly named source directory (such as `src/`), tests in `tests/` or alongside the relevant modules, and static resources in `assets/`. Keep generated files out of version control unless the project brief explicitly requires them.

## Build, Test, and Development Commands

No build, test, or local development commands are configured yet. Before adding or documenting commands, inspect the project’s package/build manifest and update this section with the exact commands contributors should run. For example, a future JavaScript project might provide `npm run dev`, `npm test`, and `npm run build`; do not assume those commands work here.

## Coding Style & Naming Conventions

Follow the formatter and linter selected when implementation begins, and commit their configuration with the code. Use two or four spaces consistently according to the language ecosystem, meaningful module and variable names, and `PascalCase` for types/components where applicable. Prefer focused modules and avoid committing editor-specific files or build artifacts.

## Testing Guidelines

No testing framework or coverage threshold is configured. New functionality should include focused automated tests once an implementation stack is chosen. Name test files after the behavior or module under test (for example, `widget.test.*`) and run the project’s documented test command before submitting changes.

## Commit & Pull Request Guidelines

The existing history contains only the initial commit (`init`), so no established commit convention can be inferred. Use concise, imperative commit subjects, such as `Add input validation`, and keep unrelated changes separate.

Pull requests should explain the change, identify affected files or requirements from the PDF, and include test results. Add screenshots or sample output when a change introduces a user-facing interface. Keep the PR narrowly scoped and call out any assumptions or follow-up work.

## Security & Configuration Tips

Do not commit credentials, private data, or local environment files. Treat the project brief as the source of truth for required behavior, and review any external dependencies before adding them.
