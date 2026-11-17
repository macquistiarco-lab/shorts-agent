# Shorts agent

Da un argomento a uno YouTube Short finito, in inglese (1080x1920, circa 50 secondi).

| Passaggio | Strumento |
|---|---|
| Script, prompt immagini, effetti, titolo e descrizione | Claude (`claude-opus-5-5`) |
| Immagini | Cloudflare Workers AI, `flux-2-klein-9b` (gratis entro il limite giornaliero) |
| Voce | Kokoro `am_michael` (gira sul tuo PC, gratis, ok per canali monetizzati) |
| Effetti sonori | generati da zero (whoosh, colpi, tensione, tick) |
| Montaggio | ffmpeg: zoom lenti, sottotitoli con numeri in giallo, scritta d'apertura |

## Installazione (una volta sola)

1. **Installa Python 3.10 o più recente** da https://www.python.org/downloads/
   (su Windows spunta "Add Python to PATH" durante l'installazione).
2. **Installa ffmpeg.** Su Windows apri il Prompt dei comandi e scrivi:
   ```
   winget install ffmpeg
   ```
   Su Mac: `brew install ffmpeg`.
3. **Scarica questo progetto:** sulla pagina GitHub del repository premi il pulsante verde
   **Code**, poi **Download ZIP**, ed estrai lo zip in una cartella.
4. **Apri un terminale in quella cartella** (su Windows: apri la cartella, scrivi `cmd` nella
   barra dell'indirizzo e premi Invio) e installa le librerie:
   ```
   pip install -r requirements.txt
   ```
5. **Chiavi.** Imposta queste due variabili (su Windows, nel Prompt dei comandi):
   ```
   setx ANTHROPIC_API_KEY "la-tua-chiave-anthropic"
   setx CLOUDFLARE_API_TOKEN "il-tuo-token-cloudflare"
   ```
   Poi chiudi e riapri il terminale.
   - La chiave Anthropic si crea su https://console.anthropic.com (API Keys). Serve solo se
     vuoi che sia Claude a scrivere lo script.
   - Il token Cloudflare si crea su dash.cloudflare.com: My Profile, API Tokens, Create Token,
     modello "Workers AI".

Il modello della voce (circa 350 MB) **si scarica da solo** la prima volta che crei uno Short.

## Uso

```
python agent.py "Nick Leeson and the fall of Barings Bank"
```

Altri modi:
- `python agent.py --script examples/barings.json` usa uno script già pronto (niente chiave Anthropic).
- `python agent.py --resume output/barings` rimonta il video dopo che hai modificato
  `script.json` o cancellato un'immagine da `img/`.

Il risultato è in `output/<nome>/`: il video `short_<nome>.mp4` e il file
`short_<nome>_upload.txt` con titolo, descrizione e hashtag.

Prima di pubblicare: guarda il video, ricontrolla i fatti e in YouTube Studio segna
"Contenuti alterati o sintetici" (le immagini IA sono realistiche).

## Pubblicare su YouTube (`publisher.py`)

Il secondo agente prende gli Short in `output/`, prepara titolo, descrizione e hashtag
(`#shorts` + hashtag della storia + hashtag del canale, max 12) e li carica sul tuo canale,
segnando già "Contenuti alterati o sintetici".

**Una volta sola:**
1. Su https://console.cloud.google.com crea un progetto, attiva **YouTube Data API v3**.
2. "Schermata consenso OAuth": tipo Esterno, aggiungi la tua email come utente di test,
   poi **pubblica l'app** (in modalità test il token scade dopo 7 giorni).
3. "Client" → Crea client → tipo **App desktop** → scarica il JSON e mettilo nella cartella del
   progetto (`client_secret_....json`, non finisce su GitHub).
4. Lancia `python publisher.py --auth`: si apre il browser, scegli il canale. Il token viene
   salvato in `youtube_token.json` (anche lui fuori da GitHub) e stampato a schermo.
5. Per la routine nel cloud: metti `YT_CLIENT_ID`, `YT_CLIENT_SECRET` (dal JSON) e
   `YT_REFRESH_TOKEN` nelle variabili dell'ambiente `shorts-agent`.

**Uso:**
```
python publisher.py output/barings --dry-run   # solo anteprima di titolo/descrizione/tag
python publisher.py output/barings             # pubblica
python publisher.py --all                      # pubblica tutti quelli non ancora pubblicati
python publisher.py output/barings --at 2026-11-18T17:00:00Z   # programma l'uscita
```
Dopo il caricamento trovi `output/<nome>/youtube.json` con il link: lo stesso Short non
viene mai caricato due volte. Limite API: circa 6 caricamenti al giorno (quota gratuita).
