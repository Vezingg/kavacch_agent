"""
Kalash Agent Config Updater
----------------------------
Web form to update WhatsApp Access Token (Secret Manager) and
Cloud Run environment variables for the kalash-agent service.
"""

import html
import logging
import os
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from google.auth import default as gauth_default
from google.auth.transport.requests import Request as GRequest
from google.cloud import secretmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kalash-updater")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "kavacch-agent-lite-491904")
REGION = os.environ.get("GCP_REGION", "asia-south1")
SERVICE_NAME = os.environ.get("TARGET_SERVICE", "kalash-agent")

# These are fixed — no text fields exposed in the form
META_APP_SECRET = os.environ.get("META_APP_SECRET_VALUE", "9395ee31e52c6738e68f180a873b6ea7")
DEFAULT_FACTORY_WHATSAPP = os.environ.get("DEFAULT_FACTORY_WHATSAPP", "919925532982")

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Kalash Agent Config Updater")

# ---------------------------------------------------------------------------
# HTML — Index Page
# ---------------------------------------------------------------------------
_INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Kalash Agent Updater</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
     background:#f0f2f5;min-height:100vh;display:flex;align-items:center;
     justify-content:center;padding:24px}
.card{background:#fff;border-radius:14px;box-shadow:0 4px 28px rgba(0,0,0,.10);
      padding:40px 44px;max-width:540px;width:100%}
h1{font-size:22px;font-weight:700;color:#1a1a2e;margin-bottom:6px}
.sub{color:#6b7280;font-size:13.5px;margin-bottom:32px;line-height:1.5}
.field{margin-bottom:20px}
label{display:block;font-size:13px;font-weight:600;color:#374151;margin-bottom:6px}
.req{color:#ef4444}
.opt{color:#9ca3af;font-weight:400;font-size:12px;margin-left:4px}
input[type=text],textarea{width:100%;padding:10px 14px;border:1.5px solid #d1d5db;
  border-radius:8px;font-size:14px;font-family:inherit;outline:none;
  transition:border .2s,box-shadow .2s;color:#111}
input[type=text]:focus,textarea:focus{border-color:#6366f1;
  box-shadow:0 0 0 3px rgba(99,102,241,.12)}
textarea{resize:vertical;min-height:92px;
  font-family:'SFMono-Regular',Consolas,monospace;font-size:12.5px}
.hint{font-size:12px;color:#9ca3af;margin-top:5px;line-height:1.5}
hr{border:none;border-top:1px solid #f0f2f5;margin:24px 0}
.fixed-section p{font-size:12px;color:#9ca3af;margin-bottom:10px}
.fixed-row{display:flex;align-items:center;gap:9px;padding:8px 0;
  font-size:13px;color:#6b7280;border-bottom:1px solid #f9fafb}
.fixed-row:last-child{border-bottom:none}
.dot{width:8px;height:8px;border-radius:50%;background:#10b981;flex-shrink:0}
.chip{background:#f3f4f6;color:#374151;border-radius:5px;font-size:12px;
  padding:2px 9px;font-weight:600;margin-left:auto}
button{width:100%;padding:12px;background:#6366f1;color:#fff;border:none;
  border-radius:9px;font-size:15px;font-weight:600;cursor:pointer;
  transition:background .15s;margin-top:12px}
button:hover{background:#4f46e5}
button:disabled{background:#a5b4fc;cursor:not-allowed}
</style>
</head>
<body>
<div class="card">
  <h1>&#128273; Kalash Agent Updater</h1>
  <p class="sub">Update deployment config for <strong>kalash-agent</strong> on Cloud Run.
     <br/>Token is added to Secret Manager; other values update the service env vars.</p>

  <form method="POST" action="/update"
        onsubmit="this.querySelector('button').disabled=true;
                  this.querySelector('button').textContent='Deploying\u2026'">

    <div class="field">
      <label>WhatsApp Access Token <span class="req">*</span></label>
      <textarea name="whatsapp_token" required
        placeholder="EAALPx6Znq\u2026 (paste full token)"></textarea>
      <div class="hint">Copy from Meta Business Manager &rarr; WhatsApp &rarr; API Setup</div>
    </div>

    <div class="field">
      <label>Factory WhatsApp Number <span class="opt">(optional)</span></label>
      <input type="text" name="factory_number" placeholder="919925532982"/>
      <div class="hint">Country code + number, no +.
        Leave blank to keep current: <strong>919925532982</strong></div>
    </div>

    <div class="field">
      <label>Resolution Limit <span class="opt">(optional)</span></label>
      <input type="text" name="resolution_limit" placeholder="500"/>
      <div class="hint">Max agent resolutions per billing cycle. Default: <strong>500</strong></div>
    </div>

    <div class="field">
      <label>Referral Credits <span class="opt">(optional)</span></label>
      <input type="text" name="referral_credits" placeholder="0"/>
      <div class="hint">Bonus resolutions granted per referral. Default: <strong>0</strong></div>
    </div>

    <hr/>

    <div class="fixed-section">
      <p>Fixed values applied automatically on every update:</p>
      <div class="fixed-row">
        <span class="dot"></span>
        Meta App Secret
        <span class="chip">uses stored value</span>
      </div>
      <div class="fixed-row">
        <span class="dot"></span>
        Automation Rate
        <span class="chip">100</span>
      </div>
    </div>

    <hr/>
    <button type="submit">&#128640; Deploy Update</button>
  </form>
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# HTML — Result Page
# ---------------------------------------------------------------------------
def _result_page(results: list[tuple[str, str, str]]) -> str:
    """Build the result page. results = [(icon, title, detail)]"""
    rows = ""
    for icon, title, detail in results:
        color = "#10b981" if icon == "✅" else "#ef4444"
        safe_detail = html.escape(str(detail))
        rows += f"""
        <div style="display:flex;gap:12px;padding:14px 16px;border-radius:9px;
                    background:#f9fafb;border:1px solid #e5e7eb;margin-bottom:12px">
          <span style="font-size:20px;flex-shrink:0">{icon}</span>
          <div>
            <div style="font-weight:600;color:{color};font-size:14px">{html.escape(title)}</div>
            <div style="font-size:12.5px;color:#6b7280;margin-top:4px;
                        word-break:break-all;line-height:1.5">{safe_detail}</div>
          </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Update Result &mdash; Kalash Agent</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
     background:#f0f2f5;min-height:100vh;display:flex;align-items:center;
     justify-content:center;padding:24px}}
.card{{background:#fff;border-radius:14px;box-shadow:0 4px 28px rgba(0,0,0,.10);
      padding:40px 44px;max-width:540px;width:100%}}
h1{{font-size:20px;font-weight:700;color:#1a1a2e;margin-bottom:6px}}
.sub{{color:#6b7280;font-size:13px;margin-bottom:24px;line-height:1.5}}
a{{display:inline-block;margin-top:18px;color:#6366f1;font-size:14px;
   text-decoration:none;font-weight:500}}
a:hover{{text-decoration:underline}}
</style>
</head>
<body>
<div class="card">
  <h1>Deployment Result</h1>
  <p class="sub">Update submitted for <strong>kalash-agent</strong></p>
  {rows}
  <a href="/">&larr; Submit another update</a>
</div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# GCP Helpers
# ---------------------------------------------------------------------------
def _get_credentials():
    """Return valid GCP Application Default Credentials."""
    creds, _ = gauth_default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    creds.refresh(GRequest())
    return creds


def _add_secret_version(token: str) -> tuple[bool, str]:
    """Add a new version of whatsapp_access_token in Secret Manager."""
    try:
        client = secretmanager.SecretManagerServiceClient()
        parent = f"projects/{PROJECT_ID}/secrets/whatsapp_access_token"
        response = client.add_secret_version(
            request={
                "parent": parent,
                "payload": {"data": token.strip().encode("utf-8")},
            }
        )
        version = response.name.split("/")[-1]
        return True, f"New secret version {version} added to whatsapp_access_token"
    except Exception as exc:
        logger.error("Secret Manager error: %s", exc)
        return False, str(exc)


async def _update_cloud_run_env(env_updates: dict) -> tuple[bool, str]:
    """Patch Cloud Run service env vars via the v2 REST API.

    Preserves secret-referenced env vars; updates only plain-value ones.
    """
    try:
        creds = _get_credentials()
        base_url = (
            f"https://run.googleapis.com/v2/projects/{PROJECT_ID}"
            f"/locations/{REGION}/services/{SERVICE_NAME}"
        )
        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json",
        }

        # Fetch current service definition
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.get(base_url, headers=headers)
            resp.raise_for_status()
            service = resp.json()

        # Rebuild env var list for each container:
        #   - Drop WHATSAPP_ACCESS_TOKEN (we re-add it with version:latest so
        #     Cloud Run re-resolves to the secret version we just added)
        #   - Keep all other secret-ref env vars unchanged
        #   - Keep plain vars whose names are NOT being updated
        #   - Re-add / add the updated plain vars
        for container in service.get("template", {}).get("containers", []):
            current = container.get("env", [])
            new_env = []
            for e in current:
                name = e.get("name")
                if name == "WHATSAPP_ACCESS_TOKEN":
                    continue  # re-added below with version:latest
                if "valueSource" in e:
                    new_env.append(e)  # preserve other secret refs
                elif name not in env_updates:
                    new_env.append(e)  # preserve plain vars not being updated
            # Updated plain env vars
            new_env += [{"name": k, "value": v} for k, v in env_updates.items()]
            # Force WHATSAPP_ACCESS_TOKEN to resolve to the newest secret version
            new_env.append({
                "name": "WHATSAPP_ACCESS_TOKEN",
                "valueSource": {
                    "secretKeyRef": {
                        "secret": "whatsapp_access_token",
                        "version": "latest",
                    }
                },
            })
            container["env"] = new_env

        # Stamp a unique timestamp annotation so Cloud Run always creates a new
        # revision — without this, if `version: latest` was already the stored
        # value, Cloud Run sees no diff and silently skips the new revision.
        template = service.setdefault("template", {})
        template.setdefault("annotations", {})
        template["annotations"]["run.googleapis.com/description"] = (
            datetime.now(timezone.utc).isoformat()
        )

        # PATCH covering both containers and the annotation we just added
        patch_url = f"{base_url}?updateMask=template.containers,template.annotations"
        async with httpx.AsyncClient(timeout=120) as client:
            patch_resp = await client.patch(patch_url, headers=headers, json=service)
            patch_resp.raise_for_status()

        updated_names = ", ".join(env_updates.keys())
        return True, f"Updated env vars: {updated_names}. Changes live in ~30s."

    except httpx.HTTPStatusError as exc:
        body = exc.response.text
        logger.error("Cloud Run API %s: %s", exc.response.status_code, body)
        return False, f"HTTP {exc.response.status_code}: {body[:400]}"
    except Exception as exc:
        logger.error("Cloud Run update error: %s", exc)
        return False, str(exc)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=_INDEX_HTML)


@app.post("/update", response_class=HTMLResponse)
async def update(
    whatsapp_token: str = Form(...),
    factory_number: str = Form(""),
    resolution_limit: str = Form(""),
    referral_credits: str = Form(""),
):
    results: list[tuple[str, str, str]] = []

    # 1. Update WhatsApp token in Secret Manager
    ok, msg = _add_secret_version(whatsapp_token)
    results.append(("✅" if ok else "❌", "WhatsApp Token — Secret Manager", msg))

    # 2. Update Cloud Run env vars
    env_vars = {
        "FACTORY_WHATSAPP": factory_number.strip() or DEFAULT_FACTORY_WHATSAPP,
        "RESOLUTION_LIMIT": resolution_limit.strip() or "500",
        "REFERRAL_CREDITS": referral_credits.strip() or "0",
        "AUTOMATION_RATE": "100",
        "META_APP_SECRET": META_APP_SECRET,
    }
    ok, msg = await _update_cloud_run_env(env_vars)
    results.append(("✅" if ok else "❌", "Cloud Run Env Vars — kalash-agent", msg))

    return HTMLResponse(content=_result_page(results))


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "kalash-updater"}
