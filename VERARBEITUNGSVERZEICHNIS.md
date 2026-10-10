# Verzeichnis von Verarbeitungstätigkeiten (Art. 30 DSGVO)

**Verantwortlicher:** Simon Heinrich · Telegram **@unst0ppabel**
**Stand:** 10. Oktober 2026

## Verarbeitungstätigkeit: Betrieb des Telegram-Bots „konzert_bot“

| Punkt | Angabe |
|---|---|
| **Zwecke** | Betrieb des Bots, Versand von Konzertempfehlungen und Erinnerungen, Speicherung und Berücksichtigung von Einstellungen, Entgegennahme von Feature-Wünschen, technische Absicherung und Fehlerbehebung (Logging) |
| **Betroffene Personen** | Nutzer des Bots |
| **Datenkategorien** | Telegram-Nutzer-ID, Telegram-Chat-ID, Telegram-Benutzername, Interessen (markierte Konzerte), bereits angezeigte Konzerte (Event-ID + Message-ID), abbestellte Quellen, Feature-Wünsche, Admin-Status, Einwilligungsdaten (Ja/Nein, Zeitpunkt, Version), Log-Daten (Nutzer-ID, Zeitstempel, Fehlermeldungen) |
| **Rechtsgrundlagen** | Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung, Kerndienst) · Art. 6 Abs. 1 lit. a DSGVO (Einwilligung: Drittlandübermittlung, Admin-Benachrichtigung, freiwillige Angaben) · Art. 6 Abs. 1 lit. f DSGVO (Logging, Fehlerbehandlung) |
| **Empfänger** | Telegram Messenger Inc. / Meta (Plattform), Administrator(en) des Bots |
| **Drittlandübermittlung** | Telegram verarbeitet Daten auch in den USA; Grundlage: Einwilligung (Art. 49 Abs. 1 lit. a DSGVO) |
| **Speicherdauer** | Nutzerdaten bis `/delete` bzw. Nichtnutzung · Feature-Wünsche bis Bearbeitung · Log-Dateien 30 Tage (automatische Rotation) · vergangene Konzerte werden laufend entfernt |
| **Technische & organisatorische Maßnahmen** | Lokale Datenbank (nicht öffentlich zugänglich), Zugriff nur durch den Administrator, keine automatisierte Entscheidungsfindung/Profiling (Art. 22 DSGVO) |

## Betroffenenrechte – Umsetzung

| Recht | Umsetzung |
|---|---|
| Auskunft (Art. 15) | Befehl `/mydata` |
| Datenübertragbarkeit (Art. 20) | Befehl `/mydata` (maschinenlesbare JSON-Datei) |
| Löschung (Art. 17) | Befehl `/delete` |
| Berichtigung (Art. 16) | `/sources` und Interesse-Buttons; sonst Nachricht an den Verantwortlichen |
| Widerspruch (Art. 21) & Widerruf (Art. 7 Abs. 3) | Nachricht an den Verantwortlichen bzw. `/delete` |
