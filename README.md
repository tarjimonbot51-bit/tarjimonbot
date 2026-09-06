# Translator Bot

Python 3.11+ va aiogram 3.13.1 asosidagi Telegram tarjimon bot. Bot tanlangan tillar orasida matn tarjima qiladi, tarix saqlaydi va admin broadcast/statistika paneliga ega.

## Imkoniyatlar

- 12 ta asosiy til va avtomatik manba tilini aniqlash
- SQLite + aiosqlite tarix va foydalanuvchilar bazasi
- FSM, Router, InlineKeyboardBuilder va ReplyKeyboardBuilder
- Tarjima API timeout, 1 marta retry va xotira cache
- Tarix pagination
- Admin statistika va rate-limitga mos broadcast
- `.env` orqali xavfsiz konfiguratsiya

## Tuzilma

```text
translator_bot/
├── bot.py
├── config.py
├── database.py
├── requirements.txt
├── .env.example
├── .gitignore
├── handlers/
├── keyboards/
├── services/
├── states/
└── utils/
```

## Translation API


Standart endpoint `https://api.mymemory.translated.net` bo‘lib, API key talab qilmaydi. Bu bepul servisning kunlik limitlari bor. Ko‘proq yuklama uchun LibreTranslate-compatible serverdan foydalanib, `.env`da `TRANSLATION_API_URL` va kerak bo‘lsa `TRANSLATION_API_KEY`ni o‘zgartiring. Masalan: `TRANSLATION_API_URL=http://localhost:5000`.

## Windows o‘rnatish

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env` faylida BotFather tokeni, Telegram admin IDsi va translation API sozlamalarini to‘ldiring. Tokenni BotFather’dan oling. Telegram IDni `@userinfobot` kabi bot orqali bilish mumkin.

## Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

## Ishga tushirish

```bash
python bot.py
```

Birinchi `/start` foydalanuvchini bazaga qo‘shadi. `🌐 Tarjima qilish` orqali matn yuboring, `🔄 Tilni tanlash` orqali yo‘nalishni sozlang.

## Muammolarni hal qilish

- `BOT_TOKEN is not configured`: `.env` yarating va tokenni kiriting.
- `ADMIN_ID must be an integer`: faqat raqamli Telegram ID kiriting.
- Translation API xatosi: API URL, internet, API key va server limitlarini tekshiring.
- `ModuleNotFoundError`: virtual muhit yoqilganini va `pip install -r requirements.txt` bajarilganini tekshiring.
- Bot javob bermasa: token to‘g‘ri ekanini va boshqa polling jarayoni ishlamayotganini tekshiring.

Bot API yoki translation API sababli xatolarni loglaydi, lekin foydalanuvchining matni, tokeni va API keyini loglamaydi.
