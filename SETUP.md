# Configurare lo Short giornaliero sul tuo account Claude

Guida per far girare questo sistema in automatico con il **tuo** account Claude, il **tuo**
canale YouTube e il **tuo** Cloudflare. Ogni giorno Claude sceglie una storia, scrive lo script,
genera il video, lo pubblica e risponde ai commenti. Ci vogliono circa 30-45 minuti, una volta sola.

Serve un abbonamento Claude (Pro va bene) e un account GitHub.

---

> **Canale condiviso (2 Short al giorno).** Se pubblichi sul canale di qualcun altro insieme a
> lui: non fare il fork, fatti aggiungere come **collaboratore** al suo repository (così
> `topics.md` è unico e non escono storie doppie); per YouTube fatti aggiungere come **gestore**
> del suo Brand Account e al punto 4 scegli il **suo** canale; gli Short escono alle 14:00 e
> alle 18:00 (`--slot auto` sceglie lo slot libero): nel punto 7 fai partire il task prima di uno dei due
> (es. 12:12 o 15:37). Salta il punto 1.

## 1. La tua copia del repository

1. Apri la pagina GitHub del progetto e premi **Fork**. Un repo **privato** va benissimo.
2. Nella tua copia svuota `topics.md` e lascia solo l'intestazione, così Claude non salta
   argomenti che non hai mai fatto.

## 2. Collega GitHub a Claude

1. Su https://claude.ai/code collega il tuo account GitHub.
2. Installa la **Claude GitHub App** sul tuo fork:
   https://github.com/apps/claude/installations/select_target

## 3. Cloudflare (immagini, gratis)

1. Crea un account su https://dash.cloudflare.com.
2. Copia il tuo **Account ID**: lo trovi nella home del dashboard, colonna di destra,
   oppure nell'URL.
3. **My Profile → API Tokens → Create Token**, modello **"Workers AI"**. Non impostare il filtro
   sugli indirizzi IP (le sessioni cloud cambiano IP: errore 9109). Copia il token.

La quota gratuita giornaliera basta per uno Short al giorno.

## 4. YouTube (pubblicazione e commenti)

1. Su https://console.cloud.google.com crea un progetto e attiva **YouTube Data API v3**.
2. **Schermata consenso OAuth**: tipo Esterno, aggiungi la tua email come utente di test,
   poi **pubblica l'app**. In modalità test il token scade dopo 7 giorni.
3. **Client → Crea client → App desktop**. Scarica il JSON e mettilo nella cartella del progetto
   sul tuo PC (non finisce su GitHub).
4. Sul tuo PC, nella cartella del progetto:
   ```
   pip install -r requirements.txt
   python publisher.py --auth
   ```
   Si apre il browser: scegli **il tuo canale**. A fine procedura il comando stampa il
   **refresh token**: copialo.
5. Dal JSON del punto 3 copia `client_id` e `client_secret`.

## 5. L'ambiente cloud

Su https://claude.ai/code apri le impostazioni degli ambienti e creane uno nuovo:

- **Nome:** `shorts-agent`
- **Repository:** il tuo fork
- **Rete:** limitata, con package manager consentiti, più questi host:
  ```
  api.cloudflare.com
  oauth2.googleapis.com
  www.googleapis.com
  github.com
  objects.githubusercontent.com
  release-assets.githubusercontent.com
  ```
  (gli ultimi tre servono a scaricare il modello della voce).
- **Variabili d'ambiente:**
  ```
  CLOUDFLARE_ACCOUNT_ID=<il tuo Account ID Cloudflare>
  YT_CLIENT_ID=<client_id>
  YT_CLIENT_SECRET=<client_secret>
  YT_REFRESH_TOKEN=<refresh token>
  ```
  `CLOUDFLARE_ACCOUNT_ID` è **obbligatoria**: senza, `images.py` si ferma con un errore.
  Scrivi i valori senza virgolette né spazi. `YT_REFRESH_TOKEN` deve venire dallo stesso client
  di `YT_CLIENT_ID` (altrimenti YouTube risponde `invalid_grant`).
- **Network secret** (credenziale gestita dal proxy) per l'host `api.cloudflare.com`:
  header `Authorization`, tipo `Bearer`, valore = il token Cloudflare del punto 3.
- **Script di setup:**
  ```bash
  if [ -d shorts-agent ]; then
    cd shorts-agent
    pip install -q -r requirements.txt
    python3 -c "import tts; tts.ensure_models()"
  fi
  ```
  Se il tuo fork ha un altro nome, sostituisci `shorts-agent` con quel nome.

Non incollare mai token o password in chat o nei file del repo: vanno solo nelle impostazioni
dell'ambiente.

## 6. Prova a mano

Apri una sessione Claude Code sul web con l'ambiente `shorts-agent` e il tuo fork, poi scrivi:

```
crea lo Short del giorno
```

Claude segue la "Daily routine" di `CLAUDE.md`. Alla fine ti manda il video e il link YouTube.
Se qualcosa non va, chiedi a Claude nella stessa sessione.

## 7. Automatizza (task programmato)

Nella stessa sessione chiedi a Claude:

> Crea un task programmato "Short giornaliero", ogni giorno alle 12:12 ora di Roma, modello
> Sonnet, sessione nuova a ogni esecuzione, con notifiche push, che esegua questo prompt:

Importante: nel task deve essere selezionato il **repository** (il tuo fork) e l'ambiente
`shorts-agent`. Se il task non ha il repository, lo Short viene pubblicato ma il push su GitHub
fallisce con errore 403 e `topics.md` non si aggiorna. Il modo più sicuro è creare il task
dall'interfaccia (claude.ai/code → Routine → Nuova) scegliendo lì repository e ambiente.
Per due Short al giorno crea un secondo task alle 15:37.

```
Crea lo Short del giorno per il canale YouTube.

Se il repository <tuo-utente>/<tuo-fork> non è già nella sessione, aggiungilo con add_repo
(access "push") e clonalo. Poi leggi CLAUDE.md nella radice del repository e segui per intero
la sezione "Daily routine": scegli un argomento nuovo non presente in topics.md, scrivi tu lo
script in examples/<slug>.json, genera il video con agent.py, controlla alcuni fotogrammi,
mandami mp4 e testo di caricamento con SendUserFile, pubblica con publisher.py --slot auto,
aggiorna topics.md, fai commit e push su main.

Concludi con 3-4 righe in italiano: titolo, durata, link YouTube, orario di uscita, primo
commento da fissare ed eventuali fatti da ricontrollare.
```

Sostituisci `<tuo-utente>/<tuo-fork>` con il tuo repository.

## Consumi e limiti

- Con il piano **Pro** una run usa indicativamente il 20-50% della finestra di 5 ore. Con
  **Sonnet** consuma molto meno che con Opus. Controlla su claude.ai → Impostazioni → Utilizzo.
- Cloudflare: se la quota gratuita del giorno è finita, lo Short viene saltato.
- YouTube: circa 6 caricamenti al giorno e 10.000 unità di quota (una risposta = 50 unità).

## Ogni giorno, a mano

- Fissa il primo commento in YouTube Studio → Commenti → ⋮ → **Fissa** (l'API non lo permette;
  Claude ti manda il link).
- Ricontrolla i fatti che Claude segnala come incerti.
