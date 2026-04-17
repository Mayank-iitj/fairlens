# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  # FairLens Frontend

  React 18 + TypeScript frontend for FairLens.

  ## Stack

  - Vite
  - Tailwind CSS (custom warm-brown FairLens palette)
  - React Router
  - React Query
  - Zustand
  - React Hook Form + Zod
  - Recharts
  - Framer Motion

  ## Run

  ```powershell
  npm install
  npm run dev
  ```

  Set API base URL if needed:

  ```powershell
  $env:VITE_API_URL="http://localhost:8000/api/v1"
  ```

  ## Main routes

  - `/`
  - `/login`
  - `/register`
  - `/dashboard`
  - `/audit/new`
  - `/audit/:id`
  - `/reports`
  - `/monitor`
  - `/settings`
