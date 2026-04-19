# Selena Translator

A standalone, Dockerised translation service with a Bootstrap web UI.

- **Argos Translate** backend — install / uninstall language pairs, translate text in-browser.
- **Helsinki-NLP model converter** — fetch an `opus-mt` model from HuggingFace, convert it to CTranslate2 int8 and package it as a `.tar.gz` archive that [SelenaCore](https://github.com/dotradepro/SelenaCore) can consume directly.
- Dark / light theme toggle, EN / UK UI.

> **Ukrainian version below / Українська версія нижче.**

---

## Quickstart

```bash
curl -fsSL https://raw.githubusercontent.com/dotradepro/selena-translator/main/install.sh | bash
```

The installer clones the repo to `~/selena-translator`, builds the image, starts the container on port **8002**, and drops a desktop shortcut.

Open <http://localhost:8002> once the container is healthy.

### Manual install

```bash
git clone https://github.com/dotradepro/selena-translator.git
cd selena-translator
sudo docker compose up -d --build
```

If your user is in the `docker` group you can drop `sudo`.

### Reusing existing Argos language packs

`docker-compose.yml` volume-mounts `~/.local/share/argos-translate/packages` into the container. Packs installed on the host are available immediately inside the service — no re-download.

---

## Features

### Translate tab

- Pick source and target languages from everything Argos has installed.
- Swap languages, paste text, press **Translate**.
- **Manage language packs** modal installs or removes any Argos pack from the online index.

### Helsinki Converter tab

- Built-in catalog of vetted `opus-mt-tc-big-*` and legacy `opus-mt-*` models (East Slavic, Germanic, Romance, Slavic, Turkic).
- Pick a catalog entry or enter any custom HuggingFace repo ID (e.g. `Helsinki-NLP/opus-mt-en-fr`).
- Multi-target models (e.g. `opus-mt-tc-big-en-zle`) take an optional language token (`>>ukr<<`, `>>rus<<`, `>>deu<<`, …) that is baked into the archive metadata.
- Live job log + download link when the archive is ready.

### Archive layout

The converter produces `.tar.gz` archives whose extracted root contains exactly:

```
model.bin       — CTranslate2 weights
source.spm      — SentencePiece tokenizer (source side)
target.spm      — SentencePiece tokenizer (target side)
metadata.json   — { model_id, direction, language_token, quantization, converted_date }
```

This matches the `_layout_ok()` validator in SelenaCore's `core/translation/helsinki_translator.py`.

---

## API reference

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/health` | liveness probe |
| `GET`  | `/api/languages` | installed languages + pairs |
| `GET`  | `/api/packages/available` | Argos online index + installed flag |
| `POST` | `/api/packages/install` | install a pair `{ from, to }` |
| `DELETE` | `/api/packages/{from}-{to}` | uninstall a pair |
| `POST` | `/api/translate` | `{ text, from, to }` → `{ translation }` |
| `GET`  | `/api/helsinki/catalog` | curated HuggingFace opus-mt list |
| `POST` | `/api/helsinki/convert` | kick off a conversion job |
| `GET`  | `/api/helsinki/jobs/{id}` | poll status (`queued`, `running`, `done`, `error`) |
| `GET`  | `/api/helsinki/download/{id}` | download the produced archive |

Example:

```bash
curl -sX POST http://localhost:8002/api/translate \
  -H 'content-type: application/json' \
  -d '{"text":"Hello world","from":"en","to":"uk"}'
```

---

## Configuration

| Env var | Default | Purpose |
|---------|---------|---------|
| `HELSINKI_OUT_DIR` | `/app/data/helsinki-out` | where archives are stored |
| `HF_HOME` | `/root/.cache/huggingface` | HuggingFace download cache |

The container binds host port `8002`. To change it, edit `docker-compose.yml` or set `SELENA_TRANSLATOR_PORT` before running `install.sh`.

---

## Troubleshooting

- **`docker: permission denied`** — your user is not in the `docker` group. Either `sudo usermod -aG docker $USER` (log out/in) or keep using `sudo docker compose ...`.
- **Conversion fails with `ct2-transformers-converter: not found`** — the image was not rebuilt after a `requirements.txt` change. Run `sudo docker compose up -d --build`.
- **Port 8002 already in use** — change the host side of the port mapping in `docker-compose.yml` and restart.
- **Translation returns 400 `no translation pair installed`** — open the **Manage language packs** modal and install the pair, or `POST /api/packages/install`.

---

## Українська

Selena Translator — автономний контейнеризований сервіс перекладу з веб-інтерфейсом на Bootstrap.

- Бекенд **Argos Translate** — встановлення / видалення мовних пар, переклад у браузері.
- **Конвертер моделей Helsinki-NLP** — завантажує модель `opus-mt` з HuggingFace, конвертує її у CTranslate2 int8 та пакує у `.tar.gz` архів, сумісний із SelenaCore.
- Перемикач темної / світлої теми, інтерфейс EN / UK.

### Швидкий старт

```bash
curl -fsSL https://raw.githubusercontent.com/dotradepro/selena-translator/main/install.sh | bash
```

Інсталятор клонує репо у `~/selena-translator`, будує образ, запускає контейнер на порту **8002** і створює ярлик на робочому столі.

Відкрийте <http://localhost:8002>, коли контейнер буде готовий.

### Вкладка «Переклад»

- Оберіть вихідну й цільову мови з усіх встановлених Argos-пакетів.
- Поміняйте мови місцями, вставте текст, натисніть **Перекласти**.
- Модальне вікно **Керувати мовними пакетами** встановлює або видаляє будь-який пакет із онлайн-індексу Argos.

### Вкладка «Конвертер Helsinki»

- Вбудований каталог перевірених моделей `opus-mt-tc-big-*` (Східнослов'янські, Германські, Романські, Слов'янські, Тюркські).
- Оберіть запис із каталогу або введіть будь-який HuggingFace repo ID.
- Для мульти-таргет моделей вкажіть мовний токен (`>>ukr<<`, `>>rus<<`, `>>deu<<` тощо) — він буде записаний у метадані архіву.
- Живий журнал завдання та посилання для завантаження архіву після завершення.

### Використання архіву в SelenaCore

1. Запустіть конвертацію (наприклад, `en-uk`, `Helsinki-NLP/opus-mt-tc-big-en-zle`, токен `>>ukr<<`).
2. Завантажте готовий `.tar.gz`.
3. У SelenaCore → **Налаштування → Переклад → Helsinki** завантажте архів.
4. SelenaCore перевірить макет (`model.bin` + `source.spm` + `target.spm`) і активує пару.

### Ліцензія

MIT — див. `LICENSE`.
