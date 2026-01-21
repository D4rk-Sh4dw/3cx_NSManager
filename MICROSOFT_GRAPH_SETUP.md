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
7.  ⚠️ **WICHTIG**: Du musst jetzt auf den Button **Grant admin consent for [Deine Organisation]** klicken, damit die Berechtigungen aktiv werden.

## 5. Ziel-Kalender (Shared Mailbox / Public Calendar)

Standardmäßig erstellt die Graph API Termine im Kalender des Users, dem die App "gehört" (oft unklar bei App-Permissions), oder man muss einen spezifischen User angeben.

Für einen **öffentlichen Team-Kalender** empfehlen wir eine **Shared Mailbox** (Freigegebenes Postfach) oder einen **Resource Account** (Raumpostfach).

1.  Erstelle im Microsoft 365 Admin Center eine Shared Mailbox, z.B. `notfall-kalender@deine-firma.de`.
2.  Trage diese E-Mail-Adresse in deine `.env` Datei ein unter `MS_CALENDAR_EMAIL`.

Das System nutzt dann diese Adresse in der URL: `/users/notfall-kalender@deine-firma.de/calendar/events`.

## Zusammenfassung .env

```ini
MS_TENANT_ID=00000000-0000-0000-0000-000000000000
MS_CLIENT_ID=11111111-1111-1111-1111-111111111111
MS_CLIENT_SECRET=DeinGeheimesSecretValue...
MS_CALENDAR_EMAIL=notfall-kalender@deine-firma.de
```
