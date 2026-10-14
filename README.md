# 🚗 AutoService-Bot: Telegram-бот для автосервиса

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-v3.x-green?logo=telegram)](https://docs.aiogram.dev/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue?logo=docker)](https://www.docker.com/)
[![Redis](https://img.shields.io/badge/Redis-7-red?logo=redis)](https://redis.io/)
[![Baserow](https://img.shields.io/badge/Baserow-CRM-orange)](https://baserow.io/)

**AutoService-Bot** — это асинхронный Telegram-бот для автоматизации записи клиентов в автосервис «Восток». Бот не только записывает на ТО, но и выступает в роли умного помощника: проводит ИИ-диагностику по тексту, голосу и фото, а также позволяет отслеживать статус ремонта в реальном времени.

Бот интегрирован с CRM **Baserow** для хранения записей и использует **Polza.ai** для мультимодального анализа неисправностей.

---

## 🛠 Как это работает

```text
[Пользователь (Telegram)]
       │
       ▼
[Бот (aiogram v3)] ──────► [FSM Состояния (BookingStates, AIDiagnosticStates)]
       │                         │
       │                         ▼
       ├─► [Baserow CRM] ◄───────┘ (Создание / Чтение записей)
       │      (Асинхронный клиент)
       │
       └─► [Polza.ai API] ◄─────── (Текст / Голос / Фото -> ИИ-Диагностика)
```
1. Запись на ТО: Пользователь выбирает дату и время. Бот проверяет занятость слотов через Baserow, собирает данные (имя, авто, проблема) и создает запись.

2. ИИ-диагностика: Пользователь отправляет текст, голосовое или фото. Бот распознает речь (Whisper), анализирует изображение и выдает структурированный ответ через GPT-4o-mini.

3. Статус ремонта: Бот находит последнюю запись клиента в CRM и отображает текущий статус.
