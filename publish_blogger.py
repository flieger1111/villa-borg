#!/usr/bin/env python3

from pathlib import Path
import argparse
import hashlib
import json
import sys
from datetime import datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build


BLOG_ID = "6165637049845407616"
SCOPES = ["https://www.googleapis.com/auth/blogger"]

HOME = Path.home()
TOKEN_FILE = HOME / "blogger_token.json"
STATE_FILE = HOME / "villa-borg-autopublish" / ".last_publish.json"


def load_credentials():
    if not TOKEN_FILE.exists():
        print("FEHLER: blogger_token.json wurde nicht gefunden.")
        sys.exit(1)

    creds = Credentials.from_authorized_user_file(
        str(TOKEN_FILE),
        SCOPES
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN_FILE.write_text(creds.to_json())

    if not creds.valid:
        print("FEHLER: Blogger-Anmeldung ist nicht gültig.")
        sys.exit(1)

    return creds


def make_hash(title, content):
    data = (title + "\n" + content).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def read_last_hash():
    if not STATE_FILE.exists():
        return None

    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        return data.get("hash")
    except Exception:
        return None


def save_state(content_hash, result):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state = {
        "hash": content_hash,
        "post_id": result.get("id"),
        "title": result.get("title"),
        "url": result.get("url"),
        "published_at": datetime.now().isoformat()
    }

    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def already_live_on_blogger(service, title, content):
    """Verhindert Doppelveröffentlichungen auch auf frischen GitHub-Runnern."""
    try:
        response = service.posts().list(
            blogId=BLOG_ID,
            status=["LIVE"],
            maxResults=20,
            fetchBodies=True
        ).execute()
    except Exception as exc:
        print("WARNUNG: Online-Doppelprüfung nicht möglich:", exc)
        return False

    target_hash = make_hash(title.strip(), content.strip())
    for post in response.get("items", []):
        post_title = (post.get("title") or "").strip()
        post_content = (post.get("content") or "").strip()
        if make_hash(post_title, post_content) == target_hash:
            print("NICHT VERÖFFENTLICHT")
            print("Ein identischer öffentlicher Beitrag existiert bereits auf Blogger.")
            print("URL:", post.get("url"))
            return True

    return False


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--title",
        required=True,
        help="Datei mit dem Titel"
    )

    parser.add_argument(
        "--html",
        required=True,
        help="HTML-Datei mit dem Beitrag"
    )

    parser.add_argument(
        "--publish",
        action="store_true",
        help="Beitrag öffentlich veröffentlichen"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Doppel-Schutz umgehen"
    )

    args = parser.parse_args()

    title_file = Path(args.title).expanduser()
    html_file = Path(args.html).expanduser()

    if not title_file.exists():
        print("FEHLER: Titeldatei fehlt:", title_file)
        sys.exit(1)

    if not html_file.exists():
        print("FEHLER: HTML-Datei fehlt:", html_file)
        sys.exit(1)

    title = title_file.read_text(encoding="utf-8").strip()
    content = html_file.read_text(encoding="utf-8").strip()

    if not title:
        print("FEHLER: Titel ist leer.")
        sys.exit(1)

    if not content:
        print("FEHLER: Beitrag ist leer.")
        sys.exit(1)

    current_hash = make_hash(title, content)

    # Lokaler Doppel-Schutz, falls die Statusdatei vorhanden ist.
    if args.publish and not args.force:
        previous_hash = read_last_hash()

        if previous_hash == current_hash:
            print("NICHT VERÖFFENTLICHT")
            print("Titel und Inhalt sind seit der letzten Veröffentlichung unverändert.")
            print("Doppelveröffentlichung wurde verhindert.")
            return

    creds = load_credentials()

    service = build(
        "blogger",
        "v3",
        credentials=creds,
        cache_discovery=False
    )

    # GitHub-Runner sind bei jedem Lauf frisch. Deshalb zusätzlich online prüfen.
    if args.publish and not args.force:
        if already_live_on_blogger(service, title, content):
            return

    post = {
        "title": title,
        "content": content
    }

    result = service.posts().insert(
        blogId=BLOG_ID,
        body=post,
        isDraft=not args.publish
    ).execute()

    print()
    print("Blogger-Übertragung erfolgreich")
    print("------------------------------")
    print("Titel:   ", result.get("title"))
    print("Post-ID: ", result.get("id"))
    print("Status:  ", result.get("status"))
    print("URL:     ", result.get("url"))

    if args.publish:
        if result.get("status") != "LIVE":
            print("FEHLER: Veröffentlichung war angefordert, Blogger meldet aber nicht LIVE.")
            sys.exit(1)
        save_state(current_hash, result)
        print("ERGEBNIS: Beitrag wurde ÖFFENTLICH veröffentlicht.")
        print("Doppel-Schutz wurde aktualisiert.")
    else:
        print("ERGEBNIS: Beitrag wurde nur als ENTWURF gespeichert.")


if __name__ == "__main__":
    main()
