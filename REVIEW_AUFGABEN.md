# Review-Aufgaben für die Codebasis

Diese Datei sammelt konkrete Vorschläge aus einer kurzen Durchsicht der aktuellen Codebasis. Der Fokus liegt auf kleinen, gut abgrenzbaren Aufgaben, die unabhängig voneinander bearbeitet werden können.

## 1. Aufgabe zur Korrektur eines Tippfehlers

**Fundstelle:** `leukbach`, Abschnitt „Für villa-borg.com interne Suche-Funktionen oder Label-Recherche“.

**Problem:** Die Formulierung „interne Suche-Funktionen“ ist im Deutschen uneinheitlich und wirkt wie ein Tipp- oder Bindestrichfehler.

**Vorschlag:** In „interne Suchfunktionen“ oder „interne Suche und Label-Recherche“ umformulieren.

**Akzeptanzkriterium:** Die Überschrift verwendet eine konsistente deutsche Schreibweise ohne unnötigen Bindestrich.

## 2. Aufgabe zur Korrektur eines Programmierfehlers

**Fundstelle:** Repository-Struktur; aktuell gibt es nur die Datei `leukbach` ohne Dateiendung oder ausführbaren Anwendungscode.

**Problem:** Wenn diese Datei von Skripten, Generatoren oder statischen Website-Tools verarbeitet werden soll, ist der Dateityp nicht maschinenlesbar erkennbar. Das kann zu Programmierfehlern in automatisierten Verarbeitungsschritten führen, weil Tools häufig anhand der Endung entscheiden, ob ein Text als Markdown, Plaintext oder anderer Inhaltstyp behandelt wird.

**Vorschlag:** Die Datei in `leukbach.md` umbenennen oder ein Verarbeitungsmanifest ergänzen, das den Inhaltstyp eindeutig festlegt.

**Akzeptanzkriterium:** Automatisierte Tools können den Inhaltstyp eindeutig erkennen und die Datei ohne Sonderfalllogik verarbeiten.

## 3. Aufgabe zur Korrektur eines Codekommentars oder einer Dokumentations-Unstimmigkeit

**Fundstelle:** `leukbach`, Suchprompt „Leukbach Saarburg Zufluss der Saar Geographie Entstehung Quelle Perl Eft“ und der spätere Hintergrundsatz „Quelle bei Eft (Gemeinde Perl)“.

**Problem:** Die Begriffe „Quelle Perl Eft“ und „Quelle bei Eft (Gemeinde Perl)“ beschreiben vermutlich denselben Ort, sind aber unterschiedlich präzise. Dadurch kann bei Leserinnen, Lesern oder KI-Tools der Eindruck entstehen, Quelle und Gemeinde seien zwei getrennte Ortsangaben.

**Vorschlag:** Die Ortsangabe durchgehend als „Quelle bei Eft in der Gemeinde Perl“ formulieren.

**Akzeptanzkriterium:** Alle relevanten Stellen verwenden dieselbe präzise geografische Formulierung.

## 4. Aufgabe zur Verbesserung eines Tests

**Fundstelle:** Repository insgesamt; es sind derzeit keine Testdateien vorhanden.

**Problem:** Die vorhandene Prompt- und Recherchedatei enthält strukturierte Kategorien, aber es gibt keinen Test oder Check, der grundlegende Qualitätsregeln absichert.

**Vorschlag:** Einen einfachen Text-/Lint-Test ergänzen, der prüft, ob die Datei erwartete Abschnittsüberschriften enthält, keine doppelten Leerzeilen am Dateiende aufweist und zentrale Suchbegriffe wie „Leukbach“, „Villa Borg“ und „Saar“ weiterhin vorkommen.

**Akzeptanzkriterium:** Ein automatisierter Check schlägt fehl, wenn zentrale Abschnitte oder Pflichtbegriffe versehentlich entfernt werden.
