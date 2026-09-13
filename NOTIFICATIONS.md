# E-Mail-Benachrichtigungen

Das System verschickt zwei Arten von Benachrichtigungen:

| Benachrichtigung | Auslöser | Empfänger | Läuft in |
|---|---|---|---|
| **Wochen-Erinnerung** | Für die kommende Kalenderwoche (Mo–So) existiert kein Eintrag | Alle aktiven Benutzer mit `can_take_duty` oder Rolle `planner` | `scheduler` |
| **Bestätigung nötig** | Ein neuer, unbestätigter Eintrag wurde angelegt | Alle aktiven Admins (außer der Person, die den Eintrag angelegt hat) | `backend` |

Beide Mails werden in der Tabelle `notification_log` protokolliert. Für die Wochen-Erinnerung dient dieser Eintrag zusätzlich als Sperre, damit pro Kalenderwoche nur **eine** Mail rausgeht – auch wenn der Scheduler-Container zwischendurch neu startet.

## Versandweg

Der Transport wird automatisch gewählt:

1. **SMTP** – wenn `SMTP_HOST` gesetzt ist.
2. **Microsoft Graph `sendMail`** – wenn MS-Graph-Credentials und ein Absender (`MAIL_FROM`, ersatzweise `MS_CALENDAR_EMAIL`) vorhanden sind. Benötigt die Application Permission `Mail.Send` und ein echtes Absenderpostfach — Schritt-für-Schritt inklusive Einschränkung auf ein einzelnes Postfach und Fehlerdiagnose in [MICROSOFT_GRAPH_SETUP.md, Abschnitt 6](MICROSOFT_GRAPH_SETUP.md#6-mail-versand-über-graph-optional).
3. **Mock** – ist nichts konfiguriert, wird die Mail nur ins Log geschrieben (`[MAIL] MOCK ...`). Das System läuft dadurch auch ohne Mail-Setup weiter.

## Konfiguration (`.env`)

```ini
# SMTP (hat Vorrang)
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=notfallservice@deine-firma.de
SMTP_PASSWORD=...
SMTP_STARTTLS=true
SMTP_SSL=false

# Absender & Link in den Mails
MAIL_FROM=notfallservice@deine-firma.de
MAIL_FROM_NAME=Notfallservice Manager
APP_BASE_URL=https://notfall.deine-firma.de

# Wochen-Erinnerung
REMINDER_ENABLED=true
REMINDER_WEEKDAY=3   # 0=Montag ... 6=Sonntag (3 = Donnerstag)
REMINDER_HOUR=9      # Stunde in Europe/Berlin
```

Der Scheduler prüft im Minutentakt; die Erinnerung wird am konfigurierten Wochentag ab `REMINDER_HOUR` verschickt. Startet der Container an dem Tag später neu, wird die Mail nachgeholt (sofern für die Woche noch keine verschickt wurde).

## Prüfen / Testen

Als Admin einloggen und:

* `GET /api/notifications/status` – zeigt aktiven Transport, Admin-Empfänger und die letzten 20 verschickten Benachrichtigungen.
* `POST /api/notifications/test` – schickt eine Testmail an die eigene Adresse.

Beide Endpunkte sind auch in der API-Doku unter `/api/docs` zu finden.

Logs:

```bash
docker compose logs -f scheduler | grep -E "REMINDER|MAIL"
```

## Erinnerung manuell auslösen

```bash
docker compose exec scheduler python -c "
from datetime import datetime
from database import SessionLocal
from reminders import send_weekly_reminder
db = SessionLocal()
print(send_weekly_reminder(db, datetime.now(), force=True))
"
```

`force=True` ignoriert die Sperre aus `notification_log`, aber nicht die Prüfung, ob die Woche bereits besetzt ist.
