# Web UI

React + TypeScript + Vite. The server serves the compiled result from `web/dist`, so there is nothing to run in production besides building once:

```bash
npm ci
npm run build
```

For development, run the server (`python servidor/servir.py`) and, in another terminal:

```bash
npm run dev      # Vite with hot reload
npm run lint     # oxlint
```

`npm run dev` serves the UI on its own port and proxies `/api` to the server on `127.0.0.1:8099` (see `vite.config.ts`).

Layout (same split as the server; see [docs/architecture.md](../docs/architecture.md)):

- `src/dominio/` — types and wording shared with the server
- `src/aplicacion/` — hooks: when things happen
- `src/infraestructura/` — the HTTP client, the only file that knows about HTTP
- `src/ui/` — components, each with its CSS alongside
- `public/fuentes/` — bundled fonts (SIL Open Font License)
