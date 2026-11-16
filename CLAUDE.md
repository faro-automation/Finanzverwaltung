# CLAUDE.md

Hinweise für Claude Code zur Arbeit in diesem Repository.

## Projekt

**Finanzverwaltung**: ein Programm, um alle Konten und Bargeldreserven zu verwalten und Verwendungszwecken zuzuordnen.

Stand: Das Datenmodell (`src/finance_manager/model/`) steht. Als Nächstes folgen Logik (Buchungen anwenden, Bilanzprüfung, Gehaltsaufteilung), Speicherung, Import, Export und die Oberfläche (Desktop, Qt).

## Kommunikation und Arbeitsweise

- Mit dem Nutzer wird Deutsch gesprochen.
- Vor größeren Änderungen erst planen und abstimmen, dann umsetzen.
- **In kleinen Schritten arbeiten und nur bauen, was ausdrücklich gewünscht ist.** Keine Klassen, Methoden oder Felder auf Vorrat. Ist unklar, ob etwas gewollt ist, weglassen und in einem Satz erwähnen.
- Namen und Fachbegriffe sind dem Nutzer wichtig: neue Namen kurz vorstellen, damit er sie prüfen kann.

## Sprache im Repository

- **Alles im Repository ist auf Englisch:** Bezeichner, Code, Kommentare, Docstrings, Commit-Nachrichten, Branchnamen und Dokumentation im Code.
- **Ausnahme Fachbegriffe:** Deutsche Begriffe nur dort, wo der englische Begriff missverständlich wäre. Diese werden dann **nicht übersetzt**, auch nicht in Klassen-, Attribut- und Methodennamen.
  - Beispiele für die Mischung: `topf.is_active`, `topf.aufloesen()`, `value.is_negative`, `InvalidValueError`
  - Umlaute in Bezeichnern werden umschrieben: `aufloesen`, `toepfe`, `rueckzahlung`.

## Datenmodell und Fachbegriffe

Alle Klassen liegen in `src/finance_manager/model/`.

| Begriff | Klasse / Name | Bedeutung |
|---|---|---|
| Nutzerkonfiguration | `UserConfig` (`config.py`) | Zustand pro Nutzer: Zähler für Kennungen, vergebene Topfnamen. Wird beim Anlegen von Geldorten, Töpfen, realen Buchungen und Topfumbuchungen übergeben. |
| Währung | `Currency` (`money.py`) | Enum, z. B. `Currency.EURO` mit Symbol `€` und 2 Nachkommastellen. `exchange_rate` ist vorbereitet und vorerst `None`. |
| Geldwert | `Value` (`money.py`) | Zahl mit Vorzeichen und Währung, z. B. −12,50 €. **Nie „Betrag“** nennen, ein Betrag hat kein Vorzeichen. |
| Monat | `Month` (`month.py`) | Jahr und Monatsnummer; Monate sind chronologisch vergleichbar. |
| Geldort | `Geldort` (`geldort.py`) | Ort, an dem Geld tatsächlich liegt. Abstrakte Basis von `Bankkonto` (mit `bank` und `Kontoart`), `Bargeld` (z. B. die Schublade) und `Gutscheine` (ein Bestand aus vielen Gutscheinen). Hat `get_actual_value()`/`set_actual_value()` und den Status `ACTIVE`/`CLOSED`. |
| Kontoart | `Kontoart` | Girokonto, Tagesgeldkonto, Festgeldkonto, Sparbuch, Sparbrief, Bausparvertrag, Kreditkartenkonto. |
| Topf | `Topf` (`topf.py`) | Zweck, dem Geld zugeordnet ist, unabhängig vom Geldort. Hat `main_geldort` (Hauptgeldort) und `geldort_values` (Wert je Geldort-Kennung); der aktuelle Wert ist deren Summe. Status `ACTIVE`/`AUFGELOEST`. |
| Transaktion | `Transaction` (`transaction.py`) | Allgemeine Geldbewegung mit `value` und `transaction_date`. |
| Reale Buchung | `RealTransaction` | Bewegung auf einem Geldort, z. B. eine Zeile im Kontoauszug. Vorzeichen bestimmt `direction` (`INCOMING`/`OUTGOING`); dazu `statement_text`, Markierung `get_mark()` und genau ein `topf` (oder noch keiner, z. B. nach dem Import), gesetzt mit `assign_topf()`. Muss eine Buchung aufgeteilt werden, kommt sie in einen Topf, und die Teile werden per `TopfTransfer` weitergebucht. |
| Topfumbuchung | `TopfTransfer` | Interne Umbuchung von `source`- zu `target`-Topf am selben `geldort`; Wert immer positiv. Mit `split_of` ist sie die Aufteilung einer realen Buchung (zählt als Ausgabe des Zieltopfs) und muss vom Topf und Geldort dieser Buchung ausgehen; ohne `split_of` ein Umschichten von Erspartem. Die Verknüpfung steht nur an der Umbuchung, nicht zusätzlich an der Buchung. |
| Auslage, Rückzahlung | `Auslage`, `TransactionMark.AUSLAGE`/`.RUECKZAHLUNG` | Auslage für andere mit erwarteter Anzahl Rückzahlungen (`expected_rueckzahlung_amount`, Standard 1). Beträge werden bewusst nicht verglichen. |
| Gehalt | `Salary` (`salary.py`) | Geplantes Gehalt: `value`, `geldort` (wo es eingeht) und `topf` (Gehaltstopf, hält das Gehalt bis zur Aufteilung). |
| Gehaltsplan | `SalaryPlan` | Gehalt, Resttopf (`remainder_topf`), gültig ab Monat (`valid_from`) und Aufteilung (`allocation`). Kein Enddatum: ein Plan gilt bis zum nächsten. |
| Gehaltsteil, Posten | `SalaryPart`, `SalaryPartItem` | Teil des Gehalts für einen Topf an einem Geldort, bestehend aus benannten Posten (z. B. Versicherungen = KFZ + Haftpflicht + …). |

### Regeln des Modells

- **Kennungen** werden automatisch vergeben und nie wiederverwendet; gezählt wird pro Nutzer in der `UserConfig`:
  - Geldort: zwei Teile plus je Kombination hochzählende Zahl, getrennt durch `_`: `ING_Tagesgeldkonto_02`, `Bargeld_Schublade_01`, `Gutscheine_Geburtstag_01`.
  - Reale Buchung: Jahr, Monat und je Monat hochzählende Zahl: `2026_03_0042`.
  - Topfumbuchung: Jahr, Monat, Name des Quelltopfs und je Monat und Quelltopf hochzählende Zahl: `2026_03_Urlaub_0002`.
  - Topf: der vom Nutzer gewählte Name, eindeutig pro Nutzer. Umbenennen geht ab einem Monat (`rename`); `get_name(month)` liefert den damals gültigen Namen. Alte Namen bleiben reserviert.
- Geldorte werden nie gelöscht, nur geschlossen, und nur bei Wert 0. Töpfe werden nur bei Wert 0 aufgelöst.
- Im Topf fällt ein Geldort weg, sobald sein Wert 0 erreicht; derselbe Geldort steht nie doppelt drin.
- Die Gehaltsteile dürfen zusammen nie mehr als das Gehalt ergeben. Jede Änderung am `SalaryPlan` wird vorher geprüft und bei Verstoß mit Fehler abgelehnt.
- **Nur vorbereitende Felder** (z. B. `Currency.exchange_rate`) werden mit `None` initialisiert, bis es eine echte Verwendung gibt.

### Geplant, noch nicht umgesetzt

- Später: Hilfswerte (freie Formeln pro Topf), Aktien, Forderungen an andere.

## Ordnerstruktur

- `src/finance_manager/`: der gesamte Quellcode des Projekts.
  - `model/`: das Datenmodell, ohne Abhängigkeit zu Speicherung oder Oberfläche.
- `tests/`: alle Tests (pytest), gleich gegliedert wie `src/finance_manager/`.
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

- **ruff** prüft unter anderem Namenskonventionen, fehlende Type Hints, Komplexität (`max-complexity = 8`) und die Single-Return-Regel (`max-returns = 1`). Die Grenzen für die Anzahl von Parametern (`PLR0913`, `PLR0917`) sind bewusst abgeschaltet.
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

- Aussagekräftige, ausgeschriebene Namen für Variablen, Funktionen, Klassen und Module: `kontostand`, nicht `ks` oder `x` (Fachbegriffe deutsch, siehe oben).
- Der Name sagt, *was* etwas ist oder tut. Ein Kommentar sollte dafür nicht nötig sein.
- **Funktionen und Methoden** heißen immer nach **Tätigkeiten**, beginnen also mit einem Verb: `get_actual_value`, `aufloesen`, `add_geldort_value`, `change_salary_value`.
- **Klassen** heißen immer nach **Substantiven**: `Geldort`, `Topf`, `Value`.
- **Variablen, Attribute und Properties** heißen nach **Substantiven** (`main_geldort`, `allocation`) oder **Eigenschaften** (`is_active`, `is_negative`).
- Boolesche Werte lesen sich wie Aussagen: `is_active`, `is_open`, `has_rueckzahlung`.
- **Keine sinnlosen Abkürzungen.** Eigene Namen werden immer ausgeschrieben: `currency`, nicht `cur` oder `curr`. Erlaubt sind nur allgemein verständliche Abkürzungen wie `id` oder `iban` und Standardcodes als Daten (z. B. Währungscode `"EUR"`).
- Auch abgekürzte oder kryptische Namen aus Bibliotheken (z. B. `eq=False` bei `dataclass`, `Decimal.scaleb`) nur verwenden, wenn es keine verständliche Alternative gibt. Dann kurz kommentieren, was sie bewirken.
- Begriffe aus der Fachdomäne einheitlich verwenden: ein Konzept, ein Wort.

### Funktionen

- Eine Funktion erledigt genau eine Aufgabe und ist kurz.
- Keine feste Obergrenze für Parameter. Gehören mehrere Werte fachlich zusammen, wird daraus ein eigenes Objekt (z. B. `Salary` aus Wert, Geldort und Topf).
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
- **Zustand mit Regeln ist privat.** Attribute, für die Regeln gelten, beginnen mit `_` und werden nur über Methoden geändert, die die Regeln prüfen. Gelesen wird über Properties ohne Setter; Sammlungen werden als Tupel oder Kopie herausgegeben.
- Solche Klassen haben ein ausgeschriebenes `__init__`. `@dataclass` (meist `frozen=True`) nur für einfache, unveränderliche Werteklassen wie `Value`, `Month`, `Salary`, `SalaryPart`.
- Gemeinsame Ressourcen pro Nutzer (Zähler, vergebene Namen) gehören in die `UserConfig`, nie als Klassenvariable in eine Fachklasse.
- Keine zyklischen Importe. Die Module im Modell sind geschichtet, jedes importiert nur aus den Schichten davor: `errors` → `money`, `month`, `config` → `geldort` → `topf` → `transaction`, `salary`.
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
- Eigene, aussagekräftige Exception-Klassen für fachliche Fehler (z. B. `TopfAlreadyAufgeloestError`).
- Exceptions nicht stillschweigend schlucken.
- Eingaben an den Systemgrenzen (Benutzereingaben, Importdateien) validieren.

### Fachliche Besonderheiten

- Geldwerte **nie** als `float` speichern oder berechnen. Stattdessen `Value` mit `Decimal` verwenden; die erlaubten Nachkommastellen legt die `Currency` fest.

### Tests

- Fachlogik wird durch automatisierte Tests abgesichert.
- Tests sind genauso sauber und lesbar wie der Produktivcode.
- Ein Test prüft genau ein Verhalten, und sein Name beschreibt, welches.

### Formatierung

- Einheitlicher Stil im ganzen Projekt, automatisch durch ruff (Formatter und Linter) sichergestellt.
- Zusammengehöriger Code steht beieinander; von oben nach unten lesbar, vom Allgemeinen zum Detail.

### Pfadfinder-Regel

- Code immer etwas sauberer hinterlassen, als man ihn vorgefunden hat, solange es im Rahmen der aktuellen Aufgabe bleibt.
