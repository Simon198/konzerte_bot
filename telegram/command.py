from enum import Enum


class Commands(Enum):
    start = "Registrierung neuer Nutzer"
    sources = "Konfiguration, von welchen Veranstaltern Du Events erhalten möchtest"
    go = "Lädt die nächsten n Konzerte, über die Du noch nicht informiert wurdest. Wenn keine Zahl nach dem Kommando steht, werden die nächsten 5 Konzerte geladen."
    next = "Lädt die nächsten n Konzerte, die Dich interessieren. Wenn keine Zahl nach dem Kommando steht, werden die nächsten 5 Konzerte geladen."
    feature = "Schreibe ein Feature-Wunsch, der dir wichtig ist"
    changelog = "Erhalte den letzten Changelog-Eintrag"
