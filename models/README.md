# Vosk models

`thot live` looks here for offline Vosk models (not tracked by git).

| Model | Size | Notes |
|-------|------|-------|
| [vosk-model-small-it-0.22](https://alphacephei.com/vosk/models/vosk-model-small-it-0.22.zip) | 48 MB | default, fast |
| [vosk-model-it-0.22](https://alphacephei.com/vosk/models/vosk-model-it-0.22.zip) | 1.2 GB | more accurate |

Other languages: <https://alphacephei.com/vosk/models>.

```bash
scripts/download_vosk_model.sh                      # small Italian model
scripts/download_vosk_model.sh vosk-model-it-0.22   # any model name from the list
thot live -M models/vosk-model-it-0.22              # use a specific model
```
