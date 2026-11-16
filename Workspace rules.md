# Workspace rules

You are assisting with a scientific and technical writing repository dedicated to modeling and analyzing road transport energy demand, decarbonization levers, and multi-objective optimization strategies in rural areas, using the Cuadrilla de Gorbeialdea region as a case study. The workspace operates under a zero-cost, subscription-free, automated workflow built around Visual Studio Code, Markdown, Python, Git, and GitHub Actions. All assistance, manuscript drafting, code generation, documentation, comments, and Git commit messages must be written strictly in clear, formal academic and technical English.

## Authoring environment

The manuscript is written in Markdown. The main document is `Methodology.md`. Equations use GitHub-compatible math: inline `$...$` and display `$$...$$` blocks, numbered manually with `\tag{n}`. Do not use LaTeX document commands (`\label`, `\ref`, `\eqref`, `\begin{equation}`), because the files are not compiled with LaTeX. Equation cross-references are written as "Equation (n)". Markdown files must render correctly on GitHub and in the Visual Studio Code preview.

## Repository separation

The repository separates human-authored content from auto-generated records. `methodology.md` is the primary manuscript. `log.md` is a chronological record of work sessions and is generated automatically. Local virtual environments, caches and raw data are excluded from version control through `.gitignore`.

## Automation

Every push to `main` triggers a GitHub Actions workflow that runs `generate_log.py`, reads the full Git history localized to the Europe/Madrid timezone, and regenerates `log.md`. The workflow then commits and pushes `log.md` under the GitHub Actions bot identity, ignoring bot commits so that an infinite loop never occurs.

## Commit message convention

The end of a work session is taken from the Git commit timestamp. The start is read from square brackets at the beginning of the subject line. For a same-day session the subject begins with `[HH:MM]` followed by a concise English title. For a multi-day session the brackets contain `[YYYY-MM-DD--HH:MM]`. Body lines that begin with a hyphen and a space become bullet points in the log.

## Mandatory operational rules

1. Never edit `log.md` directly: manual edits are overwritten the next time GitHub Actions runs. To change its layout or parsing behavior, modify `generate_log.py`.
2. When asked to summarize a work session or suggest a commit message, follow the bracketed start-time convention and the hyphenated task list, so that it can be pasted directly into the Visual Studio Code Source Control panel.
3. The user follows a cycle of pulling remote changes before starting work, editing and previewing locally, and committing and syncing at the end of each session.