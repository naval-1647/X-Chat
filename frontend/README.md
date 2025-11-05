# ChatX Frontend

This is a Vite + React frontend scaffold for ChatX. It expects a ChatX FastAPI backend running at `http://localhost:8000`.

Features included:
- React functional components + hooks
- Routing with `react-router-dom`
- Auth state via `AuthContext` (stores JWT in localStorage)
- Chat state via `ChatContext` (socket.io-client + axios fallback)
- Tailwind CSS integration

Setup

1. cd frontend
2. npm install
3. npm run dev

Notes

- The current `ChatContext` uses `socket.io-client`. If your FastAPI websocket endpoint is a raw WebSocket (`ws://...`) and not a socket.io server, replace the socket code with a native WebSocket client.
- API base is `http://localhost:8000` (change in `src/services/api.js` if needed).

