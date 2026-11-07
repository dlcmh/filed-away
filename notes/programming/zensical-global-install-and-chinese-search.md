# Zensical: global install, Chinese search, and Cloudflare Pages

> Based on a DeepSeek conversation about running Zensical without project-local dependencies and publishing it with Cloudflare Pages: [shared conversation](https://chat.deepseek.com/share/jr38t1uqx0smokagq6).

Zensical is a static documentation site generator that can run as a globally installed `uv` tool. The move away from mdBook was motivated by search quality: Zensical provides working Chinese search, including CJK tokenization. mdBook's default search has historically been weak for Chinese and Japanese content without plugins or preprocessing.

## Global installation with uv

Install Zensical into an isolated tool environment:

```bash
uv tool install zensical
```

This makes `zensical` available on `PATH` without creating a project virtual environment or `pyproject.toml`. For a one-off run, `uvx zensical` is also available.

Update it in place:

```bash
uv tool upgrade zensical
```

The maintainers recommend a project virtual environment when version reproducibility matters. A global tool install is appropriate for a rolling, latest-version workflow.

## Minimal project

Zensical still needs a configuration file and a content directory:

```text
my-site/
├── zensical.toml
└── docs/
    └── index.md
```

A minimal `zensical.toml`:

```toml
[project]
site_name = "Lorem Ipsum"
docs_dir = "docs"
```

Preview locally:

```bash
zensical serve
```

`zensical serve` is only a local preview. To produce the static site, run:

```bash
zensical build
```

The generated output is written to `site/`.

For Chinese pages, use UTF-8 Markdown, which is the normal default. ASCII filenames and URL slugs avoid routing quirks in static-site tooling even when the search index handles CJK text correctly.

## Deploying to Cloudflare Pages

Build first:

```bash
zensical build
```

Then choose one of two deployment methods.

**Drag-and-drop:** In the Cloudflare dashboard, open **Workers & Pages**, create an application, and upload the `site/` folder. The site becomes available at `<project-name>.pages.dev`. This method has a limit of 1,000 files.

**Wrangler:** For larger or frequently updated sites:

```bash
npm install -g wrangler
wrangler login
wrangler pages project create
wrangler pages deploy site
```

After each content change, rebuild with `zensical build` and redeploy.

## What to ignore in Git

For a global tool installation, only generated and system files need to be ignored:

```gitignore
# Zensical build output
site/

# macOS metadata
.DS_Store
```

A local `.venv/` is unnecessary because Zensical is installed as a `uv` tool rather than into the project.

## Summary

- Install Zensical globally with `uv tool install zensical`.
- Configure it with `zensical.toml` and a `docs/` directory.
- Use `zensical serve` for preview and `zensical build` for static output.
- Chinese search, including CJK tokenization, is the reason for preferring Zensical over mdBook.
- Deploy the generated `site/` directory through Cloudflare Pages directly or with Wrangler.
- Ignore `site/` and `.DS_Store`; no project virtual environment is required for the global-tool setup.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/jr38t1uqx0smokagq6).
