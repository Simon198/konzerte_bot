# Datenschutzerklärung

**Stand:** 19. Oktober 2026

Diese Datenschutzerklärung informiert dich gemäß Art. 12 ff. DSGVO darüber, welche
personenbezogenen Daten der Telegram-Bot **„konzert_bot“** (nachfolgend „der Bot“)
verarbeitet, zu welchen Zwecken dies geschieht und welche Rechte dir zustehen.

## 1. Verantwortlicher

Verantwortlicher im Sinne der DSGVO ist:

**Simon Heinrich**  
**@unst0ppabel**

(Impressum: siehe `IMPRESSUM.md` im Projekt-Repository)

## 2. Allgemeines

Der Bot informiert über Konzerte an ausgewählten Veranstaltungsorten und sendet auf
Wunsch Empfehlungen und Erinnerungen. Die Nutzung ist freiwillig. Mit dem Starten des
Bots über `/start` forderst du den beschriebenen Dienst an. Für die Übermittlung deiner
Daten an Telegram in Drittländer sowie die Benachrichtigung des Administrators holt der
Bot beim ersten Start deine ausdrückliche Einwilligung ein (Schaltfläche „Ich stimme zu“),
die du jederzeit widerrufen kannst.

## 3. Welche Daten werden verarbeitet?

| Datenkategorie | Beispiele | Zweck |
|---|---|---|
| Telegram-Nutzer-ID | eindeutige numerische ID | Identifikation und Zuordnung deiner Einstellungen |
| Telegram-Chat-ID | Chat-ID | Zusenden von Nachrichten |
| Telegram-Benutzername | `@name` (sofern gesetzt) | Anzeige und Benachrichtigung des Administrators |
| Telegram-Vor- und Nachname | `Vorname Nachname` (nur falls kein Benutzername gesetzt) | Benachrichtigung des Administrators; wird nicht dauerhaft gespeichert |
| Interessen | Konzerte, für die du „Interesse“ markiert hast | Empfehlungen und Erinnerungen |
| Bereits angezeigte Konzerte | Event-ID + Message-ID | Vermeidung doppelter Empfehlungen, Aktualisierung von Nachrichten |
| Abbestellte Quellen | Veranstaltungsorte | Anpassung deiner Empfehlungen |
| Abbestellte Genres | Musikrichtungen, die du nicht erhalten möchtest | Anpassung deiner Empfehlungen |
| Admin-Status | ja/nein | Zugriffskontrolle |
| Log-Daten | Nutzer-ID, Zeitstempel, Fehlermeldungen | Sicherstellung von Stabilität und Sicherheit |

## 4. Zwecke der Verarbeitung

Die Daten werden ausschließlich verarbeitet, um

- den Bot zu betreiben und dir Konzertempfehlungen und Erinnerungen zu senden,
- deine Einstellungen (Quellen, Genres, Interessen) zu speichern und zu berücksichtigen,
- den Betrieb des Bots technisch abzusichern und Fehler zu beheben (Logging).

Eine darüber hinausgehende Verwendung findet nicht statt.

## 5. Rechtsgrundlagen

- **Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung):** Die Verarbeitung ist
  erforderlich, um den von dir mit `/start` angeforderten Dienst zu erbringen
  (Empfehlungen, Erinnerungen, Speicherung deiner Einstellungen).
- **Art. 6 Abs. 1 lit. a DSGVO (Einwilligung):** Auf deiner ausdrücklichen
  Einwilligung beruhen
  - die Übermittlung personenbezogener Daten an Telegram in Drittländer
    (Art. 49 Abs. 1 lit. a DSGVO),
  - die Benachrichtigung des Administrators über neue Nutzer und markierte Interessen.
  Die Einwilligung erteilst du beim ersten Start über die Schaltfläche „Ich stimme zu"
  und kannst sie jederzeit widerrufen.
- **Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse):** Das Logging und die
  Fehlerbehandlung dienen dem berechtigten Interesse an einem stabilen und sicheren
  Betrieb des Bots.

## 6. Empfänger der Daten

- **Telegram Messenger Inc. / Meta:** Der Bot läuft über die Telegram-Plattform. Nachrichten,
  IDs und Benutzernamen werden technisch bedingt über die Server von Telegram verarbeitet.
- **Administrator(en) des Bots:** Erhalten Benachrichtigungen über neue Nutzer
  (ggf. mit Benutzername bzw. Vor- und Nachname), Interessen sowie
  technische Log- und Fehlermeldungen.

Eine Weitergabe an weitere Dritte erfolgt nicht.

## 7. Übermittlung in Drittländer

Telegram verarbeitet Daten auch auf Servern außerhalb der Europäischen Union bzw. des
Europäischen Wirtschaftsraums (insbesondere in den USA). Rechtsgrundlage für diese
Übermittlung ist deine ausdrückliche Einwilligung (Art. 49 Abs. 1 lit. a DSGVO), die du
beim ersten Start über die Schaltfläche „Ich stimme zu“ erteilst.

## 8. Speicherdauer

- **Nutzerdaten** (ID, Chat-ID, Benutzername, Interessen, angezeigte Konzerte,
  Abbestellungen): bis du den Dienst nicht mehr nutzt bzw. bis du `/delete` ausführst.
- **Vor- und Nachname:** wird nicht dauerhaft gespeichert, sondern nur zur einmaligen
  Benachrichtigung des Administrators verwendet.
- **Log-Dateien:** automatische Löschung nach **30 Tagen**.
- Vergangene Konzerte und damit verknüpfte Interessen-/Anzeige-Daten werden laufend
  automatisch entfernt.

## 9. Deine Rechte

Dir stehen nach der DSGVO folgende Rechte zu:

- **Auskunft** (Art. 15) über die zu dir gespeicherten Daten,
- **Berichtigung** (Art. 16) unrichtiger Daten,
- **Löschung** (Art. 17) – am einfachsten per `/delete` oder per Anfrage an den Verantwortlichen,
- **Einschränkung der Verarbeitung** (Art. 18),
- **Datenübertragbarkeit** (Art. 20),
- **Widerspruch** gegen die Verarbeitung (Art. 21),
- **Widerruf** einer erteilten Einwilligung (Art. 7 Abs. 3) – jederzeit möglich.

Zur Ausübung deiner Rechte genügt eine Nachricht an die unter Abschnitt 1 genannte
Kontaktmöglichkeit.

## 10. Beschwerderecht

Du hast das Recht, dich bei einer Datenschutz-Aufsichtsbehörde zu beschweren (Art. 77 DSGVO),
z. B. beim

**Hessischen Beauftragten für Datenschutz und Informationsfreiheit (HBDI)**  
*(bitte die für deinen Wohnsitz zuständige Aufsichtsbehörde prüfen)*

## 11. Datensicherheit

Der Bot setzt geeignete technische und organisatorische Maßnahmen ein, um deine Daten vor
unbefugtem Zugriff, Verlust oder Missbrauch zu schützen. Die Daten werden in einer lokalen
Datenbank gespeichert und sind nicht öffentlich zugänglich.

## 12. Keine automatisierte Entscheidungsfindung

Es findet keine automatisierte Entscheidungsfindung einschließlich Profiling im Sinne von
Art. 22 DSGVO statt.

## 13. Änderungen dieser Datenschutzerklärung

Diese Datenschutzerklärung wird bei Bedarf angepasst. Die jeweils aktuelle Fassung wird an
gleicher Stelle bereitgestellt.
