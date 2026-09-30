# Deploy the full prototype to Render

This repository has one Render service. It serves the website files and the API from the same address, so a visitor opens one link and the browser can call the API without separate frontend and backend deployments.

## Before you start

- Put this repository in a GitHub, GitLab, or other Git repository that Render can access.
- Create or sign in to a Render account.
- Be ready to choose a **paid web service**. This Blueprint attaches a 1 GB persistent disk so saved choices, meeting notes, and results survive restarts. Render does not allow a persistent disk on a free web service.

The Blueprint does not ask for passwords or external service keys. The sample company records are fictional and the service runs without third-party Python packages.

## Create the service

1. Push the repository, including the root-level `render.yaml`, to your Git provider.
2. In Render, choose **New → Blueprint** and connect the repository.
3. Review the Blueprint plan, region, and disk details. The service uses the Singapore region and the `starter` plan; change the region in `render.yaml` before creating it if another supported region is closer to your audience. The attached 1 GB disk is required for saved demo state to persist.
4. Apply the Blueprint and wait for the first deploy to finish.
5. Open the service URL shown in Render, then add `/GROOT.dc.html` to view the main website page.

The Blueprint file is at the repository root. Its `rootDir` points Render at the existing project folder, while `backend/app.py` starts one server for both the website and the API. The health check calls `/api/health`.

## Check the deployed prototype

Replace `YOUR-SERVICE.onrender.com` with the service host Render assigned:

- Website: `https://YOUR-SERVICE.onrender.com/GROOT.dc.html`
- Service status: `https://YOUR-SERVICE.onrender.com/api/health`
- Sample company overview: `https://YOUR-SERVICE.onrender.com/api/dashboard`
- Request examples: `https://YOUR-SERVICE.onrender.com/backend/demo.http`
- API guide: `https://YOUR-SERVICE.onrender.com/backend/docs/api.md`

The website files stay in their current folder and are served by the same process. Their contents are not changed by the deployment setup. The current website controls still use their original in-browser sample behavior; this deployment does not connect those controls to the new API. To present the working service logic, use the API guide and request examples alongside the website.

## Where saved data lives

The service writes its SQLite database to `/var/data/groot-demo.sqlite3`. Render mounts the Blueprint's disk at `/var/data`, so sample history and newly saved demo activity remain after a restart or deploy. The service seeds its example history only when the database is empty; redeploying does not intentionally erase existing saved decisions.

Keep the service at one instance while it uses SQLite and a disk. This prototype is designed for one small presentation service, not multiple app instances or heavy simultaneous use.

## Updates and common fixes

- Push a commit to the connected branch; Render will build and deploy it automatically.
- If a deploy fails, open the service's **Events** and **Logs** pages. The build compiles the Python files, then starts `backend/app.py`.
- If the health check fails, confirm the service starts successfully and that `/api/health` returns JSON with `"status": "ok"`.
- If the main page is not visible at the service root, open `/GROOT.dc.html` directly. The UI's existing main file is named `GROOT.dc.html`.
- The project PDF and the original handoff files are not part of the deployed web root. The project site and API guide are served from the project folder selected by `rootDir`.

## What this deploy does not add

This is a presentation prototype, not a public production system. It does not add user accounts, access controls, live company connections, live web research, audio capture, or model training. Anyone with the public service link can use the sample API and write to its demo database. Use fictional/sample information only. The meeting example uses written sample statements and requires explicit consent in its sample flow.

For a larger real-world launch, add authentication and access controls, move saved data to a managed database, and review the service's privacy and security needs before using real company information.
