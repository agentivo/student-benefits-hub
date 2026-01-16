#!/usr/bin/env python3
"""
Creates a GitHub App via manifest flow.
"""

import json
import subprocess
import webbrowser
import tempfile
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

APP_NAME = "student-benefits-hub-models"
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


def exchange_code(code):
    """Exchange the code for app credentials."""
    print("Exchanging code for app credentials...")

    result = subprocess.run(
        ["gh", "api", f"/app-manifests/{code}/conversions", "-X", "POST"],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None

    app = json.loads(result.stdout)
    print(f"\nApp created: {app['name']} (ID: {app['id']})")

    print("Saving APP_ID and APP_PRIVATE_KEY secrets...")
    subprocess.run(["gh", "secret", "set", "APP_ID"], input=str(app["id"]), text=True, check=True)
    subprocess.run(["gh", "secret", "set", "APP_PRIVATE_KEY"], input=app["pem"], text=True, check=True)

    print(f"\nDone! Install the app: https://github.com/settings/apps/{app['slug']}/installations")
    return app


class CallbackHandler(BaseHTTPRequestHandler):
    app_data = None

    def log_message(self, *args):
        pass

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)
        code = query.get("code", [None])[0]

        if not code:
            self.send_error(400, "Missing code")
            return

        app = exchange_code(code)
        CallbackHandler.app_data = app

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        if app:
            install_url = f"https://github.com/settings/apps/{app['slug']}/installations"
            self.wfile.write(f"""
                <html><body style="font-family:system-ui;text-align:center;padding:40px">
                <h1>Done</h1>
                <p>App: <strong>{app['name']}</strong> (ID: {app['id']})</p>
                <p>Secrets added to repo.</p>
                <p><a href="{install_url}">Install the app</a></p>
                </body></html>
            """.encode())
        else:
            self.wfile.write(b"<html><body><h1>Failed</h1></body></html>")


def main():
    print(f"Creating GitHub App: {APP_NAME}\n")

    print("Configuration:")
    print(f"  Name:     {APP_NAME}")
    print(f"  Homepage: {HOMEPAGE}")
    print(f"  Webhook:  Disabled")
    print()
    print("Permissions:")
    for perm, level in MANIFEST["default_permissions"].items():
        print(f"  {perm}: {level}")
    print()
    print(f"Callback:   http://localhost:{PORT}")
    print()

    input("Press Enter to open browser...")

    # Create HTML form that POSTs the manifest
    manifest = {**MANIFEST, "redirect_url": f"http://localhost:{PORT}"}
    manifest_json = json.dumps(manifest).replace('"', '&quot;')

    html = f"""<!DOCTYPE html>
<html>
<body>
<form id="form" action="https://github.com/settings/apps/new" method="post">
  <input type="hidden" name="manifest" value="{manifest_json}">
</form>
<script>document.getElementById('form').submit();</script>
</body>
</html>"""

    # Write to temp file and open in browser
    fd, path = tempfile.mkstemp(suffix='.html')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(html)

        webbrowser.open(f'file://{path}')

        print(f"\nWaiting for callback on http://localhost:{PORT}")
        print("After clicking 'Create GitHub App', your browser will redirect here.\n")
        print("If redirect fails, paste the URL from your browser here:\n")

        # Start server
        import threading
        server = HTTPServer(("localhost", PORT), CallbackHandler)
        server.timeout = 300

        def serve():
            server.handle_request()

        thread = threading.Thread(target=serve)
        thread.daemon = True
        thread.start()

        # Wait for callback or manual input
        while thread.is_alive():
            try:
                import select
                import sys
                if select.select([sys.stdin], [], [], 0.5)[0]:
                    manual_url = input().strip()
                    if "code=" in manual_url:
                        code = parse_qs(urlparse(manual_url).query).get("code", [None])[0]
                        if code:
                            exchange_code(code)
                            return
            except:
                pass

        if not CallbackHandler.app_data:
            print("\nNo callback received. Manual setup:")
            print("1. Go to https://github.com/settings/apps")
            print("2. Click your app → copy App ID")
            print("3. Generate private key")
            print("4. Run:")
            print("   gh secret set APP_ID")
            print("   gh secret set APP_PRIVATE_KEY < private-key.pem")

    finally:
        os.unlink(path)


if __name__ == "__main__":
    main()
