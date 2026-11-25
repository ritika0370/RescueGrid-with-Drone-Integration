# CIRRUS Response Coordination Prototype

A frontend prototype for citizen emergency reporting, department coordination, and manually piloted survey missions. It contains a Next.js operations dashboard and a separate Expo Router citizen application. All seeded incident, location, drone, pilot, and observation records are simulated and visibly labelled; they are not emergency-service data.

## Apps

- **Operations dashboard** — Next.js App Router at `/`. Overview, incidents and original linked citizen reports, fleet, pilot mission queue, and intelligence/report screens.
- **Citizen reporting companion** — responsive browser walkthrough at `/citizen` and native Expo app in `mobile/`.
- **Sign-in screen** — `/login`. Connect this form to the backend identity provider; frontend roles are not an authorization boundary.

## Development

Install all web and Expo workspace dependencies with `pnpm install`. Run the operations dashboard with `pnpm dev` at `http://localhost:3000`. Start the citizen app with `pnpm --filter cirrus-citizen run start` for Expo Go / simulators, or `pnpm --filter cirrus-citizen run web` for the browser preview. Expo Go or a configured simulator is required to exercise native camera, microphone, and location permissions. Environment variables are listed in `.env.example`; for a physical device, set `EXPO_PUBLIC_API_BASE_URL` to a backend host reachable over your LAN instead of `localhost`.

## Demo mode and backend connection

`NEXT_PUBLIC_DEMO_MODE=true` selects fixtures from `shared/demo-data.ts`; the fixture adapter is isolated in `lib/demo-service.ts`. The dashboard makes no simulated telemetry or live WebSocket claims in demo mode. The REST client is `lib/api.ts`, and the operations data selector is `lib/coordination.ts`. Set `NEXT_PUBLIC_DEMO_MODE=false`, `NEXT_PUBLIC_API_BASE_URL`, and optionally `NEXT_PUBLIC_WS_URL` to use the separate backend. The backend must authorize every operation; hiding controls in the frontend is not security.

The API client is prepared for reports, media and updates; incidents, assignment and job cards; drone inventory; mission accept/status/findings; and realtime events. Adjust endpoint paths and payloads in `lib/api.ts` to match the backend contract without changing view components. The Expo app has a corresponding isolated client in `mobile/src/api.ts` and reads `EXPO_PUBLIC_API_BASE_URL` / `EXPO_PUBLIC_DEMO_MODE`.

## Safety and data handling

The SOS flow permits a minimal report with a category and location, and it labels manually entered locations. The prototype does not claim a rescue dispatch, invent emergency numbers, control drones, or treat possible observations as confirmed people. AI summaries and confidence in the seed data are illustrative and advisory only. Do not put real personal or emergency data into this demo environment.

For production, configure trusted map tiles, authenticated uploads, secure native token storage, backend authorization, location retention, consent, audit logging, and a verified emergency-contact configuration. The local prototype uses OpenStreetMap tiles for the simulated incident map. No official department logo or affiliation is represented.
