# CLAUDE.md

Hinweise für Claude Code zur Arbeit in diesem Repository.

## Projekt

**Finanzverwaltung**: ein Programm, um alle Konten und Bargeldreserven zu verwalten und Verwendungszwecken zuzuordnen.

Das Projekt steht noch am Anfang; Architektur, Datenmodell und Technologien werden gerade geplant. Die `.gitignore` ist auf Python ausgelegt.

## Kommunikation

- Mit dem Nutzer wird Deutsch gesprochen.
- **Alles im Repository ist auf Englisch:** Bezeichner, Code, Kommentare, Docstrings, Commit-Nachrichten, Branchnamen und Dokumentation im Code.
- Vor größeren Änderungen erst planen und abstimmen, dann umsetzen.

## Ordnerstruktur

- `src/`: der gesamte Quellcode des Projekts.
- `tests/`: alle Tests (pytest).
- `.github/`: CI-Workflow und Vorlage für Pull Requests.
- `data/`: lokale Daten des Programms. Der Inhalt ist per `.gitignore` ausgeschlossen, nur `data/.gitkeep` ist versioniert. Hier liegen persönliche Finanzdaten: **niemals committen** und keine echten Daten in Code, Tests oder Beispielen verwenden.

## Entwicklungsumgebung

- Python 3.12 in einer virtuellen Umgebung unter `.venv`.
- Konfiguration und direkte Abhängigkeiten stehen in `pyproject.toml`; Entwicklerwerkzeuge im Extra `dev`.
- Feste Versionen stehen in `requirements-dev.txt`, erzeugt mit pip-tools. Diese Datei nie von Hand bearbeiten.
- Umgebung einrichten bzw. auf den Lock-Stand bringen: `.venv/bin/pip-sync requirements-dev.txt`
- Nach Änderungen an den Abhängigkeiten in `pyproject.toml` die Lock-Datei neu erzeugen:
  `.venv/bin/pip-compile --extra dev --strip-extras --output-file requirements-dev.txt pyproject.toml`
- pre-commit ist installiert und führt ruff und mypy bei jedem Commit aus. Hooks niemals mit `--no-verify` umgehen.
- Die CI (`.github/workflows/checks.yml`) führt alle Prüfungen bei Pull Requests nach `main` und `develop` aus.
- Nutzerrelevante Änderungen im Abschnitt `[Unreleased]` der `CHANGELOG.md` eintragen (Format: Keep a Changelog).

Vor jedem Commit müssen alle Prüfungen fehlerfrei durchlaufen:

```bash
.venv/bin/ruff format .
.venv/bin/ruff check .
.venv/bin/mypy .
.venv/bin/pytest
```

- **ruff** prüft unter anderem Namenskonventionen, fehlende Type Hints, Komplexität und die Single-Return-Regel (`max-returns = 1`).
- **mypy** läuft im strikten Modus.

## Git

- **Niemals pushen.** Pushen macht ausschließlich der Nutzer.
- **Nur committen, wenn der Nutzer ausdrücklich dazu auffordert oder es freigibt.** Ohne Aufforderung oder Freigabe bleiben Änderungen uncommittet; der Nutzer committet dann selbst.

### Branch-Modell

- `main`: Stand für das Deployment. Hier wird nicht direkt entwickelt.
- `develop`: Integrationsbranch für die Entwicklung.
- Arbeitsbranches (`<typ>/<beschreibung>`) werden von `develop` abgezweigt und wieder in `develop` gemergt.
- `develop` wird in `main` gemergt, wenn ein Stand deployt werden soll. Das entscheidet der Nutzer.

### Typen

Branches und Commits verwenden dieselben Typen:

Emojis werden als Gitmoji-Shortcode geschrieben, nicht als Unicode-Zeichen.

| Typ        | Shortcode            | Verwendung                                     |
|------------|----------------------|------------------------------------------------|
| `feat`     | `:sparkles:`         | Neue Funktion                                  |
| `fix`      | `:bug:`              | Fehlerbehebung                                 |
| `refactor` | `:recycle:`          | Umbau ohne Verhaltensänderung                  |
| `test`     | `:white_check_mark:` | Tests hinzufügen oder anpassen                 |
| `docs`     | `:memo:`             | Dokumentation                                  |
| `style`    | `:art:`              | Formatierung, Code-Struktur ohne Logikänderung |
| `perf`     | `:zap:`              | Performance-Verbesserung                       |
| `build`    | `:package:`          | Build-System, Abhängigkeiten                   |
| `ci`       | `:construction_worker:` | CI-Konfiguration                            |
| `chore`    | `:wrench:`           | Wartung, Konfiguration, Sonstiges              |

### Branchnamen

Schema: `<typ>/<beschreibung>`

- `<beschreibung>` auf Englisch, in Kleinbuchstaben, Wörter mit Bindestrich getrennt, kurz und aussagekräftig.
- Beispiele: `feat/create-accounts`, `fix/balance-rounding`, `docs/claude-md`.

### Commit-Nachrichten

Schema:

```
<typ>: <shortcode> <summary>

<optional body>
```

- Die gesamte Nachricht ist auf Englisch.
- Keine `Co-Authored-By`-Zeilen oder sonstigen Trailer.
- Die erste Zeile ist ein knapper Einzeiler (max. ca. 72 Zeichen), im Imperativ, kleingeschrieben, ohne Punkt am Ende.
- Ein Beschreibungstext nach einer Leerzeile nur, wenn nötig: Er erklärt das *Warum* und wichtige Details, nicht das, was der Diff ohnehin zeigt.
- Beispiele:
  - `feat: :sparkles: add account creation and listing`
  - `fix: :bug: fix rounding error in balance calculation`
  - `docs: :memo: add initial claude.md for this project`

## Clean-Code-Regeln

Wir programmieren nach den Prinzipien von Clean Code. Lesbarkeit und Verständlichkeit haben Vorrang vor Kürze oder Cleverness.

### Namen

- Aussagekräftige, ausgeschriebene englische Namen für Variablen, Funktionen, Klassen und Module: `account_balance`, nicht `bal` oder `x`.
- Der Name sagt, *was* etwas ist oder tut. Ein Kommentar sollte dafür nicht nötig sein.
- Funktionen heißen nach Tätigkeiten (`calculate_balance`, `assign_purpose`), Klassen und Variablen nach Dingen (`Account`, `Transaction`).
- Boolesche Werte lesen sich wie Aussagen: `is_locked`, `has_sufficient_funds`.
- Keine Abkürzungen außer allgemein üblichen (`id`, `iban`).
- Begriffe aus der Fachdomäne einheitlich verwenden: ein Konzept, ein Wort.

### Funktionen

- Eine Funktion erledigt genau eine Aufgabe und ist kurz.
- Möglichst wenige Parameter. Gehören mehrere Werte zusammen, wird daraus ein eigenes Objekt.
- Keine versteckten Seiteneffekte: Eine Funktion tut, was ihr Name verspricht, und nichts darüber hinaus.
- Abfragen und Befehle trennen: Eine Funktion ändert entweder einen Zustand oder liefert einen Wert, nicht beides.
- Keine Flag-Parameter, die das Verhalten umschalten. Stattdessen zwei Funktionen schreiben.
- **Single Return:** Jede Funktion hat genau ein `return`, und zwar am Ende. Keine vorzeitigen Rücksprünge; das Ergebnis wird in einer Variablen gesammelt und am Schluss zurückgegeben.

### Typing

- **Type Hints sind Pflicht** für alle Parameter, Rückgabewerte und Attribute, auch bei `-> None`.
- Wo der Typ nicht offensichtlich ist, werden auch lokale Variablen annotiert.
- Moderne Syntax verwenden: `list[str]`, `dict[str, Decimal]`, `X | None`.
- `Any` vermeiden; wenn es unumgänglich ist, die Begründung kommentieren.
- Für strukturierte Daten typisierte Konstrukte nutzen (`dataclass`, `Enum`, `TypedDict`, `Protocol`) statt loser Dicts oder Tupel.
- Der Code muss eine statische Typprüfung (z. B. mypy im strikten Modus) fehlerfrei bestehen.

### Klassen und Module

- **Single Responsibility:** Jede Klasse und jedes Modul hat genau einen Grund, sich zu ändern.
- Fachlogik, Datenhaltung und Benutzeroberfläche sind klar voneinander getrennt.
- Abhängigkeiten zeigen auf Abstraktionen, nicht auf konkrete Implementierungen (Dependency Inversion), wo das die Austauschbarkeit oder Testbarkeit verbessert.
- Komposition hat Vorrang vor Vererbung.

### Wiederholungen vermeiden (DRY)

- Kein kopierter Code. Wiederkehrende Logik wird in eine Funktion oder Klasse ausgelagert.
- Konstanten und Konfigurationswerte werden einmal zentral definiert. Keine „magischen Zahlen“ oder Strings im Code.
- Aber: keine voreilige Abstraktion. Erst wenn sich etwas tatsächlich wiederholt, wird es zusammengefasst.

### Einfachheit

- **KISS:** die einfachste Lösung, die das Problem korrekt löst.
- **YAGNI:** nichts auf Vorrat bauen, was aktuell nicht gebraucht wird.
- Toten oder auskommentierten Code löschen; die Versionsgeschichte steht in Git.

### Kommentare

- Guter Code erklärt sich selbst. Kommentare erklären das *Warum*, nicht das *Was*.
- Docstrings für öffentliche Funktionen und Klassen, wenn Zweck oder Verhalten nicht schon aus dem Namen klar wird.
- Veraltete Kommentare sofort anpassen oder entfernen.

### Fehlerbehandlung

- Fehler über Exceptions melden, nicht über Sonderwerte wie `None` oder `-1`.
- Eigene, aussagekräftige Exception-Klassen für fachliche Fehler (z. B. `InsufficientFundsError`).
- Exceptions nicht stillschweigend schlucken.
- Eingaben an den Systemgrenzen (Benutzereingaben, Importdateien) validieren.

### Fachliche Besonderheiten

- Geldbeträge **nie** als `float` speichern oder berechnen. Stattdessen `Decimal` oder ganzzahlige Cent-Beträge verwenden.

### Tests

- Fachlogik wird durch automatisierte Tests abgesichert.
- Tests sind genauso sauber und lesbar wie der Produktivcode.
- Ein Test prüft genau ein Verhalten, und sein Name beschreibt, welches.

### Formatierung

- Einheitlicher Stil im ganzen Projekt, automatisch durch ruff (Formatter und Linter) sichergestellt.
- Zusammengehöriger Code steht beieinander; von oben nach unten lesbar, vom Allgemeinen zum Detail.

### Pfadfinder-Regel

- Code immer etwas sauberer hinterlassen, als man ihn vorgefunden hat, solange es im Rahmen der aktuellen Aufgabe bleibt.
