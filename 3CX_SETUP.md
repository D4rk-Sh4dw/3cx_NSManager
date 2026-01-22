# 3CX Notfall-Routing Einrichten (Push Methode via XAPI)

Wir verwenden den "Push"-Ansatz: Der Scheduler aktualisiert automatisch die Mobilnummer eines Dummy-Users in der 3CX.

**Vorteil:** Funktioniert auch, wenn der lokale Server/Internet ausfällt (die Umleitung bleibt in der Cloud bestehen).

## 1. 3CX Vorbereitung

### A. Dummy User anlegen
1.  Erstellen Sie in der 3CX einen neuen Benutzer.
2.  **Rolle:** User (oder eine Rolle ohne Admin-Rechte).
3.  **Name:** "Notdienst Routing".
4.  **Nummer:** z.B. **999** (Merk dir diese Nummer für `CX_DUMMY_EXT`).
5.  **Email:** Eine technisch genutzte Email.

### B. Weiterleitungsregeln konfigurieren
Dieser Nutzer dient nur als "Weiche".
1.  Gehen Sie in die Einstellungen des Users -> **Weiterleitungsregeln**.
2.  Setzen Sie für **ALLE Status** (Verfügbar, Abwesend, DND, etc.) die Regel:
    - **"Externe Anrufe":** Weiterleiten an -> **Mobiltelefon**.
    - **"Interne Anrufe":** (Optional) Weiterleiten an -> Mobiltelefon.

*Hinweis: Der Scheduler wird das Feld "Mobiltelefon" dieses Users dynamisch ändern.*

### C. API Credentials erstellen (XAPI)
1.  Gehen Sie in der 3CX Konsole auf **Admin** > **Integrations** > **API**.
2.  Klicken Sie auf **Generate New** (oder ähnlich).
3.  Notieren Sie sich:
    - **Client ID**
    - **Client Secret**
    - Ihre 3CX URL (z.B. `https://my-company.3cx.eu`)

## 2. Server/Scheduler Konfiguration

Bearbeiten Sie die `.env` Datei auf Ihrem Server und tragen Sie die Werte ein:

```properties
# 3CX Integration (Push / XAPI)
CX_TENANT_URL=https://my-company.3cx.eu
CX_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
CX_CLIENT_SECRET=yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
CX_DUMMY_EXT=999
CENTRAL_NUMBER=200
```
*(Die `CENTRAL_NUMBER` ist die Fallback-Nummer, falls kein Notdienstplan aktiv ist. Diese wird dann als Mobilnummer beim Dummy-User eingetragen).*

## 3. Deployment

Starten Sie den Scheduler neu, damit die Änderungen wirksam werden:

```bash
docker-compose up -d --build scheduler
```

## 4. Testen
1.  Erstellen Sie einen aktiven Notfallplan für "Max Mustermann" (Mobil: 0171-12345).
2.  Warten Sie ca. 1 Minute (Scheduler Interval).
3.  Prüfen Sie die Logs: `docker logs emergency-scheduler`.
    - Meldung: `[3CX] Successfully updated mobile number.`
4.  Prüfen Sie in der 3CX Konsole beim User 999:
    - Das Feld "Mobilnummer" sollte jetzt `0171-12345` sein.
5.  Rufen Sie die Nummer 999 an -> Sie sollten bei Max Mustermann landen.
