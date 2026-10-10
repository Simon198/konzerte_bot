from enum import Enum


class Commands(Enum):
    start = "Registrierung neuer Nutzer"
    sources = "Konfiguration, von welchen Veranstaltern Du Events erhalten möchtest"
    go = "Lädt die nächsten n Konzerte, über die Du noch nicht informiert wurdest. Wenn keine Zahl nach dem Kommando steht, wird nur das nächste Konzert geladen."
    next = "Lädt die nächsten n Konzerte, die Dich interessieren. Wenn keine Zahl nach dem Kommando steht, werden die nächsten 100 Konzerte geladen."
    feature = "Schreibe ein Feature-Wunsch, der dir wichtig ist"
    changelog = "Erhalte den letzten Changelog-Eintrag"
    datenschutz = "Zeigt die Datenschutzerklärung"
    pairings = "Zeigt Konzerte, für die sich mehrere Nutzer interessieren (nur für Admins)"
    delete = "Löscht alle deine gespeicherten Daten vollständig"
