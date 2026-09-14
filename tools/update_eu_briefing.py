#!/usr/bin/env python3
"""Replace the content of the existing EU briefing Google Doc safely."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/blogger",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/documents",
]


def document_text(document: dict) -> str:
    parts: list[str] = []
    for item in document.get("body", {}).get("content", []):
        paragraph = item.get("paragraph")
        if not paragraph:
            continue
        for element in paragraph.get("elements", []):
            parts.append(element.get("textRun", {}).get("content", ""))
    return "".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-id", required=True)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument(
        "--token",
        type=Path,
        default=Path.home() / "blogger_token.json",
    )
    args = parser.parse_args()

    wanted = args.input.read_text(encoding="utf-8").strip() + "\n"
    if len(wanted.strip()) < 200:
        raise SystemExit("Abbruch: Das Briefing ist unerwartet kurz.")

    credentials = Credentials.from_authorized_user_file(str(args.token), SCOPES)
    service = build("docs", "v1", credentials=credentials, cache_discovery=False)
    document = service.documents().get(documentId=args.document_id).execute()
    current = document_text(document)

    if current.strip() == wanted.strip():
        print(f"UNVERÄNDERT: {document.get('title', args.document_id)}")
        return 0

    end_index = document["body"]["content"][-1]["endIndex"]
    requests: list[dict] = []
    if end_index > 2:
        requests.append(
            {
                "deleteContentRange": {
                    "range": {"startIndex": 1, "endIndex": end_index - 1}
                }
            }
        )
    requests.append({"insertText": {"location": {"index": 1}, "text": wanted}})

    service.documents().batchUpdate(
        documentId=args.document_id,
        body={"requests": requests},
    ).execute()

    verified = service.documents().get(documentId=args.document_id).execute()
    if document_text(verified).strip() != wanted.strip():
        raise SystemExit("Fehler: Die Kontrolle nach dem Schreiben ist fehlgeschlagen.")

    print(f"AKTUALISIERT: {verified.get('title', args.document_id)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HttpError as error:
        raise SystemExit(f"Google-API-Fehler: {error}") from error
