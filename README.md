<p align="center">
  <img src="assets/logo.svg" width="160" alt="THOT logo: ibis-headed god crowned by the moon, writing a sound wave">
</p>

<h1 align="center">THOT</h1>

<p align="center"><em>Trascrizione vocale offline — dal suono alla scrittura.</em></p>

Thot, dio egizio dalla testa di ibis, era lo scriba degli dèi: ascoltava e metteva per iscritto.
**THOT** fa lo stesso con i tuoi file audio, interamente in locale.

- **Trascrizione batch** di file e cartelle con [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (CPU o GPU CUDA)
- **Riconoscimento parlanti** leggero (MFCC + clustering), etichette coerenti su tutto il file
- **Uscite** `txt`, `srt`, `vtt`, `json`
- **Dettatura live** dal microfono con [Vosk](https://alphacephei.com/vosk/)
- **Interfaccia grafica** PyQt5 con drag & drop, avanzamento, annullamento
- **Correzione grammaticale** opzionale (modello T5, solo inglese)

## Installazione

Requisiti: Python ≥ 3.9. FFmpeg di sistema non è necessario (la decodifica usa PyAV).

```bash
git clone https://github.com/gc10code/thot.git
cd thot
scripts/install.sh            # crea .venv e installa con GUI + live
source .venv/bin/activate
```

Su Windows: `scripts\install.bat`. Installazione manuale con gli extra desiderati:

```bash
pip install -e ".[gui,live]"      # extra: gui, live, grammar, all, dev
```

## Uso

### Trascrizione

```bash
thot transcribe intervista.mp3                       # → transcripts/intervista.txt
thot transcribe registrazioni/ -o out -f srt -f txt  # intera cartella, più formati
thot transcribe riunione.m4a -s 3 -m medium          # 3 parlanti, modello medium
thot transcribe talk.mp4 -l auto -d cuda             # lingua automatica, GPU
```

| Opzione | Descrizione | Default |
|---|---|---|
| `-o, --output` | cartella di uscita | `transcripts` |
| `-m, --model` | `tiny` `base` `small` `medium` `large-v3` `turbo` | `small` |
| `-l, --language` | codice lingua (`it`, `en`, …) o `auto` | `it` |
| `-d, --device` | `auto` `cpu` `cuda` | `auto` |
| `-f, --format` | `txt` `srt` `vtt` `json` (ripetibile) | `txt` |
| `-s, --speakers N` | etichetta N parlanti (0 = disattivo) | `0` |
| `-g, --grammar` | correzione grammaticale T5 (inglese) | off |
| `-r, --recursive` | cerca nelle sottocartelle | off |
| `--no-vad` | disattiva il filtro di attività vocale | — |

I modelli Whisper vengono scaricati automaticamente al primo uso.

### Interfaccia grafica

```bash
thot gui        # oppure: thot-gui
```

<p align="center"><img src="assets/screenshot.png" width="640" alt="THOT GUI"></p>

### Dettatura live

```bash
scripts/download_vosk_model.sh        # modello italiano piccolo (48 MB) in models/
thot live                             # parla; Ctrl+C per terminare
thot live -o appunti.txt -i 2         # salva su file, usa il dispositivo d'ingresso 2
thot live --list-devices
```

Il modello si sceglie con `-M <cartella>` o con la variabile `THOT_VOSK_MODEL`. Vedi [models/README.md](models/README.md).

## Struttura

```
src/thot/
├── config.py            costanti ed enum condivisi
├── core/                motore, senza dipendenze da interfaccia
│   ├── audio.py         decodifica (PyAV) e ricerca file
│   ├── transcriber.py   pipeline Whisper con progresso e annullamento
│   ├── diarization.py   etichettatura parlanti
│   ├── grammar.py       correzione T5 (caricata solo se usata)
│   ├── formatters.py    txt / srt / vtt / json
│   └── models.py        Segment, Transcript
├── cli/                 `thot transcribe | live | gui`
├── gui/                 finestra PyQt5 e worker in thread separato
└── resources/           icona e foglio di stile
```

## Sviluppo

```bash
pip install -e ".[dev]"
pytest
```

## Licenza

[MIT](LICENSE)
