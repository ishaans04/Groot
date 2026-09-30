repo: ishaans04/Orbit
branch: main
path: frontend

## Last sync
date: 2026-09-30T00:58:00Z

### Updated in this project
- Rebuilt Landing and Dashboard as one standalone GROOT UI (frontend only; repo untouched)
- Replaced all Orbit briefing content with the GROOT Final Concept Paper
- Replaced the dashboard with the GROOT Console (mission compiler log, decision graph, decision state, memory)
- Landing gained scroll-animated Product, Architecture, Decision Room and Roadmap sections

## Screen map
| Project screen | Repo files |
| --- | --- |
| GROOT.dc.html — Landing | frontend/src/pages/Landing.jsx, frontend/src/components/OrbitBackground.jsx, frontend/src/components/MouseSpotlight.jsx, frontend/src/components/TypingHeroWord.jsx, frontend/index.html |
| GROOT.dc.html — Console (new design, replaces Dashboard) | frontend/src/pages/Dashboard.jsx (replaced) |
| GROOT v1.dc.html — previous Mission Control version | frontend/src/pages/Dashboard.jsx |
| assets/groot-styles.css | frontend/src/styles.css, frontend/tailwind.config.js |
| assets/icons.js | lucide-react icons (frontend/package.json) |
