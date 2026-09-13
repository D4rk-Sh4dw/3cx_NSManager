# SSO mit Authentik (OpenID Connect)

Das System kann sich per OpenID Connect an einen Identity Provider anbinden. Entwickelt und getestet gegen **Authentik**, es werden aber ausschließlich Standard-OIDC-Mechanismen verwendet (Discovery, Authorization Code Flow mit PKCE) — Keycloak, Entra ID oder Zitadel funktionieren genauso.

Ohne Konfiguration ist SSO aus und es bleibt beim lokalen Passwort-Login.

## Wie der Login abläuft

1. Benutzer klickt auf der Login-Seite auf **Anmelden mit Authentik**.
2. Das Backend erzeugt `state`, `nonce` und einen PKCE-Verifier, legt sie in einem signierten, httpOnly-Cookie ab und leitet zu Authentik weiter.
3. Nach der Anmeldung schickt Authentik den Benutzer an `/api/auth/oidc/callback` zurück.
4. Das Backend prüft `state`, tauscht den Code gegen Tokens, validiert das ID-Token (Signatur über JWKS, `iss`, `aud`, `exp`, `nonce`) und ermittelt das lokale Konto.
5. Das Backend stellt ein normales App-Token aus und legt es in ein Cookie mit 60 Sekunden Lebensdauer. Die Login-Seite holt es über `POST /api/auth/oidc/complete` ab und legt es wie beim Passwort-Login im `localStorage` ab.

Das Token steht damit nie in der URL und landet dadurch nicht in Browser-Verlauf, Proxy-Logs oder `Referer`-Headern.

## Kontenzuordnung

Beim Login sucht das Backend in dieser Reihenfolge:

1. **Nach `oidc_sub`** — der unveränderlichen Benutzer-ID aus Authentik. Greift bei jedem Login nach dem ersten.
2. **Nach E-Mail-Adresse** — trifft ein bestehendes Konto zu, wird es mit `oidc_sub` verknüpft. Rolle, Telefonnummer und ein eventuell vorhandenes lokales Passwort bleiben unverändert.
3. **Sonst wird ein neues Konto angelegt** aus `email`, `preferred_username`, `given_name`/`family_name`.

Neue Konten bekommen die Rolle aus `OIDC_DEFAULT_ROLE` (Default `planner`) und `can_take_duty=false`. Telefonnummer und Diensttauglichkeit setzt danach ein Admin in der Benutzerverwaltung.

> **Rollen kommen nicht aus Authentik.** Gruppen werden bewusst nicht gemappt — die Rolle wird nur beim Anlegen gesetzt und danach ausschließlich im Tool gepflegt. Ein Login überschreibt eine dort geänderte Rolle nie.

Verknüpfungen und Neuanlagen landen als `SSO_LINK` bzw. `SSO_CREATE` im Audit-Log.

## Authentik einrichten

### 1. Provider anlegen

In Authentik unter **Applications → Providers → Create → OAuth2/OpenID Provider**:

| Feld | Wert |
|---|---|
| Name | `Notfallservice Manager` |
| Authorization flow | `default-provider-authorization-explicit-consent` (oder implicit, wenn ohne Rückfrage) |
| Client type | **Confidential** |
| Client ID | wird generiert → `OIDC_CLIENT_ID` |
| Client Secret | wird generiert → `OIDC_CLIENT_SECRET` |
| Redirect URIs | `https://notfall.deine-firma.de/api/auth/oidc/callback` |
| Signing Key | ein RSA-Zertifikat auswählen (nicht leer lassen) |
| Scopes | `openid`, `profile`, `email` |

Die Redirect URI muss **exakt** stimmen, inklusive `https` und ohne abschließenden Slash.

### 2. Application anlegen

**Applications → Applications → Create**, den eben erstellten Provider auswählen und einen Slug vergeben, z.B. `notfallservice`. Über die Bindings der Application steuerst du, wer sich überhaupt anmelden darf — das ist die Zugangskontrolle, nicht die Rolle im Tool.

### 3. Issuer ablesen

Auf der Provider-Übersichtsseite steht unter **OpenID Configuration Issuer** die URL, die du als `OIDC_ISSUER` einträgst:

```
https://authentik.deine-firma.de/application/o/notfallservice/
```

Prüfen lässt sich das direkt:

```bash
curl -s https://authentik.deine-firma.de/application/o/notfallservice/.well-known/openid-configuration | head -c 300
```

## Konfiguration (`.env`)

```ini
OIDC_ISSUER=https://authentik.deine-firma.de/application/o/notfallservice/
OIDC_CLIENT_ID=...
OIDC_CLIENT_SECRET=...
# Leer lassen, dann wird ${APP_BASE_URL}/api/auth/oidc/callback verwendet
OIDC_REDIRECT_URL=
OIDC_SCOPES=openid profile email
OIDC_PROVIDER_NAME=Authentik    # Beschriftung des Buttons
OIDC_DEFAULT_ROLE=planner       # Rolle für neu angelegte Konten
OIDC_COOKIE_SECURE=true         # nur für lokale HTTP-Tests auf false
LOCAL_LOGIN_ENABLED=true        # Passwort-Login als Fallback
```

`APP_BASE_URL` muss gesetzt sein, wenn `OIDC_REDIRECT_URL` leer bleibt.

## Lokalen Login abschalten

`LOCAL_LOGIN_ENABLED=false` blendet das Passwortformular aus und lässt `POST /auth/token` mit `403` antworten.

> ⚠️ Erst umstellen, wenn du dich **einmal erfolgreich per SSO als Admin angemeldet** hast. Sonst sperrst du dich aus, sobald am Authentik-Setup etwas nicht stimmt. Zurückdrehen geht nur über die `.env` und einen Neustart des Backends.

Ein guter Ablauf: SSO aktivieren, mit dem eigenen Konto anmelden (es wird per E-Mail mit dem bestehenden Admin-Konto verknüpft), prüfen dass die Admin-Rolle erhalten geblieben ist, danach den lokalen Login abschalten.

## Datenbank

Beim Start ergänzt das Backend automatisch die Spalte `users.oidc_sub` und macht `users.password_hash` optional (SSO-Konten haben kein lokales Passwort). Die Migration läuft in `backend/init_db.py`, ist idempotent und lässt bestehende Daten unberührt.

## Fehlersuche

Die Login-Seite zeigt eine verständliche Meldung, die Details stehen im Backend-Log:

```bash
docker compose logs -f backend | grep OIDC
```

| Meldung auf der Login-Seite | Ursache |
|---|---|
| Der SSO-Anbieter ist nicht erreichbar | Discovery-Dokument nicht ladbar, oder `OIDC_ISSUER` falsch. Log zeigt auch einen Issuer-Mismatch, wenn die URL nicht zu der im Dokument passt |
| Die Anmeldung wurde vom SSO-Anbieter abgelehnt | Benutzer hat keine Berechtigung auf die Application, oder Zustimmung abgebrochen |
| Die Anmeldung hat zu lange gedauert | Mehr als 10 Minuten zwischen Klick und Rückkehr, oder Cookies blockiert |
| Die Anmeldung konnte nicht zugeordnet werden | `state` passt nicht — meist ein doppelt geöffneter Login-Tab |
| Dieses Konto ist deaktiviert | `is_active=false` im Tool |
| SSO-Anmeldung fehlgeschlagen | Sammelmeldung, echte Ursache im Log: Token-Exchange fehlgeschlagen (falsches Secret oder falsche Redirect URI), Signaturprüfung fehlgeschlagen, oder keine E-Mail in den Claims |

Zwei Fälle, die im Log konkret benannt werden:

* *"The provider returned no email address"* — der `email`-Scope fehlt am Provider, oder der Benutzer hat in Authentik keine E-Mail hinterlegt. Ohne E-Mail kann kein Konto angelegt werden.
* *"Account '…' is already linked to a different SSO identity"* — die E-Mail gehört zu einem Konto, das schon mit einer anderen Authentik-Identität verknüpft ist. Passiert, wenn ein Benutzer in Authentik neu angelegt wurde. Lösung: `oidc_sub` des betroffenen Kontos in der Datenbank leeren, dann verknüpft der nächste Login neu.

## Abmelden

Der Logout im Tool verwirft nur das lokale Token. Die Sitzung bei Authentik bleibt bestehen — ein erneuter Klick auf den SSO-Button meldet ohne Passwortabfrage wieder an. Das ist normales SSO-Verhalten. Wer sich vollständig abmelden will, tut das in Authentik selbst.
