#!/usr/bin/env python3
from pathlib import Path
import sys

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/blogger"]
TOKEN_FILE = Path.home() / "blogger_token.json"

if not TOKEN_FILE.exists():
    print("FEHLER: ~/blogger_token.json wurde nicht gefunden.")
    sys.exit(1)

creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")

if not creds.valid:
    print("FEHLER: Blogger-Anmeldung ist nicht gültig.")
    sys.exit(1)

service = build("blogger", "v3", credentials=creds, cache_discovery=False)
response = service.blogs().listByUser(userId="self").execute()
blogs = response.get("items", [])

if not blogs:
    print("Keine Blogger-Blogs gefunden.")
    sys.exit(0)

print("Gefundene Blogger-Blogs:\n")
for blog in blogs:
    print(f"Name: {blog.get('name')}")
    print(f"Blog-ID: {blog.get('id')}")
    print(f"URL: {blog.get('url')}")
    print("-")
