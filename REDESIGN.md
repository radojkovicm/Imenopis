# Imenolom Next

Nova UI verzija projekta `imenolom`, izdvojena iz originalnog foldera radi bezbednog poređenja.

## Šta je unapređeno

- uveden jedinstven vizuelni sistem (tamna data-editorial paleta, tokeni, kartice i jasna tipografija)
- početna strana je pretvorena u istraživački dashboard sa tri jasna ulaza i brzom pretragom
- poboljšani responsive layout, keyboard focus, hover states i reduced-motion ponašanje
- postojeći FastAPI API, SQLite baza, vanilla JS moduli i rute ostaju kompatibilni
- originalni projekat nije menjan

## Pokretanje

```powershell
cd C:\Users\KATA\Documents\Python\imenolom-next
py -3 -m uvicorn src.api.main:app --reload --port 8001
```

## Analiza početnog stanja

Originalni folder sadrži 137 fajlova: 44 Python modula, 9 JavaScript fajlova, 8 HTML stranica, normalizovane CSV podatke, 5 XLSX izvora, PDF izvor i SQLite bazu. Backend je funkcionalno bogat; najveći prostor za napredak bio je u vizuelnoj hijerarhiji i konzistentnosti interfejsa.

Napomena: početni test-suit trenutno pada tokom kolekcije zbog postojeće SQLite baze bez tabele `historical_name_attestation`; to je zaseban problem inicijalizacije/migracije podataka, nevezan za UI redizajn.
