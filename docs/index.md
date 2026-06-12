# Multiplanar Fabric Documentation

This site renders HTML pages supplied in `content/html/` using MkDocs and Material for MkDocs.

## How it works

1. Add `.html` files to `content/html/`
2. Run `make generate` to create MkDocs pages under `docs/generated/`
3. Run `make serve` or `make build` to preview or publish

## Local preview

```bash
make install
make serve
```

Then open http://127.0.0.1:8000
