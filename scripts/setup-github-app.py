#!/usr/bin/env python3
"""
Creates a GitHub App using the manifest flow.
Uses local `gh` CLI auth for API calls.
"""

import json
import subprocess
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

APP_NAME = "student-benefits-hub-bot"
HOMEPAGE = "https://agentivo.github.io/student-benefits-hub/"
PORT = 3456

MANIFEST = {
    "name": APP_NAME,
    "url": HOMEPAGE,
    "hook_attributes": {"active": False},
    "public": False,
    "default_permissions": {
        "contents": "write",
        "issues": "write",
        "pull_requests": "write",
        "models": "read"
    },
    "default_events": []
}


def gh_api(endpoint, method="GET", data=None):
    """Call GitHub API using gh CLI auth."""
    cmd = ["gh", "api", endpoint, "-X", method]
    if data:
        cmd.extend(["-f", f"data={json.dumps(data)}"])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(result.stderr)
    return json.loads(result.stdout) if result.stdout else None


def set_secret(name, value):
    """Set a repository secret using gh CLI."""
    subprocess.run(
        ["gh", "secret", "set", name],
        input=value,
        text=True,
        check=True
    )


class CallbackHandler(BaseHTTPRequestHandler):
    app_data = None

    def log_message(self, format, *args):
        pass  # Suppress logs

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        code = query.get("code", [None])[0]

        if not code:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing code")
            return

        print("Exchanging code for credentials...")

        # Exchange code for app credentials using gh api
        try:
            result = subprocess.run(
                ["gh", "api", f"/app-manifests/{code}/conversions", "-X", "POST"],
                capture_output=True,
                text=True,
                check=True
            )
            CallbackHandler.app_data = json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"Failed to create app")
            return

        app = CallbackHandler.app_data
        print(f"\nApp created: {app['name']} (ID: {app['id']})")

        # Add secrets
        print("Adding secrets to repository...")
        try:
            set_secret("APP_ID", str(app["id"]))
            set_secret("APP_PRIVATE_KEY", app["pem"])
            print("Secrets added!")
        except Exception as e:
            print(f"Could not add secrets: {e}")
            print(f"\nManually add these secrets:")
            print(f"  APP_ID: {app['id']}")
            print(f"  APP_PRIVATE_KEY: (saved to app-private-key.pem)")
            with open("app-private-key.pem", "w") as f:
                f.write(app["pem"])

        print(f"\nInstall the app: https://github.com/settings/apps/{app['slug']}/installations")

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(f"""
            <html><body style="font-family:system-ui;text-align:center;padding:40px">
            <h1>GitHub App Created</h1>
            <p><strong>{app['name']}</strong> (ID: {app['id']})</p>
            <p>Secrets added to repository.</p>
            <p><a href="https://github.com/settings/apps/{app['slug']}/installations">Install the app</a></p>
            </body></html>
        """.encode())


def main():
    print(f"Creating GitHub App: {APP_NAME}\n")

    manifest = {**MANIFEST, "redirect_url": f"http://localhost:{PORT}"}
    encoded = json.dumps(manifest).replace(" ", "")
    url = f"https://github.com/settings/apps/new?manifest={encoded}"

    print("Opening browser - click 'Create GitHub App'\n")
    webbrowser.open(url)

    server = HTTPServer(("localhost", PORT), CallbackHandler)
    server.handle_request()  # Handle single request then exit

    if CallbackHandler.app_data:
        print("\nDone! Run 'make test-issue' to test the workflow.")


if __name__ == "__main__":
    main()
