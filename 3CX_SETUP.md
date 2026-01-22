# 3CX Notfall-Routing Einrichten (CFD Methode)

Dieser Guide erklärt, wie Sie die 3CX Telefonanlage so konfigurieren, dass sie eingehende Anrufe basierend auf dem aktuellen IT-Notfallplan automatisch weiterleitet.

## 1. Konzept (Pull vs. Push)
Wir verwenden die "Pull"-Methode. Das bedeutet, die 3CX "fragt" bei jedem Anruf unser System: *"Wer hat gerade Dienst?"*.

1.  Anruf geht an eine "Dummy" Nebenstelle / digitale Rezeption (die von CFD gesteuert wird).
2.  CFD App macht einen **HTTP GET Request** an unseren Backend-Server.
3.  Backend antwortet mit der Handynummer des Diensthabenden.
4.  CFD leitet den Anruf an diese Nummer weiter (oder an die Zentrale, falls niemand Dienst hat).

## 2. Backend Vorbereitung

Stellen Sie sicher, dass das Backend läuft und der neue Endpunkt erreichbar ist.

- **URL:** `https://<ihr-backend-server>:8001/integration/routing`
- **Authentifizierung:** via Header `X-API-Key`
- **Standard Key:** `secret-cx-key` (Änderbar in `.env`: `CX_API_KEY`)

**Testen Sie den Endpunkt:**
```bash
curl -k -H "X-API-Key: secret-cx-key" https://localhost:8001/integration/routing
```
**Antwort (Beispiel):**
```json
{
  "status": "active_plan",
  "destination_number": "01712345678",
  "source": "plan",
  "display_name": "Max Mustermann"
}
```

## 3. Call Flow Designer (CFD) App Erstellen

Laden Sie den [3CX Call Flow Designer](https://www.3cx.com/docs/manual/call-flow-designer-installation/) herunter.

### Schritte im CFD:

1.  **Neues Projekt:** `File > New Project` -> Name: `EmergencyRouting`.
2.  **HTTP Request Komponente hinzufügen:**
    - Ziehen Sie eine `HTTP Request` Komponente in den Main Flow.
    - **Properties:**
        - `Uri`: `"https://<ihr-backend-host>:8001/integration/routing"`
        - `Method`: `GET`
        - `Headers`: Klicken Sie auf den '...' Button und fügen Sie hinzu:
            - Key: `X-API-Key`
            - Value: `"secret-cx-key"` (oder Ihr Key)
    - **Wichtig:** Da wir ein selbst-signiertes Zertifikat nutzen, muss in 3CX ggf. die Validierung deaktiviert werden oder das Root-CA importiert werden. In älteren Versionen gibt es dafür keine Option, dann muss ein offizielles Zertifikat (Let's Encrypt) verwendet werden. Für Tests: curl mit `-k`.
3.  **JSON Response Parsen:**
    - Verwenden Sie die `JsonParser` Komponente oder via C# Script `JsonConvert.DeserializeObject`.
    - Extrahieren Sie `destination_number` aus der Antwort.
4.  **Bedingte Weiterleitung (Transfer):**
    - Ziehen Sie eine `Create a Condition` Komponente.
    - **Branch 1 (Diensthabender gefunden):**
        - Condition: `destination_number != ""`
        - Action: `Transfer` Komponente -> `Destination`: `destination_number`.
    - **Branch 2 (Fallback / Kein Dienst):**
        - Condition: `Else`
        - Action: `Transfer` Komponente -> `Destination`: z.B. `"200"` (Zentrale) oder Mailbox.

## 4. App in 3CX Hochladen

1.  Compilieren Sie das Projekt im CFD (`Build > Build`).
2.  Login in 3CX Verwaltungskonsole -> **Erweitert** -> **Call Flow Apps**.
3.  `Hinzufügen/Update` und wählen Sie die compilierte Archive-Datei (.zip).
4.  Geben Sie der App eine interne Nummer (z.B. **999**).

## 5. Eingehende Anrufe Routen

1.  Gehen Sie zu **Eingehende Regeln** (Inbound Rules) oder **SIP Trunks**.
2.  Wählen Sie die Hauptnummer/Notfallnummer.
3.  Setzen Sie das Ziel ("Leiten an") auf **Call Flow Apps** -> **EmergencyRouting (999)**.

Fertig! Jetzt wird jeder Anruf dynamisch geroutet.
