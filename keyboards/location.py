from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

LATITUDE = 59.9372
LONGITUDE = 30.3130

# pt={lon},{lat},pm2rdm ставит красную круглую метку прямо на дом
# z=17 задает крупный масштаб (уровень дома)
yandex_url = f"https://yandex.ru/maps/?pt={LONGITUDE},{LATITUDE},pm2rdm&z=17&l=map"

# m={lon}%2C{lat}%2F17 открывает 2ГИС строго на точке с зумом 17
gis_url = f"https://2gis.ru/spb/geo/5348651268307283?m={LONGITUDE}%2C{LATITUDE}%2F17"

location_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📍 Яндекс Карты", url=yandex_url),
            InlineKeyboardButton(text="🧭 2ГИС", url=gis_url)
        ]
    ]
)
