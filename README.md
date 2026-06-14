# Multiplanar Fabric AI Networking Primer

MkDocs site that renders **your HTML files** as themed documentation pages.

## Quick start

```bash
make install
make serve     # http://127.0.0.1:8000
```

## Adding HTML pages

1. Drop `.html` files into `content/html/`
2. Run `make generate` (or `make serve` / `make build`)
3. Each file becomes a page under **Pages** in the site navigation

Co-located assets (CSS, JS, images) in the same folder as an HTML file are copied to `docs/assets/html/<page>/` and paths are rewritten automatically.

## Repository layout

```
.
├── .github/workflows/     # CI: validate build, deploy to GitHub Pages
├── content/
│   └── html/              # ← put your HTML files here
├── docs/
│   ├── index.md
│   ├── generated/         # auto-generated (do not edit)
│   ├── assets/html/       # copied static assets per page
│   └── stylesheets/
├── infrastructure/
│   ├── docker/
│   └── nginx/
├── scripts/
│   ├── generate_pages.py
│   └── build.sh
├── mkdocs.yml
├── requirements.txt
└── Makefile
```

## Commands

| Command | Description |
|---------|-------------|
| `make install` | Install Python dependencies |
| `make generate` | Regenerate markdown from HTML |
| `make build` | Generate + build static site to `site/` (custom domain URL) |
| `make build-github` | Build for `mbalagot12.github.io/multiplanar-fabric/` |
| `make build-custom` | Build for `multiplanar.agentic24x7.net` |
| `make serve` | Generate + local dev server |
| `make deploy` | Build and publish to `gh-pages` branch |
| `make deploy-github` | Deploy with GitHub Pages URL |
| `make deploy-custom` | Deploy with Cloudflare custom domain URL |
| `make clean` | Remove build artifacts |

## Production URL (GitHub Pages vs custom domain)

The site is published at **https://multiplanar.agentic24x7.net/** via Cloudflare DNS. You can switch back to the GitHub Pages URL without code changes:

| Target | `MKDOCS_SITE_URL` | DNS / GitHub Pages |
|--------|-------------------|--------------------|
| Custom domain (default) | `https://multiplanar.agentic24x7.net/` | CNAME `multiplanar` → `mbalagot12.github.io` in Cloudflare; custom domain set in repo **Settings → Pages**; `docs/CNAME` present |
| GitHub Pages | `https://mbalagot12.github.io/multiplanar-fabric/` | Remove custom domain in **Settings → Pages**; delete `docs/CNAME`; grey-cloud or remove Cloudflare record |

**CI / deploy:** set the repository variable `MKDOCS_SITE_URL` under **Settings → Secrets and variables → Actions → Variables**. If unset, workflows default to the custom domain. After changing the URL, merge to `main` (or run deploy) so links and assets match the active hostname.

## Docker

```bash
make build
docker build -f infrastructure/docker/Dockerfile -t multiplanar-fabric-docs .
docker run --rm -p 8080:80 multiplanar-fabric-docs
```

## HTML requirements

- Full HTML documents (`<html>`, `<head>`, `<body>`) work best; the build extracts `<body>` content and `<head>` assets.
- Fragment-only HTML (no `<body>`) is embedded as-is.
- Use `<title>` in your HTML for the MkDocs page title and nav label.
