# NeuralWatt Mobile

The mobile client is an Expo React Native companion to the React dashboard. It
uses the same FastAPI account, household, analytics, forecast, recommendation,
and anomaly APIs.

## Local development

1. Copy `.env.example` to `.env`.
2. Replace `192.168.1.10` with the computer's LAN address when testing on a
   physical phone. Android emulators can use `10.0.2.2`; iOS simulators can use
   `localhost`.
3. Install dependencies with `npm install`.
4. Start the backend and MongoDB from the repository root.
5. Run `npm start`, then open the project in Expo Go or a simulator.

```bash
cd mobile
cp .env.example .env
npm install
npm start
```

Run `npm run typecheck` before committing mobile changes.

## Native builds

Install and authenticate the EAS CLI, assign the final iOS and Android app
identifiers in `app.json`, then create store-ready builds:

```bash
npx eas-cli build --platform all --profile production
```

The `preview` profile creates internal test builds. The `production` profile is
intended for App Store and Play Store submission. Store credentials, signing
keys, API secrets, and production service URLs must not be committed.

## Current scope

- Shared registration, login, and secure session persistence
- Live household power over the existing WebSocket
- Daily usage and KSEB bill estimate
- Energy recommendations and anomaly history
- Account, household, and active-device summary

Remote push delivery is a follow-up backend capability; the alerts tab
currently presents alerts already recorded by NeuralWatt.
