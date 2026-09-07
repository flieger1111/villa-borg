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


DEFAULT_BLOG_ID = "6165637049845407616"
SCOPES = ["https://www.googleapis.com/auth/blogger"]

HOME = Path.home()
TOKEN_FILE = HOME / "blogger_token.json"
STATE_DIR = HOME / "villa-borg-autopublish"


def load_credentials():
    if not TOKEN_FILE.exists():
        print("FEHLER: blogger_token.json wurde nicht gefunden.")
        sys.exit(1)

    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

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


def state_file(blog_id):
    return STATE_DIR / f".last_publish_{blog_id}.json"


def read_last_hash(blog_id):
    path = state_file(blog_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("hash")
    except Exception:
        return None


def save_state(blog_id, content_hash, result):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state = {
        "blog_id": blog_id,
        "hash": content_hash,
        "post_id": result.get("id"),
        "title": result.get("title"),
        "url": result.get("url"),
        "published_at": datetime.now().isoformat()
    }
    state_file(blog_id).write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def normalize_labels(labels):
    result = []
    seen = set()
    for label in labels:
        label = label.strip()
        if not label:
            continue
        key = label.casefold()
        if key not in seen:
            result.append(label)
            seen.add(key)
    return result


def infer_labels(title, content):
    text = f"{title}\n{content}".casefold()
    labels = ["Gallier", "Villa Borg"]

    if "perl" in text:
        labels.append("Perl aktuell")
    if "nennig" in text:
        labels.append("Nennig")
    if any(word in text for word in ("barriere", "inklusion", "mobilität für alle", "barrierefreier öpnv")):
        labels.append("Barrierefreiheit")
    if any(word in text for word in ("kommunalpolitik", "gemeinderat", "ortsrat", "ausschuss", "gemeinde perl")):
        labels.append("Kommunalpolitik")
    if "schulbus" in text:
        labels.append("Schulbus")
    if "schulweg" in text:
        labels.append("Schulweg")
    if "saarland" in text:
        labels.append("Saarland")

    return normalize_labels(labels)


def sync_labels_on_existing_post(service, blog_id, post, labels):
    desired = normalize_labels(labels)
    if not desired:
        return post

    existing = post.get("labels") or []
    merged = normalize_labels(existing + desired)
    if [x.casefold() for x in merged] == [x.casefold() for x in existing]:
        print("Blogger-Labels sind bereits vollständig vorhanden:", ", ".join(existing))
        return post

    updated = service.posts().patch(
        blogId=blog_id,
        postId=post.get("id"),
        body={"labels": merged}
    ).execute()
    print("Blogger-Labels aktualisiert:", ", ".join(updated.get("labels") or merged))
    return updated


def already_live_on_blogger(service, blog_id, title, content, labels=None):
    try:
        response = service.posts().list(
            blogId=blog_id,
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
            if labels:
                try:
                    post = sync_labels_on_existing_post(service, blog_id, post, labels)
                except Exception as exc:
                    print("WARNUNG: Labels des vorhandenen Beitrags konnten nicht aktualisiert werden:", exc)
            print("NICHT VERÖFFENTLICHT")
            print("Ein identischer öffentlicher Beitrag existiert bereits auf Blogger.")
            print("URL:", post.get("url"))
            return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True, help="Datei mit dem Titel")
    parser.add_argument("--html", required=True, help="HTML-Datei mit dem Beitrag")
    parser.add_argument("--blog-id", default=DEFAULT_BLOG_ID, help="Blogger-Blog-ID")
    parser.add_argument("--publish", action="store_true", help="Beitrag öffentlich veröffentlichen")
    parser.add_argument("--force", action="store_true", help="Doppel-Schutz umgehen")
    parser.add_argument("--labels", default="", help="Kommagetrennte Blogger-Labels")
    parser.add_argument("--auto-labels", action="store_true", help="Passende Blogger-Labels automatisch aus Titel und Inhalt ableiten")
    args = parser.parse_args()

    blog_id = str(args.blog_id).strip()
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

    labels = normalize_labels(args.labels.split(","))
    if args.auto_labels:
        labels = normalize_labels(labels + infer_labels(title, content))

    current_hash = make_hash(title, content)

    if args.publish and not args.force:
        if read_last_hash(blog_id) == current_hash:
            print("NICHT VERÖFFENTLICHT")
            print("Titel und Inhalt sind seit der letzten Veröffentlichung unverändert.")
            print("Doppelveröffentlichung wurde verhindert.")
            return

    creds = load_credentials()
    service = build("blogger", "v3", credentials=creds, cache_discovery=False)

    if args.publish and not args.force:
        if already_live_on_blogger(service, blog_id, title, content, labels):
            return

    post = {"title": title, "content": content}
    if labels:
        post["labels"] = labels

    result = service.posts().insert(
        blogId=blog_id,
        body=post,
        isDraft=not args.publish
    ).execute()

    print()
    print("Blogger-Übertragung erfolgreich")
    print("------------------------------")
    print("Blog-ID: ", blog_id)
    print("Titel:   ", result.get("title"))
    print("Post-ID: ", result.get("id"))
    print("Status:  ", result.get("status"))
    print("URL:     ", result.get("url"))
    if result.get("labels"):
        print("Labels:  ", ", ".join(result.get("labels")))

    if args.publish:
        if result.get("status") != "LIVE":
            print("FEHLER: Veröffentlichung war angefordert, Blogger meldet aber nicht LIVE.")
            sys.exit(1)
        save_state(blog_id, current_hash, result)
        print("ERGEBNIS: Beitrag wurde ÖFFENTLICH veröffentlicht.")
        print("Doppel-Schutz wurde aktualisiert.")
    else:
        print("ERGEBNIS: Beitrag wurde nur als ENTWURF gespeichert.")


if __name__ == "__main__":
    main()
