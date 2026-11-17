"""One-time, reversible maintenance of the reviewed Villa Borg posts."""
import html
import re
from datetime import datetime
from publish_blogger import build, load_credentials, list_recent_live_posts, DEFAULT_BLOG_ID

MARKER = '<!-- aktualitaet-2026-11-11 -->'
FUEL_TITLES = {
    "Luxemburg: Super 95 wird am 7. November 5,1 Cent günstiger",
    "Luxemburg: Super 98 und Diesel werden am 6. November günstiger",
    "Luxemburg: Benzin und Diesel seit 4. November deutlich günstiger",
}
DUP_TITLE = "Bahnhof Besch: Beide Bahnsteige laut DB stufenfrei – Einstieg bleibt offen"
BARRIER_FREE_PATH = "/2026/10/barrierefreiheit-gemeinde-perl.html"
BARRIER_FREE_TITLE = "Barrierefreiheit in Perl: Bahnhöfe, Wege und Gebäude"


def normalized(content):
    content = re.sub(r"<!--.*?-->", "", content, flags=re.S)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", content)).split())


def notice(post):
    title = post.get("title", "")
    if title in FUEL_TITLES:
        return "Preisarchiv: Die folgenden Preise gelten für den im Beitrag genannten Tag. Sie wurden nicht als heutige Tankpreise bestätigt. Bitte prüfen Sie vor der Fahrt die aktuellen Preise."
    if title == "Schengen: CR152 bis Sonntag 17 Uhr gesperrt – Buslinie L06 wird umgeleitet":
        return "Archivhinweis vom 11. November 2026: Der angekündigte Zeitraum endete am 8. November 2026 um 17 Uhr. Die damals verlinkte Mobiliteit-Verkehrsmeldung ist nicht mehr abrufbar. Eine aktuelle Sperrung oder erfolgte Freigabe wird mit diesem Archivbeitrag nicht bestätigt. Bitte prüfen Sie Ihre Verbindung bei Mobiliteit.lu."
    if title == "Martinsumzüge in Perl: Buslinie 260 lässt Haltestellen aus":
        return "Einordnung vom 11. November 2026: Die im Beitrag genannten Umzüge vom 6. und 7. November sind vergangen. Der ursprüngliche Streckenhinweis nennt einen Zeitraum bis 14. November; er bestätigt keine durchgehende Sperrung. Prüfen Sie die konkrete Fahrt bei der VMW."
    return None



def improve_waldkindergarten_post(service):
    """Update the existing article in place, preserving its URL and published date."""
    from googleapiclient.errors import HttpError
    marker = '<!-- seo-waldkindergarten-2026-11-17 -->'
    post = None
    for path in (
        "/2026/10/ortsrat-borg-waldkindergarten-neu-auf.html",
        "/2026/11/ortsrat-borg-waldkindergarten-neu-auf.html",
    ):
        try:
            post = service.posts().getByPath(
                blogId=DEFAULT_BLOG_ID, path=path
            ).execute()
            break
        except HttpError as exc:
            if exc.resp.status != 404:
                raise
    if post is None:
        raise RuntimeError("Waldkindergarten article not found; no replacement created.")
    content = post.get("content", "")
    if marker in content:
        print("SEO BEREITS AKTUELL:", post["url"])
        return
    intro = (
        marker
        + '<section aria-label="Aktualisierung zum Waldkindergarten Borg">'
        + '<h2>Waldkindergarten Borg: Planungsstand vom 17. November 2026</h2>'
        + '<p>Für den Waldkindergarten Borg hat der Gemeinderat Perl am 26. Oktober 2026 '
        + 'die Abwägung und den Entwurf zur öffentlichen Auslegung einstimmig gebilligt. '
        + 'Mosella 46/2026 veröffentlicht diesen Beschluss. Er ist ein Schritt im '
        + 'Planverfahren und bestätigt weder einen Baubeginn noch einen Eröffnungstermin.</p>'
        + '<p>Der ursprüngliche Bericht unten dokumentiert die ergänzte Tagesordnung '
        + 'des Ortsrates Borg für den 5. Oktober 2026. Eine Tagesordnung und der spätere '
        + 'Gemeinderatsbeschluss sind unterschiedliche Nachweise; das gesonderte Ergebnis '
        + 'der Ortsratssitzung wird damit nicht bestätigt.</p>'
        + '<p><a href="https://ol.wittich.de/titel/158/ausgabe/46/2026/artikel/00000000000055698171-OL-158-2026-46-46-0">'
        + 'Amtliche Veröffentlichung der Gemeinderatsbeschlüsse</a> · '
        + '<a href="https://magazin.villa-borg.com/gemeinde-perl/#waldkindergarten-borg">'
        + 'Waldkindergarten Borg und aktuelle Kommunalpolitik in Perl</a> · '
        + '<a href="https://magazin.villa-borg.com/heimatgeschichte/borg/">Geschichte des Ortsteils Borg</a></p>'
        + '</section>\n'
    )
    labels = list(dict.fromkeys(post.get("labels", []) + ["Gemeinde Perl", "Borg", "Waldkindergarten", "Kommunalpolitik"]))
    expected_title = "Waldkindergarten Borg: Planung und Beschlüsse im Überblick"
    result = service.posts().patch(
        blogId=DEFAULT_BLOG_ID,
        postId=post["id"],
        body={"title": expected_title, "content": intro + content, "labels": labels}
    ).execute()
    verified = service.posts().get(blogId=DEFAULT_BLOG_ID, postId=post["id"]).execute()
    if verified.get("title") != expected_title or marker not in verified.get("content", ""):
        raise RuntimeError("SEO update verification failed")
    if verified.get("url") != post.get("url") or verified.get("published") != post.get("published"):
        raise RuntimeError("Unexpected URL or publication-date change")
    print("SEO GEPRUEFT; URL UND DATUM ERHALTEN:", verified["url"])


def main():
    service = build("blogger", "v3", credentials=load_credentials(), cache_discovery=False)
    improve_waldkindergarten_post(service)
    posts = list_recent_live_posts(service, DEFAULT_BLOG_ID)
    for post in posts:
        if (post.get("url") or "").endswith(BARRIER_FREE_PATH) and post.get("title") != BARRIER_FREE_TITLE:
            service.posts().patch(blogId=DEFAULT_BLOG_ID, postId=post["id"], body={"title": BARRIER_FREE_TITLE}).execute()
            print("BARRIEREFREIHEITS-TITEL AKTUALISIERT:", post.get("url"))
        message = notice(post)
        content = post.get("content", "")
        if not message or MARKER in content:
            continue
        body = MARKER + '<p><strong>' + html.escape(message) + '</strong></p>\n' + content
        service.posts().patch(blogId=DEFAULT_BLOG_ID, postId=post["id"], body={"content": body}).execute()
        print("ARCHIVHINWEIS:", post.get("url"))
    duplicates = sorted(
        [p for p in posts if p.get("title", "") == DUP_TITLE],
        key=lambda p: (datetime.fromisoformat(p["published"].replace("Z", "+00:00")), p["id"]),
    )
    if duplicates:
        original = duplicates[0]
        for duplicate in duplicates[1:]:
            if normalized(duplicate.get("content", "")) != normalized(original.get("content", "")):
                print("NICHT IDENTISCH; UNVERÄNDERT:", duplicate.get("url"))
                continue
            service.posts().revert(blogId=DEFAULT_BLOG_ID, postId=duplicate["id"]).execute()
            print("DUPLIKAT ALS ENTWURF GESICHERT:", duplicate.get("url"))
        print("BEIBEHALTENE ADRESSE:", original.get("url"))


if __name__ == "__main__":
    main()
