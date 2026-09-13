# Microsoft Graph & Kalender Integration Setup

Damit das System Termine in einem öffentlichen Kalender oder einer Shared Mailbox erstellen kann, muss eine **App Registration** in Azure Active Directory (Entra ID) angelegt werden.

## 1. App Registration erstellen

1.  Gehe zum [Azure Portal](https://portal.azure.com/).
2.  Navigiere zu **Microsoft Entra ID** (früher Azure Active Directory).
3.  Wähle im Menü links **App registrations** -> **New registration**.
4.  **Name**: z.B. `NotfallService-Manager`.
5.  **Supported account types**: "Accounts in this organizational directory only (Single tenant)".
6.  **Redirect URI**: Kann leer bleiben (wir nutzen nur Backend-Service-to-Service).
7.  Klicke auf **Register**.

## 2. IDs kopieren

Nach der Erstellung siehst du die Übersicht ("Overview"). Kopiere folgende Werte in deine `.env` Datei:

*   **Application (client) ID** -> `MS_CLIENT_ID`
*   **Directory (tenant) ID** -> `MS_TENANT_ID`

## 3. Client Secret erstellen

Damit sich der Backend-Service ohne User-Login authentifizieren kann, brauchen wir ein "Secret".

1.  Wähle im Menü der App links **Certificates & secrets**.
2.  Tab **Client secrets** -> **New client secret**.
3.  **Description**: z.B. `BackendServer`.
4.  **Expires**: Wähle eine Gültigkeitsdauer (z.B. 24 Monate).
5.  Klicke **Add**.
6.  ⚠️ **WICHTIG**: Kopiere sofort den **Value** (nicht die Secret ID!). Das ist dein `MS_CLIENT_SECRET`.

## 4. Berechtigungen (API Permissions)

Die App braucht Schreibzugriff auf Kalender.

1.  Wähle im Menü links **API permissions**.
2.  Klicke **+ Add a permission** -> **Microsoft Graph**.
3.  Wähle **Application permissions** (NICHT Delegated permissions, da der Service im Hintergrund läuft).
4.  Suche nach `Calendars`.
5.  Wähle `Calendars.ReadWrite` (unter Application Permissions).
6.  Klicke **Add permissions**.
7.  Wenn die Benachrichtigungs-Mails über Graph (statt SMTP) verschickt werden sollen, füge zusätzlich `Mail.Send` (Application Permission) hinzu.
8.  ⚠️ **WICHTIG**: Du musst jetzt auf den Button **Grant admin consent for [Deine Organisation]** klicken, damit die Berechtigungen aktiv werden.

> **Hinweis zu `Mail.Send`:** Diese Berechtigung erlaubt der App den Versand als *jedes* Postfach im Tenant. Wie man das auf ein einzelnes Postfach einschränkt, steht in [Abschnitt 6](#6-mail-versand-über-graph-optional).

## 5. Ziel-Kalender (Shared Mailbox / Public Calendar)

Standardmäßig erstellt die Graph API Termine im Kalender des Users, dem die App "gehört" (oft unklar bei App-Permissions), oder man muss einen spezifischen User angeben.

Für einen **öffentlichen Team-Kalender** empfehlen wir eine **Shared Mailbox** (Freigegebenes Postfach) oder einen **Resource Account** (Raumpostfach).

1.  Erstelle im Microsoft 365 Admin Center eine Shared Mailbox, z.B. `notfall-kalender@deine-firma.de`.
2.  Trage diese E-Mail-Adresse in deine `.env` Datei ein unter `MS_CALENDAR_EMAIL`.

Das System nutzt dann diese Adresse in der URL: `/users/notfall-kalender@deine-firma.de/calendar/events`.

## 6. Mail-Versand über Graph (optional)

Dieser Abschnitt ist **nur nötig, wenn die Benachrichtigungs-Mails über Graph laufen sollen**. Ist `SMTP_HOST` gesetzt, wird SMTP verwendet und Graph spielt für den Mailversand keine Rolle — siehe [NOTIFICATIONS.md](NOTIFICATIONS.md).

### 6.1 Absenderpostfach festlegen

Graph verschickt die Mail *als* ein konkretes Postfach. Diese Adresse trägst du als `MAIL_FROM` ein (ohne Angabe wird `MS_CALENDAR_EMAIL` verwendet).

Es muss ein echtes Postfach in Exchange Online sein. Das funktioniert:

* **Shared Mailbox** (empfohlen) — braucht keine Lizenz, app-only `sendMail` funktioniert damit.
* **Normales Benutzerpostfach** — funktioniert, ist aber als Absender für Systemmails meist unpassend.

Das funktioniert **nicht**:

* Eine Mail-enabled Security Group oder Verteilerliste — das ist kein Postfach.
* Ein Alias, der auf ein anderes Postfach zeigt — nimm die primäre Adresse.
* Ein Entra-Benutzer ohne Exchange-Online-Postfach (typisch bei reinen Cloud-Accounts ohne Lizenz).

### 6.2 Zugriff auf ein Postfach einschränken (empfohlen)

`Mail.Send` als Application Permission erlaubt der App den Versand als **jedes** Postfach im Tenant. Eine [Application Access Policy](https://learn.microsoft.com/en-us/graph/auth-limit-mailbox-access) schränkt das auf die Postfächer ein, die die App wirklich braucht.

> ⚠️ **Wichtig für dieses Projekt:** Die Policy wirkt auf **alle** Postfach-Berechtigungen der App, also auch auf `Calendars.ReadWrite`. Die Gruppe muss deshalb **sowohl das Absenderpostfach (`MAIL_FROM`) als auch das Kalenderpostfach (`MS_CALENDAR_EMAIL`)** enthalten — sonst funktioniert nach dem Anlegen der Policy zwar der Mailversand, aber die Kalendereinträge schlagen fehl. Sind beide dieselbe Adresse, reicht ein Eintrag.

Die Policy lässt sich nur per Exchange-Online-PowerShell anlegen, nicht im Azure-Portal:

```powershell
Install-Module -Name ExchangeOnlineManagement -Scope CurrentUser
Connect-ExchangeOnline -UserPrincipalName admin@deine-firma.de

# Gruppe mit den Postfächern, auf die die App zugreifen darf
New-DistributionGroup -Name "Graph-NotfallService-Allowed" -Type Security `
  -PrimarySmtpAddress graph-notfallservice@deine-firma.de

Add-DistributionGroupMember -Identity "Graph-NotfallService-Allowed" `
  -Member notfallservice@deine-firma.de        # MAIL_FROM
Add-DistributionGroupMember -Identity "Graph-NotfallService-Allowed" `
  -Member notfall-kalender@deine-firma.de      # MS_CALENDAR_EMAIL

# Policy setzen (AppId = MS_CLIENT_ID)
New-ApplicationAccessPolicy `
  -AppId 11111111-1111-1111-1111-111111111111 `
  -PolicyScopeGroupId graph-notfallservice@deine-firma.de `
  -AccessRight RestrictAccess `
  -Description "Notfallservice Manager: nur Absender- und Kalenderpostfach"
```

Prüfen, ob die Policy so greift wie gedacht:

```powershell
# Muss AccessCheckResult "Granted" liefern
Test-ApplicationAccessPolicy -Identity notfallservice@deine-firma.de `
  -AppId 11111111-1111-1111-1111-111111111111

# Gegenprobe: ein beliebiges anderes Postfach muss "Denied" liefern
Test-ApplicationAccessPolicy -Identity irgendwer@deine-firma.de `
  -AppId 11111111-1111-1111-1111-111111111111
```

> Die Policy braucht nach dem Anlegen Zeit, bis sie überall greift — Microsoft nennt bis zu einer Stunde. `Test-ApplicationAccessPolicy` zeigt das Ergebnis sofort, der tatsächliche Graph-Aufruf kann in der Zwischenzeit noch abweichen.

### 6.3 Versand testen

Nach `Grant admin consent` und gesetztem `MAIL_FROM`: als Admin einloggen und

```bash
curl -s -X POST https://dein-host/api/notifications/test \
  -H "Authorization: Bearer $TOKEN"
```

Erwartet wird `{"status":"sent","transport":"graph"}`. Bei `500` steht der Graph-Fehler im Backend-Log:

```bash
docker compose logs backend | grep MAIL
```

### 6.4 Typische Fehler

| Symptom im Log | Ursache | Lösung |
|---|---|---|
| `transport: mock`, Mail wird nur geloggt | `MAIL_FROM`/`MS_CALENDAR_EMAIL` fehlt oder eine der drei `MS_*`-Variablen ist leer | `.env` prüfen, Container neu starten |
| `Graph send failed: 403` mit `ErrorAccessDenied` | `Mail.Send` fehlt, oder der **Admin Consent** wurde nach dem Hinzufügen nicht erteilt | Berechtigung prüfen, „Grant admin consent" klicken |
| `403` obwohl `Mail.Send` erteilt ist | Application Access Policy schließt das Absenderpostfach aus | `Test-ApplicationAccessPolicy` gegen `MAIL_FROM` laufen lassen |
| `404` mit `MailboxNotEnabledForRESTAPI` oder `ErrorInvalidUser` | `MAIL_FROM` hat kein Exchange-Online-Postfach, ist ein Alias oder eine Verteilerliste | Primäre Adresse eines echten Postfachs eintragen, siehe 6.1 |
| Mails gehen, aber Kalendereinträge schlagen plötzlich fehl | Policy angelegt, `MS_CALENDAR_EMAIL` aber nicht in der Gruppe | Kalenderpostfach zur Gruppe hinzufügen |
| `Error getting Graph access token` | Client Secret abgelaufen oder Secret-ID statt Value kopiert | Neues Secret erstellen, **Value** eintragen |

## Zusammenfassung .env

```ini
MS_TENANT_ID=00000000-0000-0000-0000-000000000000
MS_CLIENT_ID=11111111-1111-1111-1111-111111111111
MS_CLIENT_SECRET=DeinGeheimesSecretValue...
MS_CALENDAR_EMAIL=notfall-kalender@deine-firma.de

# Nur nötig, wenn die Benachrichtigungen über Graph laufen (kein SMTP_HOST gesetzt):
MAIL_FROM=notfall-kalender@deine-firma.de
```
