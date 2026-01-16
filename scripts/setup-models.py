#!/usr/bin/env python3
"""
Sets up GitHub Models access using existing gh CLI auth.
No GitHub App needed - just uses your gh token.
"""

import subprocess


def main():
    print("Setting up GitHub Models access...\n")

    # Get current gh token
    result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Error: Not logged in to gh CLI. Run 'gh auth login' first.")
        return

    token = result.stdout.strip()

    # Test if token works with Models
    print("Testing GitHub Models access...")
    test = subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
         "-H", f"Authorization: Bearer {token}",
         "-H", "Content-Type: application/json",
         "https://models.inference.ai.azure.com/chat/completions",
         "-d", '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"hi"}]}'],
        capture_output=True, text=True
    )

    if test.stdout.strip() != "200":
        print("Error: Your GitHub account doesn't have GitHub Models access.")
        print("Enable it at: https://github.com/marketplace/models")
        return

    print("GitHub Models access confirmed!\n")

    # Add token as secret
    print("Adding token to repository secrets...")
    subprocess.run(
        ["gh", "secret", "set", "GH_MODELS_TOKEN"],
        input=token,
        text=True,
        check=True
    )

    print("\nDone! GH_MODELS_TOKEN secret added.")
    print("The workflows will now use GitHub Models for AI processing.")


if __name__ == "__main__":
    main()
