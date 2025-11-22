import os
import sys
import asyncio
import requests
import json
import logging
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import time as _time
import threading

from telegram import Update, Message, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, request

# Azerbaijani translations
TRANSLATIONS = {
    # Welcome and menu
    "welcome_title": "🏎️ F1 Canlı Botuna Xoş Gəlmisiniz! (Leapcell Test)",
    "welcome_text": """🏁 Sizin Formula 1 üçün ən yaxşı yoldaşınız - real vaxt yarış məlumatları, sıralamalar və canlı vaxt məlumatları.

*Edə biləcəyiniz:*
🏆 Cari çempionat sıralamalarını yoxlayın
🏎️ Son nəticələri alın
📅 Gələn yarış cədvəllərini və hava proqnozunu (Bakı vaxtı ilə) görün
🔴 Canlı vaxtı izləyin
🎦 Yayım linklərini görün""",
    "menu_title": "🏎️ F1 Bot Menyusu",
    "menu_text": "Aşağıdakı variantlardan birini seçin:",
    "help_title": "🏎️ F1 Canlı Bot Köməyi (Leapcell Test)",
    "help_commands": """*Əsas Əmrlər:*
• /standings - Cari sürücü sıralamaları
• /constructors - Cari konstruktor sıralamaları
• /lastrace - Son sessiya nəticələri
• /nextrace - Gələn yarış cədvəli hava proqnozu ilə
• /live - Canlı yarış mövqeləri
• /streams - Mövcud yayımları görün
• /addstream Ad | URL - Yayım əlavə edin
• /removestream <nömrə> - Yayımı silin
• /playstream <nömrə|URL> - Yayım linkini alın
• /streamhelp - Yayım köməyi

• /menu - Düymə menyusunu göstər""",
    "help_usage": """*Məlumat İstifadəsi:* ~2-5 KB hər sorğu 📱

*İstifadə olunan API-lər:*
• Jolpica F1 API (sıralamalar, cədvəl)
• OpenF1 API (canlı vaxt, sessiya nəticələri)
• Open-Meteo (hava proqnozları)
• Formula Timer (canlı vaxt scraper)""",

    # Buttons
    "driver_standings": "🏆 Sürücü Sıralamaları",
    "constructor_standings": "🏁 Konstruktor Sıralamaları",
    "last_session": "🏎️ Son Sessiya Nəticələri",
    "schedule_weather": "📅 Cədvəl & Hava",
    "live_timing": "🔴 Canlı Vaxt",
    "streams": "▶️ Yayımlar",
    "help_commands_btn": "ℹ️ Kömək & Əmrlər",

    # Standings
    "season_driver_standings": " Pilotların Çempionat Sıralaması",
    "season_constructor_standings": "*Konstruktorların Çempionat Sıralaması- {}*",
    "points": "xal",

    # Race results
    "qualifying": "Təsnifat",
    "sprint": "Sprint",
    "race": "Yarış",
    "winner": " - Qalib",
    "fastest_lap": "Ən Sürətli Dövrə: {} ({})",

    # Schedule
    "next_race": "🏎️ *Gələn Yarış*",
    "fp1": "FP1",
    "fp2": "FP2",
    "fp3": "FP3",
    "sprint_qualifying": "Sprint Təsnifatı",
    "qualifying": "Təsnifat",
    "race": "Yarış",
    "all_times_baku": "_Bütün vaxtlar Bakı vaxtı ilə_",
    "season_completed": "🏁 Mövsüm tamamlandı! Bu il üçün daha yarış yoxdur.",

    # Weather
    "weather_forecast": "🌤️ Hava Proqnozu üçün {}",
    "friday": "Cümə",
    "saturday": "Şənbə",
    "sunday": "Bazar",
    "race_day": "Bazar (Yarış)",
    "weather_unavailable": "🌦️ Bu yer üçün hava məlumatları mövcud deyil.",

    # Live timing
    "no_live_data": "❌ Canlı vaxt məlumatları mövcud deyil\n\nSon nəticələr üçün /lastrace istifadə edin",
    "optimized_error": "❌ Optimallaşdırılmış scraper xətası: {}\n\nSon nəticələr üçün /lastrace istifadə edin",
    "scraper_error": "❌ Xəta: {}\n\nSon nəticələr üçün /lastrace istifadə edin",
    "live_not_available": "❌ Canlı vaxt mövcud deyil\n\nchromium quraşdırmaq üçün: pip install playwright && playwright install chromium",

    # Streams
    "available_streams": "🎦 *Mövcud Yayımlar*",
    "tap_to_open": "Açmaq üçün toxunun:",
    "no_streams": "❌ Yayım yoxdur.\n\nƏlavə: /addstream Ad | URL",
    "stream_added": "✅ Əlavə edildi: {}\n\n/streams istifadə edin",
    "stream_removed": "✅ Yayım '{}' uğurla silindi!",
    "stream_error": "❌ Səhv",
    "stream_help_title": "🎦 Yayım Köməyi",
    "stream_help_best": "*Ən Yaxşı: .m3u8 URL-lər*\n• Birbaşa video yayımı\n• Reklam yoxdur\n• VLC Player-də açın",
    "stream_help_how": "*Necə istifadə etmək:*\n1. Əlavə: /addstream Ad | URL\n2. Görün: /streams\n3. Açmaq üçün toxunun",
    "stream_help_vlc": "💡 .m3u8 faylları üçün VLC istifadə edin!",
    "playstream_usage": "İstifadə:\n/playstream <nömrə> - Yayım linkini alın\n/playstream <URL> - Birbaşa link",
    "direct_stream": "Birbaşa Yayım",
    "copy_open_vlc": "💡 Kopyalayın və VLC Player-də açın",

    # F1-themed loading messages
    "loading_pitstop": "🏎️ Pit stop gedir...",
    "loading_formationlap": "🏁 Formation lap başlayır...",
    "loading_racecontrol": "📻 Race Control ilə əlaqə...",
    "loading_telemetry": "📊 Telemetriya məlumatları yüklənir...",
    "loading_timing": "⏱️ Vaxt sistemi sinxronizasiya olunur...",
    "loading_weather": "🌪️ Hava şəraiti yoxlanılır...",
    "loading_standings": "🏆 Çempionat sıralamaları yenilənir...",
    "loading_results": "🏁 Nəticələr təsdiqlənir...",
    "loading_streams": "🎦 Yayım siqnalları axtarılır...",
    "loading_parcferme": "🏁 Parc Fermé rejimi...",
    "loading_redflag": "🚩 Qırmızı bayraq dalğalanır...",
    "loading_safetycar": "🚨 Təhlükəsizlik maşını trasdadır...",

    # Errors
    "api_unavailable": "❌ Xidmət mənbəyi baxımdadır. Bir neçə dəqiqə sonra yenidən cəhd edin.",
    "no_standings": "❌ Bu mövsüm üçün sıralama məlumatları tapılmadı.",
    "no_driver_standings": "❌ Sürücü sıralamaları tapılmadı.",
    "invalid_data": "❌ Mənbədən yanlış məlumat format.",
    "no_constructor_standings": "❌ Konstruktor sıralamaları tapılmadı.",
    "no_sessions": "❌ Sessiya tapılmadı. API offline ola bilər.",
    "no_recent_sessions": "❌ Son tamamlanmış sessiyalar tapılmadı.",
    "no_results": "❌ Bu sessiya üçün nəticələr mövcud deyil.",
    "no_position_data": "❌ Bu sessiya üçün mövqe məlumatları mövcud deyil.",
    "no_final_positions": "❌ Bu sessiya üçün final mövqelər mövcud deyil.",
    "error_fetching_session": "❌ Sessiya nəticələrini almaqda xəta: {}",
    "error_fetching_race": "❌ Gələn yarış alınarkən xəta: {}",
    "weather_unavailable": "❌ Hava məlumatları mövcud deyil.",
    "error_fetching_weather": "❌ Hava məlumatları alınarkən xəta: {}",
    "service_unavailable": "❌ Xidmət müvəqqəti mövcud deyil. Daha sonra yenidən cəhd edin.",
    "error_occurred": "❌ Xəta baş verdi: {}",
    "unknown_command": "❌ Naməlum əmr",
    "loading": "⏳ Yüklənir...",
    "name_url_required": "❌ Ad və URL tələb olunur",
    "use_format": "❌ /addstream Ad | URL istifadə edin",
    "invalid_number": "❌ Yanlış nömrə. Yayım nömrələrini görmək üçün /streams istifadə edin.",
    "no_personal_streams": "❌ Şəxsi yayımlarınız yoxdur.",
    "invalid_number_range": "❌ Yanlış nömrə. Sizdə {} yayım var.",
    "error_saving": "❌ Saxlanılarkən xəta",
    "error_removing": "❌ Yayım silinərkən xəta. Yenidən cəhd edin.",
    "no_streams_found": "❌ Yayım tapılmadı",
    "invalid_input": "❌ Yanlış daxiletmə",
    "no_url": "❌ URL yoxdur",

    # Commands
    "usage_addstream": "İstifadə: /addstream Ad | URL\n\nNümunə:\n/addstream F1 Live | https://example.com/stream.m3u8",
    "usage_removestream": "İstifadə: /removestream <nömrə>\n\n/streams ilə yayım nömrələrini görün.",
    "invalid_removestream": "❌ Yanlış nömrə. /streams ilə yayım nömrələrini görün.",
    "invalid_playstream": "❌ Yanlış daxiletmə",

    # Bot startup
    "bot_starting": "F1 Bot başlayır (Leapcell Test)...",
    "bot_ready": "Bot hazırdır və yeniləmələr üçün gözləyir...\n✅ Leapcell containerized deployment\n✅ Web scraping optimized\n✅ Error handling enhanced",
    "bot_stopped": "\n👋 Bot istifadəçi tərəfindən dayandırıldı",
    "error_occurred_startup": "❌ Xəta baş verdi: {}",
    "token_not_set": "❌ Xəta: TELEGRAM_BOT_TOKEN təyin edilməyib!",
    "token_setup_instructions": """
📝 Bunlardan biri ilə təyin edin:

   Yerli İnkişaf üçün:
   • .env faylını redaktə edin və əlavə edin: TELEGRAM_BOT_TOKEN=your_token_here

   Hosting/İstehsalat üçün (Railway, Fly.io, Heroku, və s.):
   • Hosting platformasının dashboardunda mühit dəyişənini təyin edin
   • Dəyişən adı: TELEGRAM_BOT_TOKEN
   • Dəyər: your_bot_token

   Ümumi (əmr sətri):
   • Windows (PowerShell): $env:TELEGRAM_BOT_TOKEN='your_token'
   • Linux/Mac: export TELEGRAM_BOT_TOKEN='your_token'

   Tokeninizi Telegram-də @BotFather-dan alın: https://t.me/BotFather
""",
}

# F1-themed loading messages list
F1_LOADING_MESSAGES = [
    "loading_pitstop", "loading_parcferme", "loading_redflag",
    "loading_safetycar", "loading_formationlap", "loading_racecontrol",
    "loading_telemetry", "loading_timing", "loading_weather",
    "loading_standings", "loading_results", "loading_streams"
]

def get_f1_loading_message():
    """Get a random F1-themed loading message"""
    message_key = random.choice(F1_LOADING_MESSAGES)
    return TRANSLATIONS[message_key]

# ==================== IN-MEMORY CACHE SYSTEM ====================
# Shared cache for all users - prevents IP bans and reduces server load
LIVE_TIMING_CACHE = {
    'data': None,
    'timestamp': 0,
    'cache_duration': 15  # 15 seconds cache
}

def get_cached_live_timing():
    """Get live timing from cache or fetch new data"""
    current_time = _time.time()
    
    # Return cached data if still valid
    if (LIVE_TIMING_CACHE['data'] is not None and 
        current_time - LIVE_TIMING_CACHE['timestamp'] < LIVE_TIMING_CACHE['cache_duration']):
        return LIVE_TIMING_CACHE['data']
    
    # Fetch new data
    try:
        if OPTIMIZED_SCRAPER_AVAILABLE:
            data = get_optimized_live_timing()
        elif SCRAPER_AVAILABLE:
            data = scrape_formula_timer_live_timing()
        else:
            return None
            
        # Update cache
        LIVE_TIMING_CACHE['data'] = data
        LIVE_TIMING_CACHE['timestamp'] = current_time
        return data
    except Exception as e:
        logging.error(f"Cache fetch error: {e}")
        return LIVE_TIMING_CACHE['data']  # Return stale data if available

# Optimized scraper integration (with fallback to original)
try:
    from optimized_scraper import get_optimized_live_timing, format_timing_data_for_telegram
    OPTIMIZED_SCRAPER_AVAILABLE = True
except (ImportError, Exception) as e:
    OPTIMIZED_SCRAPER_AVAILABLE = False
    logging.warning(f"Optimized scraper not available: {e}")

# Fallback to original scraper
try:
    from final_working_scraper import scrape_formula_timer_live_timing
    SCRAPER_AVAILABLE = True
except (ImportError, Exception) as e:
    SCRAPER_AVAILABLE = False
    logging.warning(f"Final scraper not available: {e}")

# Optional modules (not required for core functionality)
# Note: These variables were unused and have been removed for cleaner code

# ==================== F1 DATA FUNCTIONS ====================

# Country to flag emoji mapping
COUNTRY_FLAGS = {
    "Mexico": "🇲🇽",
    "Mexico City": "🇲🇽",
    "USA": "🇺🇸",
    "United States": "🇺🇸",
    "Austin": "🇺🇸",
    "Miami": "🇺🇸",
    "Las Vegas": "🇺🇸",
    "Brazil": "🇧🇷",
    "UK": "🇬🇧",
    "United Kingdom": "🇬🇧",
    "Monaco": "🇲🇨",
    "Italy": "🇮🇹",
    "Imola": "🇮🇹",
    "Monza": "🇮🇹",
    "Spain": "🇪🇸",
    "Australia": "🇦🇺",
    "Netherlands": "🇳🇱",
    "France": "🇫🇷",
    "Germany": "🇩🇪",
    "Austria": "🇦🇹",
    "Canada": "🇨🇦",
    "Japan": "🇯🇵",
    "Singapore": "🇸🇬",
    "Bahrain": "🇧🇭",
    "Saudi Arabia": "🇸🇦",
    "Qatar": "🇶🇦",
    "UAE": "🇦🇪",
    "United Arab Emirates": "🇦🇪",
    "Abu Dhabi": "🇦🇪",
    "China": "🇨🇳",
    "Belgium": "🇧🇪",
    "Hungary": "🇭🇺",
    "Portugal": "🇵🇹",
    "Russia": "🇷🇺",
    "Turkey": "🇹🇷",
    "Azerbaijan": "🇦🇿",
    "Baku": "🇦🇿",
    "British": "🇬🇧",
    "Australian": "🇦🇺",
    "Dutch": "🇳🇱",
    "Monegasque": "🇲🇨",
    "Spanish": "🇪🇸",
    "Mexican": "🇲🇽",
    "German": "🇩🇪",
    "French": "🇫🇷",
    "Japanese": "🇯🇵",
    "Canadian": "🇨🇦",
    "Thai": "🇹🇭",
    "Finnish": "🇫🇮",
    "Chinese": "🇨🇳",
    "Danish": "🇩🇰",
    "American": "🇺🇸",
    "Austrian": "🇦🇹",
    "Italian": "🇮🇹",
    "Brazilian": "🇧🇷",
    "New Zealander": "🇳🇿",
    "Russian": "🇷🇺",
    "Polish": "🇵🇱",
    "Swiss": "🇨🇭",
    "South African": "🇿🇦",
    "Venezuelan": "🇻🇪",
    "Indonesian": "🇮🇩",
    "Argentine": "🇦🇷",
    # Country codes (for OpenF1 API) - IOC codes
    "NED": "🇳🇱",
    "GBR": "🇬🇧",
    "AUS": "🇦🇺",
    "MCO": "🇲🇨",
    "ESP": "🇪🇸",
    "MEX": "🇲🇽",
    "GER": "🇩🇪",
    "FRA": "🇫🇷",
    "JPN": "🇯🇵",
    "CAN": "🇨🇦",
    "THA": "🇹🇭",
    "FIN": "🇫🇮",
    "CHN": "🇨🇳",
    "DEN": "🇩🇰",
    "USA": "🇺🇸",
    "AUT": "🇦🇹",
    "ITA": "🇮🇹",
    "BRA": "🇧🇷",
    "NZL": "🇳🇿",
    "RUS": "🇷🇺",
    "POL": "🇵🇱",
    "CHE": "🇨🇭",
    "ZAF": "🇿🇦",
    "VEN": "🇻🇪",
    "IDN": "🇮🇩",
    "ARG": "🇦🇷",
    # ISO 3166-1 alpha-3 codes (alternative for OpenF1 API)
    "NLD": "🇳🇱",
    "DEU": "🇩🇪",
    "BEL": "🇧🇪",
    "PRT": "🇵🇹",
    "TUR": "🇹🇷",
    "AZE": "🇦🇿",
    "ARE": "🇦🇪",
    "QAT": "🇶🇦",
    "BHR": "🇧🇭",
    "SAU": "🇸🇦",
    "SGP": "🇸🇬",
    "HUN": "🇭🇺",
    # Additional nationality mappings (Ergast API format)
    "Argentinian": "🇦🇷",
    "Belgian": "🇧🇪",
    "Emirati": "🇦🇪",
    "Qatari": "🇶🇦",
    "Bahraini": "🇧🇭",
    "Saudi": "🇸🇦",
    "Singaporean": "🇸🇬",
    "Hungarian": "🇭🇺",
    "Portuguese": "🇵🇹",
    "Turkish": "🇹🇷",
    "Azerbaijani": "🇦🇿",
    "New Zealand": "🇳🇿",
    "Thailand": "🇹🇭",
    "Argentinian": "🇦🇷",
    "Colombian": "🇨🇴",
    # Additional country codes for OpenF1 API
    "NZL": "🇳🇿",
    "THA": "🇹🇭",
    "GBR": "🇬🇧",
    "AUS": "🇦🇺",
    "NED": "🇳🇱",
    "MCO": "🇲🇨",
    "ESP": "🇪🇸",
    "MEX": "🇲🇽",
    "GER": "🇩🇪",
    "FRA": "🇫🇷",
    "JPN": "🇯🇵",
    "CAN": "🇨🇦",
    "FIN": "🇫🇮",
    "CHN": "🇨🇳",
    "DEN": "🇩🇰",
    "AUT": "🇦🇹",
    "ITA": "🇮🇹",
    "BRA": "🇧🇷",
    "RUS": "🇷🇺",
    "POL": "🇵🇱",
    "CHE": "🇨🇭",
    "ZAF": "🇿🇦",
    "VEN": "🇻🇪",
    "IDN": "🇮🇩",
    "COL": "🇨🇴",
}

# Driver number to nationality mapping (2025 season)
DRIVER_NATIONALITIES = {
    1: "NED",   # Max Verstappen
    4: "GBR",   # Lando Norris
    5: "BRA",   # Gabriel Bortoleto
    6: "FRA",   # Isack Hadjar
    10: "FRA",  # Pierre Gasly
    12: "ITA",  # Kimi Antonelli
    14: "ESP",  # Fernando Alonso
    16: "MCO",  # Charles Leclerc
    18: "CAN",  # Lance Stroll
    22: "JPN",  # Yuki Tsunoda
    23: "THA",  # Alexander Albon
    27: "GER",  # Nico Hulkenberg
    30: "NZL",  # Liam Lawson
    31: "FRA",  # Esteban Ocon
    43: "ARG",  # Franco Colapinto
    44: "GBR",  # Lewis Hamilton
    55: "ESP",  # Carlos Sainz
    63: "GBR",  # George Russell
    81: "AUS",  # Oscar Piastri
    87: "GBR",  # Oliver Bearman
}

# Driver acronym to full name mapping
DRIVER_NAMES = {
    "VER": "Max Verstappen", "HAM": "Lewis Hamilton", "LEC": "Charles Leclerc",
    "SAI": "Carlos Sainz", "NOR": "Lando Norris", "PIA": "Oscar Piastri",
    "RUS": "George Russell", "STR": "Lance Stroll", "ALO": "Fernando Alonso",
    "OCO": "Esteban Ocon", "GAS": "Pierre Gasly", "TSU": "Yuki Tsunoda",
    "HUL": "Nico Hulkenberg", "MAG": "Kevin Magnussen", "BOT": "Valtteri Bottas",
    "ZHO": "Zhou Guanyu", "PER": "Sergio Perez", "RIC": "Daniel Ricciardo",
    "ALB": "Alexander Albon", "SAR": "Logan Sargeant", "LAW": "Liam Lawson",
    "BEA": "Oliver Bearman", "DOO": "Jack Doohan", "ANT": "Kimi Antonelli",
}

# Cache for driver data from Ergast API
_DRIVER_CACHE = {}

def get_driver_nationality_from_ergast(driver_name):
    """Get driver nationality from Ergast API by matching name"""
    global _DRIVER_CACHE
    
    # Return from cache if available
    if driver_name in _DRIVER_CACHE:
        return _DRIVER_CACHE[driver_name]
    
    try:
        now = datetime.now()
        season = now.year if now.month > 3 else now.year - 1
        
        apis = [
            f"https://api.jolpi.ca/ergast/f1/{season}/drivers.json"
        ]
        
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    drivers = data.get("MRData", {}).get("DriverTable", {}).get("Drivers", [])
                    
                    for driver in drivers:
                        given_name = driver.get("givenName", "")
                        family_name = driver.get("familyName", "")
                        full_name = f"{given_name} {family_name}"
                        nationality = driver.get("nationality", "")
                        
                        # Cache with multiple variations
                        _DRIVER_CACHE[full_name] = nationality
                        _DRIVER_CACHE[full_name.lower()] = nationality
                        # Cache by family name only (for partial matching)
                        _DRIVER_CACHE[family_name] = nationality
                        _DRIVER_CACHE[family_name.lower()] = nationality
                    
                    # Try exact match first
                    if driver_name in _DRIVER_CACHE:
                        return _DRIVER_CACHE[driver_name]
                    if driver_name.lower() in _DRIVER_CACHE:
                        return _DRIVER_CACHE[driver_name.lower()]
                    
                    # Try matching by last name only
                    parts = driver_name.split()
                    if len(parts) >= 2:
                        last_name = parts[-1]
                        if last_name in _DRIVER_CACHE:
                            return _DRIVER_CACHE[last_name]
                        if last_name.lower() in _DRIVER_CACHE:
                            return _DRIVER_CACHE[last_name.lower()]
                    
                    return ""
            except:
                continue
    except:
        pass
    
    return ""


def get_country_flag(nationality):
    """Get flag emoji for a nationality"""
    if not nationality:
        return "🏳️"

    nationality = nationality.strip()
    
    # Direct lookup (handles exact matches including 3-letter codes)
    if nationality in COUNTRY_FLAGS:
        return COUNTRY_FLAGS[nationality]
    
    # Try uppercase (for country codes like NED, GBR)
    if nationality.upper() in COUNTRY_FLAGS:
        return COUNTRY_FLAGS[nationality.upper()]
    
    # Try lowercase
    if nationality.lower() in COUNTRY_FLAGS:
        return COUNTRY_FLAGS[nationality.lower()]
    
    # Try title case
    if nationality.title() in COUNTRY_FLAGS:
        return COUNTRY_FLAGS[nationality.title()]
    
    # Partial match
    nationality_lower = nationality.lower()
    for key, flag in COUNTRY_FLAGS.items():
        if key.lower() in nationality_lower or nationality_lower in key.lower():
            return flag
    
    return "🏳️"


def to_roman(num):
    """Convert integer to Roman numeral"""
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syb = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
    ]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syb[i]
            num -= val[i]
        i += 1
    return roman_num


def get_race_points(position):
    """Get points for race position (F1 scoring system)"""
    points_map = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
    return points_map.get(position, 0)


def get_sprint_points(position):
    """Get points for sprint race position (F1 sprint scoring system)"""
    sprint_points_map = {1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1}
    return sprint_points_map.get(position, 0)


# Comprehensive F1 circuit coordinates for weather API
CIRCUIT_COORDS = {
    # Current F1 Circuits (2024-2025) - Official names
    "Bahrain International Circuit": (26.0325, 50.5106),
    "Jeddah Corniche Circuit": (21.6319, 39.1044),
    "Albert Park Circuit": (-37.8497, 144.9680),
    "Suzuka Circuit": (34.8431, 136.5410),
    "Shanghai International Circuit": (31.3389, 121.2197),
    "Miami International Autodrome": (25.9581, -80.2389),
    "Autodromo Enzo e Dino Ferrari": (44.3439, 11.7167),
    "Circuit de Monaco": (43.7347, 7.4206),
    "Circuit de Barcelona-Catalunya": (41.5699, 2.2570),
    "Circuit Gilles Villeneuve": (45.5000, -73.5228),
    "Red Bull Ring": (47.2197, 14.7647),
    "Silverstone Circuit": (52.0720, -1.0170),
    "Hungaroring": (47.5789, 19.2486),
    "Circuit de Spa-Francorchamps": (50.4372, 5.9714),
    "Circuit Zandvoort": (52.3888, 4.5409),
    "Autodromo Nazionale di Monza": (45.6190, 9.2816),
    "Marina Bay Street Circuit": (1.2914, 103.8632),
    "Baku City Circuit": (40.4093, 49.8671),
    "Circuit of the Americas": (30.1328, -97.6411),
    "Autodromo Hermanos Rodriguez": (19.4042, -99.0907),
    "Autodromo Jose Carlos Pace": (-23.7036, -46.6997),
    "Las Vegas Street Circuit": (36.1147, -115.1739),
    "Lusail International Circuit": (25.4888, 51.4543),
    "Yas Marina Circuit": (24.4672, 54.6031),

    # Alternative/common names for matching
    "Sakhir": (26.0325, 50.5106),
    "Jeddah": (21.6319, 39.1044),
    "Melbourne": (-37.8497, 144.9680),
    "Suzuka": (34.8431, 136.5410),
    "Shanghai": (31.3389, 121.2197),
    "Miami": (25.9581, -80.2389),
    "Imola": (44.3439, 11.7167),
    "Monaco": (43.7347, 7.4206),
    "Barcelona": (41.5699, 2.2570),
    "Montreal": (45.5000, -73.5228),
    "Spielberg": (47.2197, 14.7647),
    "Silverstone": (52.0720, -1.0170),
    "Budapest": (47.5789, 19.2486),
    "Spa": (50.4372, 5.9714),
    "Zandvoort": (52.3888, 4.5409),
    "Monza": (45.6190, 9.2816),
    "Singapore": (1.2914, 103.8632),
    "Baku": (40.4093, 49.8671),
    "Austin": (30.1328, -97.6411),
    "Mexico City": (19.4042, -99.0907),
    "Sao Paulo": (-23.7036, -46.6997),
    "Interlagos": (-23.7036, -46.6997),
    "Las Vegas": (36.1147, -115.1739),
    "Lusail": (25.4888, 51.4543),
    "Abu Dhabi": (24.4672, 54.6031),

    # Future/Potential F1 Circuits
    "Kyalami Grand Prix Circuit": (-25.9894, 28.0706),  # South Africa
    "Istanbul Park": (40.9517, 29.4058),  # Turkey
    "Hockenheimring": (49.3278, 8.5658),  # Germany
    "Nurburgring": (50.3356, 6.9475),  # Germany
    "Sepang International Circuit": (2.7608, 101.7381),  # Malaysia
    "Buddh International Circuit": (28.3487, 77.5331),  # India
    "Korea International Circuit": (34.7333, 126.4167),  # South Korea
    "Portimao": (37.2270, -8.6267),  # Portugal
    "Mugello Circuit": (43.9975, 11.3719),  # Italy
    "Paul Ricard Circuit": (43.2506, 5.7919)  # France
}


def get_circuit_coordinates(location_name):
    """Get coordinates for a circuit with fuzzy matching"""
    # Direct match first
    if location_name in CIRCUIT_COORDS:
        return CIRCUIT_COORDS[location_name]
    
    # Fuzzy matching for partial names
    location_lower = location_name.lower()
    for circuit_name, coords in CIRCUIT_COORDS.items():
        if location_lower in circuit_name.lower() or circuit_name.lower() in location_lower:
            return coords
    
    # Geocoding fallback
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location_name}&count=1"
        response = requests.get(geo_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("results"):
                result = data["results"][0]
                return (result["latitude"], result["longitude"])
    except Exception:
        pass
    
    return None


def to_baku(d, t):
    # d = 'YYYY-MM-DD', t = 'HH:MM:SSZ' or 'TBA'
    if not t or t == "TBA":
        return f"{d} (TBA)"
    try:
        # strip trailing Z if present
        tzinfo = ZoneInfo("UTC")
        if t.endswith("Z"):
            t2 = t[:-1]
        else:
            t2 = t
        dt = datetime.fromisoformat(d + "T" + t2)
        # assume dt is UTC if naive
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tzinfo)
        baku = dt.astimezone(ZoneInfo("Asia/Baku"))
        date_str = baku.strftime("%d %b")
        time_str = baku.strftime("%H:%M")
        return f"{date_str} {time_str}"
    except Exception:
        return f"{d} {t}"


def get_current_standings():
    """Get current F1 driver standings"""
    try:
        now = datetime.now()
        season = now.year if now.month > 3 else now.year - 1
        
        # Try multiple APIs with better error handling
        apis = [
            f"https://api.jolpi.ca/ergast/f1/{season}/driverStandings.json",
        ]
        
        data = None
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    break
            except:
                continue
        
        if not data:
            return TRANSLATIONS["api_unavailable"]
        
        try:
            standings_list = data.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
            if not standings_list:
                return TRANSLATIONS["no_standings"]

            standings = standings_list[0].get("DriverStandings", [])
            if not standings:
                return TRANSLATIONS["no_driver_standings"]

            actual_season = standings_list[0].get("season", season)
        except:
            return TRANSLATIONS["invalid_data"]
        
        message = f"🏆 {actual_season} {TRANSLATIONS['season_driver_standings']}\n\n"
        
        for driver in standings:
            try:
                pos = driver.get("position", "?")
                driver_info = driver.get("Driver", {})
                given_name = driver_info.get("givenName", "Unknown")
                family_name = driver_info.get("familyName", "Driver")
                full_name = f"{given_name} {family_name.upper()}"
                nationality = driver_info.get("nationality", "")
                flag = get_country_flag(nationality)
                points = driver.get("points", "0")
                
                message += f"{pos}. {flag} {full_name} ({points} {TRANSLATIONS['points']})\n"
            except:
                continue
        
        return message
    except:
        return TRANSLATIONS["service_unavailable"]


def get_constructor_standings():
    """Get constructor standings"""
    try:
        now = datetime.now()
        season = now.year if now.month > 3 else now.year - 1
        
        # Try multiple APIs
        apis = [
            f"https://api.jolpi.ca/ergast/f1/{season}/constructorStandings.json",]
        
        data = None
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    break
            except:
                continue
        
        if not data:
            return TRANSLATIONS["api_unavailable"]
        
        try:
            standings_list = data.get("MRData", {}).get("StandingsTable", {}).get("StandingsLists", [])
            if not standings_list:
                return TRANSLATIONS["no_constructor_standings"]

            standings = standings_list[0].get("ConstructorStandings", [])
            if not standings:
                return TRANSLATIONS["no_constructor_standings"]

            actual_season = standings_list[0].get("season", season)
        except:
            return TRANSLATIONS["invalid_data"]
        
        # Team flags
        team_flags = {
            "Red Bull": "🇦🇹", "Ferrari": "🇮🇹", "Mercedes": "🇩🇪", "McLaren": "🇬🇧",
            "Aston Martin": "🇬🇧", "Alpine": "🇫🇷", "Williams": "🇬🇧", "AlphaTauri": "🇮🇹",
            "RB": "🇮🇹", "Alfa Romeo": "🇨🇭", "Sauber": "🇨🇭", "Haas": "🇺🇸"
        }
        
        message = f"🏆 *{TRANSLATIONS['season_constructor_standings'].format(actual_season)}*\n\n"
        
        for pos, team in enumerate(standings, 1):
            try:
                constructor = team.get("Constructor", {})
                team_name = constructor.get("name", "Unknown Team")
                points = team.get("points", "0")
                
                flag = ""
                for key, emoji in team_flags.items():
                    if key in team_name:
                        flag = emoji + " "
                        break
                
                message += f"{pos}. {flag}*{team_name}* - {points} {TRANSLATIONS['points']}\n"
            except:
                continue
        
        return message
    except:
        return TRANSLATIONS["service_unavailable"]


def get_last_race():
    """Get last race results using OpenF1 API"""
    return get_last_session_results()  # Use the OpenF1-based function instead



def get_next_race():
    """Get next race schedule using Jolpica API"""
    try:
        now = datetime.now(ZoneInfo("UTC"))
        season = now.year if now.month > 3 else now.year - 1
        
        # Try multiple APIs
        apis = [
            f"https://api.jolpi.ca/ergast/f1/{season}.json",
        ]
        
        data = None
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    break
            except:
                continue
        
        if not data:
            return TRANSLATIONS["api_unavailable"]
        
        try:
            races = data.get("MRData", {}).get("RaceTable", {}).get("Races", [])
            if not races:
                return TRANSLATIONS["no_race_schedule"]
        except:
            return TRANSLATIONS["invalid_data"]
        
        # Find next race
        next_race = None
        for race in races:
            try:
                race_date = race.get("date")
                race_time = race.get("time", "00:00")
                
                if race_date:
                    race_dt_str = f"{race_date}T{race_time.replace('Z', '')}"
                    race_dt = datetime.fromisoformat(race_dt_str)
                    if race_dt.tzinfo is None:
                        race_dt = race_dt.replace(tzinfo=ZoneInfo("UTC"))
                    
                    if race_dt >= now:
                        next_race = race
                        break
            except:
                continue
        
        if not next_race:
            return TRANSLATIONS["season_completed"]
        
        # Extract race info
        race_name = next_race.get("raceName", "Grand Prix")
        circuit = next_race.get("Circuit", {})
        location = circuit.get("Location", {})
        locality = location.get("locality", "")
        country = location.get("country", "")
        
        flag = get_country_flag(country)
        
        message = f"{TRANSLATIONS['next_race']}\n"
        message += f"{flag} *{race_name}*\n\n"
        
        # Collect all sessions with times
        sessions = []
        
        # FP1
        fp1 = next_race.get("FirstPractice", {})
        fp1_date = fp1.get("date")
        fp1_time = fp1.get("time", "TBA")
        if fp1_date and fp1_time != "TBA":
            sessions.append((fp1_date, fp1_time, TRANSLATIONS["fp1"]))

        # FP2
        fp2 = next_race.get("SecondPractice", {})
        fp2_date = fp2.get("date")
        fp2_time = fp2.get("time", "TBA")
        if fp2_date and fp2_time != "TBA":
            sessions.append((fp2_date, fp2_time, TRANSLATIONS["fp2"]))

        # FP3
        fp3 = next_race.get("ThirdPractice", {})
        fp3_date = fp3.get("date")
        fp3_time = fp3.get("time", "TBA")
        if fp3_date and fp3_time != "TBA":
            sessions.append((fp3_date, fp3_time, TRANSLATIONS["fp3"]))

        # Sprint Qualifying
        sprint_quali = next_race.get("SprintQualifying", {})
        sq_date = sprint_quali.get("date")
        sq_time = sprint_quali.get("time", "TBA")
        if sq_date and sq_time != "TBA":
            sessions.append((sq_date, sq_time, TRANSLATIONS["sprint_qualifying"]))

        # Sprint
        sprint = next_race.get("Sprint", {})
        sprint_date = sprint.get("date")
        sprint_time = sprint.get("time", "TBA")
        if sprint_date and sprint_time != "TBA":
            sessions.append((sprint_date, sprint_time, TRANSLATIONS["sprint"]))

        # Qualifying
        quali = next_race.get("Qualifying", {})
        quali_date = quali.get("date")
        quali_time = quali.get("time", "TBA")
        if quali_date and quali_time != "TBA":
            sessions.append((quali_date, quali_time, TRANSLATIONS["qualifying"]))

        # Race
        race_date = next_race.get("date")
        race_time = next_race.get("time", "TBA")
        if race_date and race_time != "TBA":
            sessions.append((race_date, race_time, TRANSLATIONS["race"]))
        
        # Sort sessions by date and time
        sessions.sort(key=lambda x: (x[0], x[1]))
        
        # Display sessions in chronological order
        for session_date, session_time, session_name in sessions:
            baku_time = to_baku(session_date, session_time)
            message += f"*{session_name}:* {baku_time}\n"
        
        message += f"\n_{TRANSLATIONS['all_times_baku']}_\n"
        
        # Add weather forecast
        try:
            coords = get_circuit_coordinates(locality)
            if coords and race_date:
                race_date_obj = datetime.fromisoformat(race_date)
                friday = race_date_obj - timedelta(days=2)
                saturday = race_date_obj - timedelta(days=1)
                sunday = race_date_obj
                
                meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={coords[0]}&longitude={coords[1]}&daily=temperature_2m_max,precipitation_probability_max,wind_speed_10m_max&start_date={friday.date()}&end_date={sunday.date()}"
                weather_response = requests.get(meteo_url, timeout=15)
                
                if weather_response.status_code == 200:
                    weather_data = weather_response.json()
                    daily = weather_data.get("daily", {})
                    temps = daily.get("temperature_2m_max", [])
                    rain_probs = daily.get("precipitation_probability_max", [])
                    wind_speeds = daily.get("wind_speed_10m_max", [])
                    
                    if temps and len(temps) >= 3:
                        message += "\n🌤️ *Hava proqnozu:*\n"
                        days = [TRANSLATIONS["friday"], TRANSLATIONS["saturday"], TRANSLATIONS["sunday"]]
                        for i, day in enumerate(days):
                            if i < len(temps):
                                temp = temps[i]
                                rain = rain_probs[i] if i < len(rain_probs) else 0
                                wind = wind_speeds[i] if i < len(wind_speeds) else 0
                                rain_icon = "🌧️" if rain >= 60 else "⛅" if rain >= 30 else "☀️"
                                message += f"{day}: {temp:.1f}°C {rain_icon} {int(rain)}% 💨{wind:.1f}km/h\n"
        except:
            pass
        
        return message
    except Exception as e:
        return TRANSLATIONS["error_fetching_race"].format(str(e))


def get_last_session_results():
    """Get last session results using OpenF1 API with enhanced data"""
    try:
        now = datetime.now(ZoneInfo("UTC"))
        current_year = now.year
        
        years_to_check = [current_year]
        if now.month <= 3:
            years_to_check.insert(0, current_year - 1)
        
        sessions = []
        for year in years_to_check:
            try:
                sessions_url = f"https://api.openf1.org/v1/sessions?year={year}"
                sessions_response = requests.get(sessions_url, timeout=10)
                if sessions_response.status_code == 200:
                    sessions.extend(sessions_response.json())
            except:
                continue
        
        if not sessions:
            return TRANSLATIONS["no_sessions"]
        
        latest_session = None
        for session in reversed(sessions):
            session_start = session.get("date_start")
            session_type = session.get("session_type")
            
            if session_start and session_type in ["Qualifying", "Sprint", "Race"]:
                try:
                    start_dt = datetime.fromisoformat(session_start.replace('Z', '+00:00'))
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=ZoneInfo("UTC"))
                    
                    if start_dt < (now - timedelta(hours=2)):
                        latest_session = session
                        break
                except:
                    continue
        
        if not latest_session:
            return TRANSLATIONS["no_recent_sessions"]
        
        session_key = latest_session.get("session_key")
        session_type = latest_session.get("session_type")
        meeting_name = latest_session.get("meeting_name", "Grand Prix")
        country_name = latest_session.get("country_name", "")
        flag = get_country_flag(country_name)
        
        # Get positions
        results_url = f"https://api.openf1.org/v1/position?session_key={session_key}"
        results_response = requests.get(results_url, timeout=10)
        if results_response.status_code != 200:
            return TRANSLATIONS["no_results"].format(session_type)
        
        positions_data = results_response.json()
        if not positions_data:
            return TRANSLATIONS["no_position_data"].format(session_type)
        
        final_positions = {}
        for pos_entry in positions_data:
            driver_number = pos_entry.get("driver_number")
            position = pos_entry.get("position")
            date = pos_entry.get("date")
            
            if driver_number and position and date:
                if driver_number not in final_positions or date > final_positions[driver_number]["date"]:
                    final_positions[driver_number] = {"position": position, "date": date}
        
        # Get driver info
        drivers_url = f"https://api.openf1.org/v1/drivers?session_key={session_key}"
        drivers_response = requests.get(drivers_url, timeout=10)
        drivers_info = {}
        if drivers_response.status_code == 200:
            for driver in drivers_response.json():
                driver_number = driver.get("driver_number")
                if driver_number:
                    driver_name = f"{driver.get('first_name', '')} {driver.get('last_name', '')}".strip()
                    country_code = driver.get("country_code") or DRIVER_NATIONALITIES.get(driver_number, "")
                    
                    drivers_info[driver_number] = {
                        "name": driver_name,
                        "country": country_code,
                        "team": driver.get("team_name", "")
                    }
        
        # Only get intervals and fastest lap for Race sessions (skip for Qualifying to speed up)
        intervals_data = {}
        fastest_lap_driver = None
        fastest_lap_time = None
        
        if session_type == "Race":
            try:
                intervals_url = f"https://api.openf1.org/v1/intervals?session_key={session_key}"
                intervals_response = requests.get(intervals_url, timeout=10)
                if intervals_response.status_code == 200:
                    for interval in intervals_response.json():
                        driver_number = interval.get("driver_number")
                        date = interval.get("date")
                        if driver_number and date:
                            if driver_number not in intervals_data or date > intervals_data[driver_number]["date"]:
                                intervals_data[driver_number] = {
                                    "gap_to_leader": interval.get("gap_to_leader", 0),
                                    "date": date
                                }
            except:
                pass
            
            try:
                laps_url = f"https://api.openf1.org/v1/laps?session_key={session_key}"
                laps_response = requests.get(laps_url, timeout=10)
                if laps_response.status_code == 200:
                    for lap in laps_response.json():
                        lap_duration = lap.get("lap_duration")
                        if lap_duration and (fastest_lap_time is None or lap_duration < fastest_lap_time):
                            fastest_lap_time = lap_duration
                            fastest_lap_driver = lap.get("driver_number")
            except:
                pass
        
        sorted_positions = sorted(final_positions.items(), key=lambda x: x[1]["position"])
        if not sorted_positions:
            return TRANSLATIONS["no_final_positions"].format(session_type)
        
        emoji = "🏁" if session_type == "Sprint" else "⏱️" if session_type == "Qualifying" else "🏆"
        session_type_az = TRANSLATIONS.get(session_type.lower(), session_type)
        message = f"{emoji} {flag} *{meeting_name} {session_type_az}*\n\n"
        
        for driver_number, pos_data in sorted_positions[:20]:
            position = pos_data["position"]
            driver_info = drivers_info.get(driver_number, {})
            driver_name = driver_info.get("name", f"Driver {driver_number}")
            driver_country = driver_info.get("country", "")
            driver_flag = get_country_flag(driver_country)
            team_name = driver_info.get("team", "")
            
            line = f"{position}. {driver_flag} {driver_name}"
            
            if session_type in ["Race", "Sprint"] and team_name:
                line += f" ({team_name})"
            
            if session_type == "Race" and driver_number in intervals_data:
                gap = intervals_data[driver_number]["gap_to_leader"]
                if position == 1:
                    line += f" - {TRANSLATIONS['winner']}"
                elif gap > 0:
                    line += f" +{gap:.3f}s"
            
            if session_type == "Race":
                points = get_race_points(position)
                if points > 0:
                    line += f" ({points} {TRANSLATIONS['points']})"
                if driver_number == fastest_lap_driver and position <= 10:
                    line += " 🏁+1"
            elif session_type == "Sprint":
                points = get_sprint_points(position)
                if points > 0:
                    line += f" ({points} {TRANSLATIONS['points']})"
            
            message += line + "\n"
        
        if session_type == "Race" and fastest_lap_driver and fastest_lap_time:
            fastest_driver_info = drivers_info.get(fastest_lap_driver, {})
            fastest_name = fastest_driver_info.get("name", f"Driver {fastest_lap_driver}")
            minutes = int(fastest_lap_time // 60)
            seconds = fastest_lap_time % 60
            message += f"\n⚡ {TRANSLATIONS['fastest_lap'].format(fastest_name, minutes, seconds)}"
        
        return message
        
    except Exception as e:
        return TRANSLATIONS["error_fetching_session"].format(str(e))





def get_weather_forecast(location, country):
    """Get 3-day weather forecast for a circuit location using Open-Meteo API"""
    try:
        # Get coordinates from static dictionary
        coords = get_circuit_coordinates(location)
        if coords is None:
            # Try geocoding as fallback
            try:
                geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1"
                response = requests.get(geo_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("results"):
                        result = data["results"][0]
                        coords = (result["latitude"], result["longitude"])
            except Exception:
                pass

        if coords is None:
            return TRANSLATIONS["weather_unavailable"]

        # For São Paulo GP, we know it's November 7-9, 2025, so use those dates
        if "são paulo" in location.lower() or "sao paulo" in location.lower() or "interlagos" in location.lower():
            race_dates = [
                datetime(2025, 11, 7).date(),  # Friday
                datetime(2025, 11, 8).date(),  # Saturday
                datetime(2025, 11, 9).date()   # Sunday (Race)
            ]
        else:
            # Calculate race weekend dates (Friday-Sunday)
            now = datetime.now(ZoneInfo("UTC"))
            days_since_friday = (now.weekday() - 4) % 7  # 4 = Friday
            friday = (now - timedelta(days=days_since_friday)).date()
            saturday = friday + timedelta(days=1)
            sunday = friday + timedelta(days=2)
            race_dates = [friday, saturday, sunday]

        # Get 7-day forecast to ensure we cover the race dates
        meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={coords[0]}&longitude={coords[1]}&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max&timezone=auto&forecast_days=7"

        weather_response = requests.get(meteo_url, timeout=15)
        weather_response.raise_for_status()
        weather_data = weather_response.json()

        daily = weather_data.get("daily", {})
        dates = daily.get("time", [])
        temps_max = daily.get("temperature_2m_max", [])
        temps_min = daily.get("temperature_2m_min", [])
        rain_probs = daily.get("precipitation_probability_max", [])
        wind_speeds = daily.get("wind_speed_10m_max", [])

        if not dates or not temps_max or not rain_probs:
            return "🌦️ Weather data not available for this location."

        # Find weather data for our race dates
        message = f"🌤️ {TRANSLATIONS['weather_forecast'].format(country)} GP:\n"

        race_day_names = ["Fri", "Sat", "Sun (Race)"]

        for i, (race_date, day_name) in enumerate(zip(race_dates, race_day_names)):
            # Find the index in the weather data that matches this date
            date_str = race_date.isoformat()
            try:
                date_index = dates.index(date_str)
                temp_max = int(temps_max[date_index])
                temp_min = int(temps_min[date_index]) if date_index < len(temps_min) else temp_max - 5
                rain_prob = int(rain_probs[date_index])
                wind_speed = int(wind_speeds[date_index]) if date_index < len(wind_speeds) else 10

                # Weather emoji based on rain probability
                if rain_prob >= 60:
                    weather_emoji = "🌧️"
                elif rain_prob >= 30:
                    weather_emoji = "⛅"
                else:
                    weather_emoji = "☀️"

                message += f"{day_name}: {temp_max}°C / {rain_prob}% rain / 💨 {wind_speed} km/h\n"
            except (ValueError, IndexError):
                # If exact date not found, try to find closest date in forecast
                try:
                    target_date = datetime.fromisoformat(date_str).date()
                    # Find closest date in available forecast
                    closest_index = min(range(len(dates)), key=lambda j: abs((datetime.fromisoformat(dates[j]).date() - target_date).days))
                    if abs((datetime.fromisoformat(dates[closest_index]).date() - target_date).days) <= 2:  # Within 2 days
                        temp_max = int(temps_max[closest_index])
                        temp_min = int(temps_min[closest_index]) if closest_index < len(temps_min) else temp_max - 5
                        rain_prob = int(rain_probs[closest_index])
                        wind_speed = int(wind_speeds[closest_index]) if closest_index < len(wind_speeds) else 10

                        if rain_prob >= 60:
                            weather_emoji = "🌧️"
                        elif rain_prob >= 30:
                            weather_emoji = "⛅"
                        else:
                            weather_emoji = "☀️"

                        message += f"{day_name}: {temp_max}°C / {rain_prob}% rain / 💨 {wind_speed} km/h\n"
                    else:
                        message += f"{day_name}: Data unavailable\n"
                except:
                    message += f"{day_name}: Data unavailable\n"

        return message.strip()

    except requests.exceptions.RequestException:
        return TRANSLATIONS["weather_unavailable"]
    except Exception:
        return TRANSLATIONS["weather_unavailable"]


def check_active_f1_session():
    """Check if there's currently an active F1 session using OpenF1 API"""
    try:
        now = datetime.now(ZoneInfo("UTC"))
        current_year = now.year

        # Check current and next year for sessions
        years_to_check = [current_year]
        if now.month >= 11:
            years_to_check.append(current_year + 1)

        sessions = []
        for year in years_to_check:
            try:
                sessions_url = f"https://api.openf1.org/v1/sessions?year={year}"
                sessions_response = requests.get(sessions_url, timeout=10)
                if sessions_response.status_code == 200:
                    sessions.extend(sessions_response.json())
            except:
                continue

        if not sessions:
            return False

        # Check if any session is currently active (within the last 2 hours and next 4 hours)
        for session in sessions:
            session_start = session.get("date_start")
            session_end = session.get("date_end")

            if session_start:
                try:
                    start_dt = datetime.fromisoformat(session_start.replace('Z', '+00:00'))
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=ZoneInfo("UTC"))

                    # Check if session is currently running or will start soon
                    time_diff_start = (start_dt - now).total_seconds() / 3600  # hours
                    time_diff_end = 0

                    if session_end:
                        end_dt = datetime.fromisoformat(session_end.replace('Z', '+00:00'))
                        if end_dt.tzinfo is None:
                            end_dt = end_dt.replace(tzinfo=ZoneInfo("UTC"))
                        time_diff_end = (end_dt - now).total_seconds() / 3600  # hours

                        # Session is active if it started within last 2 hours and hasn't ended + 1 hour grace period
                        if -2 <= time_diff_start <= 0 and time_diff_end > -1:  # Allow 1 hour after session ends
                            return True
                    else:
                        # If no end time, check if session started recently (within 2 hours)
                        if -2 <= time_diff_start <= 1:  # Allow 1 hour future for upcoming sessions
                            return True

                except (ValueError, TypeError):
                    continue

        return False

    except Exception as e:
        logging.error(f"Error checking active F1 session: {e}")
        return False


def get_weather_info():
    """Get real weather forecast using OpenF1 API for location and Open-Meteo for weather data"""
    try:
        # Handle season rollover - check current and next year if needed
        now = datetime.now(ZoneInfo("UTC"))
        current_year = now.year

        # If it's December, also check next year for sessions
        years_to_check = [current_year]
        if now.month >= 11:
            years_to_check.append(current_year + 1)

        sessions = []
        for year in years_to_check:
            try:
                sessions_url = f"https://api.openf1.org/v1/sessions?year={year}"
                sessions_response = requests.get(sessions_url, timeout=15)
                sessions_response.raise_for_status()
                year_sessions = sessions_response.json()
                sessions.extend(year_sessions)
            except requests.exceptions.RequestException:
                continue

        if not sessions:
            return "❌ No sessions found. API may be offline or offseason."

        # Find next/current weekend
        target_session = None

        for session in sessions:
            session_start = session.get("date_start")
            if session_start:
                try:
                    start_dt = datetime.fromisoformat(session_start.replace('Z', '+00:00'))
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=ZoneInfo("UTC"))
                    days_diff = (start_dt - now).days
                    if -1 <= days_diff <= 4:
                        target_session = session
                        break
                except (ValueError, TypeError):
                    continue

        if not target_session and sessions:
            target_session = sessions[-1]  # Fallback to most recent

        if not target_session:
            return "❌ No suitable session found for weather data."

        meeting_name = target_session.get("meeting_name", "Grand Prix")
        location = target_session.get("location", "")
        country_name = target_session.get("country_name", "")

        flag = get_country_flag(country_name)

        message = f"🌤️ Hava - {flag} {meeting_name}\n"
        message += f"📍 {location}\n\n"

        coords = get_circuit_coordinates(location)
        if coords is None:
            return TRANSLATIONS["weather_unavailable"]

        # Calculate actual race weekend dates (Friday-Sunday)
        # Find the Friday session to determine race weekend start
        race_weekend_start = None
        try:
            session_start = target_session.get("date_start")
            if session_start:
                start_dt = datetime.fromisoformat(session_start.replace('Z', '+00:00'))
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=ZoneInfo("UTC"))
                
                # Find the Friday of this race weekend
                # If session is Friday (weekday 4), use it; otherwise find previous Friday
                days_to_friday = (start_dt.weekday() - 4) % 7
                if days_to_friday > 0:
                    days_to_friday -= 7  # Go back to previous Friday
                friday = (start_dt + timedelta(days=-days_to_friday)).date()
                race_weekend_start = friday
        except Exception:
            # Fallback: use current week's Friday
            days_since_friday = (now.weekday() - 4) % 7
            friday = (now - timedelta(days=days_since_friday)).date()
            race_weekend_start = friday

        if not race_weekend_start:
            return TRANSLATIONS["error_fetching_weather"]

        # Get 7-day forecast to ensure we cover the race weekend
        meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={coords[0]}&longitude={coords[1]}&daily=temperature_2m_max,precipitation_probability_max,wind_speed_10m_max&timezone=auto&forecast_days=7"

        try:
            weather_response = requests.get(meteo_url, timeout=15)
            weather_response.raise_for_status()
            weather_data = weather_response.json()

            daily = weather_data.get("daily", {})
            dates = daily.get("time", [])
            temps = daily.get("temperature_2m_max", [])
            rain_probs = daily.get("precipitation_probability_max", [])
            wind_speeds = daily.get("wind_speed_10m_max", [])
        except requests.exceptions.RequestException:
            return "❌ Weather data unavailable."

        # Determine weekend format
        is_sprint_weekend = "Sprint" in meeting_name or any(x in meeting_name for x in ["Miami", "Austria", "United States", "Brazil", "Qatar"])

        if is_sprint_weekend:
            weekend_schedule = {
                "Friday": ["Practice 1 (18:30)", "Sprint Qualifying (22:30)"],
                "Saturday": ["Sprint (19:00)", "Qualifying (22:00)"],
                "Sunday": ["Race (21:00)"]
            }
        else:
            weekend_schedule = {
                "Friday": ["Practice 1 (17:30)", "Practice 2 (21:00)"],
                "Saturday": ["Practice 3 (17:30)", "Qualifying (21:00)"],
                "Sunday": ["Race (20:00)"]
            }

        # Display weekend forecast with actual race weekend dates
        race_dates = [race_weekend_start, race_weekend_start + timedelta(days=1), race_weekend_start + timedelta(days=2)]
        
        for i, (day, sessions_list) in enumerate(weekend_schedule.items()):
            race_date = race_dates[i]
            date_str = race_date.isoformat()
            
            # Find weather data for this specific date
            try:
                date_index = dates.index(date_str)
                temp = int(temps[date_index])
                rain_chance = int(rain_probs[date_index])
                wind_speed = int(wind_speeds[date_index]) if date_index < len(wind_speeds) else 10
            except (ValueError, IndexError):
                # Fallback if exact date not found
                temp = 23
                rain_chance = 20
                wind_speed = 10

            if rain_chance >= 60:
                rain_icon = "🌧️"
            elif rain_chance >= 30:
                rain_icon = "⛅"
            else:
                rain_icon = "☀️"

            rain_desc = ""
            if rain_chance >= 81:
                rain_desc = " (Very likely heavy rain)"
            elif rain_chance >= 61:
                rain_desc = " (Likely rain)"
            elif rain_chance >= 31:
                rain_desc = " (Chance of rain)"
            elif rain_chance >= 11:
                rain_desc = " (Low chance of rain)"

            message += f"🗓️ {day}\n\n"

            for session in sessions_list:
                message += f"{session} ({temp}°C {rain_icon} {rain_chance}% / 💨 {wind_speed} km/h){rain_desc}\n"

            message += "\n"

        return message.strip()

    except requests.exceptions.RequestException:
        return TRANSLATIONS["weather_unavailable"]
    except Exception as e:
        return TRANSLATIONS["error_fetching_weather"].format(str(e))


def load_user_streams():
    """Load user streams from JSON file"""
    if not os.path.exists("user_streams.json"):
        return {}
    try:
        with open("user_streams.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_user_streams(data):
    """Save user streams to JSON file"""
    try:
        with open("user_streams.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except:
        return False


def get_streams(user_id=None):
    """Read stream links and return message with keyboard"""
    try:
        all_streams = []
        
        # Load global streams
        if os.path.exists("streams.txt"):
            with open("streams.txt", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "|" in line:
                            parts = line.split("|", 1)
                            all_streams.append({"name": parts[0].strip(), "url": parts[1].strip()})
        
        # Load user streams
        user_streams_data = load_user_streams()
        if user_id and str(user_id) in user_streams_data:
            for stream in user_streams_data[str(user_id)]:
                all_streams.append({"name": stream.get("name"), "url": stream.get("url")})
        
        if not all_streams:
            return TRANSLATIONS["no_streams"], None
        
        keyboard = []
        for idx, stream in enumerate(all_streams, 1):
            keyboard.append([InlineKeyboardButton(f"🎦 {stream['name']}", url=stream['url'])])
        keyboard = InlineKeyboardMarkup(keyboard)
        message = f"{TRANSLATIONS['available_streams']}\n\n{TRANSLATIONS['tap_to_open']}"
        
        return message, keyboard
    except Exception as e:
        return f"❌ Error: {str(e)}", None





# ==================== TELEGRAM BOT HANDLERS ====================


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with comprehensive inline keyboard"""
    keyboard = [
        [InlineKeyboardButton(TRANSLATIONS["driver_standings"], callback_data="standings"),
         InlineKeyboardButton(TRANSLATIONS["constructor_standings"], callback_data="constructors")],
        [InlineKeyboardButton(TRANSLATIONS["last_session"], callback_data="lastrace"),
         InlineKeyboardButton(TRANSLATIONS["schedule_weather"], callback_data="nextrace")],
        [InlineKeyboardButton(TRANSLATIONS["live_timing"], callback_data="live"),
         InlineKeyboardButton(TRANSLATIONS["streams"], callback_data="streams")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = f"""{TRANSLATIONS["welcome_title"]}

{TRANSLATIONS["welcome_text"]}"""

    if isinstance(update.message, Message):
        await update.message.reply_text(
            welcome_text, reply_markup=reply_markup, parse_mode="Markdown"
        )


async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show menu buttons"""
    keyboard = [
        [InlineKeyboardButton(TRANSLATIONS["driver_standings"], callback_data="standings"),
         InlineKeyboardButton(TRANSLATIONS["constructor_standings"], callback_data="constructors")],
        [InlineKeyboardButton(TRANSLATIONS["last_session"], callback_data="lastrace"),
         InlineKeyboardButton(TRANSLATIONS["schedule_weather"], callback_data="nextrace")],
        [InlineKeyboardButton(TRANSLATIONS["live_timing"], callback_data="live"),
         InlineKeyboardButton(TRANSLATIONS["help_commands_btn"], callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if isinstance(update.message, Message):
        await update.message.reply_text(f"{TRANSLATIONS['menu_title']}\n\n{TRANSLATIONS['menu_text']}", reply_markup=reply_markup, parse_mode="Markdown")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks"""
    query = update.callback_query
    if query is not None:
        await query.answer()

        # Show "loading..." message
        if isinstance(query.message, Message) and query.message.chat is not None:
            loading_msg = await query.message.reply_text(get_f1_loading_message())
        else:
            loading_msg = None
    else:
        return

    try:
        if query.data == "standings":
            message = get_current_standings()
        elif query.data == "constructors":
            message = get_constructor_standings()
        elif query.data == "lastrace":
            message = get_last_session_results()
        elif query.data == "nextrace":
            message = get_next_race()
        elif query.data == "live":
            # Check if there's an active F1 session before starting live updates
            if not check_active_f1_session():
                message = "❌ Hal-hazırda aktiv F1 sessiyası yoxdur\n\n🔴 Canlı vaxt yalnız F1 yarış həftəsonlarında, sessiya gedərkən mövcuddur.\n\n⏰ Canlı vaxt sessiyadan 2 saat əvvəl başlayır və sessiyadan 1 saat sonra dayanır.\n\n📊 Canlı vaxt göstərir:\n• Sürücülərin mövqeləri\n• Dövrə vaxtları\n• Interval vaxtları\n• Təkər məlumatları\n• Hər 30 saniyədə avtomatik yeniləmə\n\nAlternativlər:\n• /nextrace - Gələn yarış və hava proqnozu\n• /lastrace - Son sessiya nəticələri"
            elif OPTIMIZED_SCRAPER_AVAILABLE:
                try:
                    # Initial fetch using optimized scraper
                    data = await get_optimized_live_timing()
                    if data:
                        message = format_timing_data_for_telegram(data)
                        if loading_msg:
                            await loading_msg.delete()
                        if isinstance(query.message, Message):
                            live_msg = await query.message.reply_text(message)

                        # Track previous data to detect changes
                        previous_data_hash = hash(str(data))

                        # Auto-update every 30 seconds until session ends or no changes detected
                        while True:
                            await asyncio.sleep(30)
                            try:
                                data = await get_optimized_live_timing()
                                if data:
                                    current_data_hash = hash(str(data))
                                    # Only update if data has actually changed
                                    if current_data_hash != previous_data_hash:
                                        message = format_timing_data_for_telegram(data)
                                        try:
                                            await live_msg.edit_text(message, parse_mode="Markdown")
                                        except:
                                            # Delete old message and send new one
                                            try:
                                                await live_msg.delete()
                                            except:
                                                pass
                                            if isinstance(query.message, Message):
                                                live_msg = await query.message.reply_text(message, parse_mode="Markdown")
                                        previous_data_hash = current_data_hash
                                    # Continue checking even if no changes (session still active)
                                else:
                                    break  # No data = session ended
                            except Exception:
                                break
                        return
                    else:
                        message = TRANSLATIONS["no_live_data"]
                except Exception as e:
                    message = TRANSLATIONS["optimized_error"].format(str(e))
            elif SCRAPER_AVAILABLE:
                try:
                    # Initial fetch using final scraper
                    data = await scrape_formula_timer_live_timing()
                    if data:
                        message = format_timing_data_for_telegram(data)
                        if loading_msg:
                            await loading_msg.delete()
                        if isinstance(query.message, Message):
                            live_msg = await query.message.reply_text(message)

                        # Track previous data to detect changes
                        previous_data_hash = hash(str(data))

                        # Auto-update every 30 seconds until session ends or no changes detected
                        while True:
                            await asyncio.sleep(30)
                            try:
                                data = await scrape_formula_timer_live_timing()
                                if data:
                                    current_data_hash = hash(str(data))
                                    # Only update if data has actually changed
                                    if current_data_hash != previous_data_hash:
                                        message = format_timing_data_for_telegram(data)
                                        try:
                                            await live_msg.edit_text(message, parse_mode="Markdown")
                                        except:
                                            # Delete old message and send new one
                                            try:
                                                await live_msg.delete()
                                            except:
                                                pass
                                            if isinstance(query.message, Message):
                                                live_msg = await query.message.reply_text(message, parse_mode="Markdown")
                                        previous_data_hash = current_data_hash
                                    # Continue checking even if no changes (session still active)
                                else:
                                    break  # No data = session ended
                            except Exception:
                                break
                        return
                    else:
                        message = "❌ No live timing data available\n\nTry /lastrace for recent results"
                except Exception as e:
                    message = TRANSLATIONS["scraper_error"].format(str(e))
            else:
                message = "❌ Live timing not available\n\nInstall: pip install playwright && playwright install chromium"
        elif query.data == "weather_current":
            # Redirect to schedule which now includes weather
            message = get_next_race()
        elif query.data == "weather_info":
            # Handle weather info button click
            message = get_weather_info()
        elif query.data == "streams":
            user_id = query.from_user.id if query.from_user else None
            message, keyboard = get_streams(user_id)
            if loading_msg is not None:
                try:
                    await loading_msg.delete()
                except:
                    pass
            if isinstance(query.message, Message):
                if keyboard:
                    await query.message.reply_text(message, parse_mode="Markdown", reply_markup=keyboard)
                else:
                    await query.message.reply_text(message, parse_mode="Markdown")
            return
        elif query.data == "help":
            message = f"""{TRANSLATIONS["help_title"]}

{TRANSLATIONS["help_commands"]}

{TRANSLATIONS["help_usage"]}"""
        else:
            message = TRANSLATIONS["unknown_command"]
    except Exception as e:
        message = TRANSLATIONS["error_occurred"].format(str(e))
    finally:
        # Always delete loading message
        if loading_msg is not None:
            try:
                await loading_msg.delete()
            except:
                pass

    # Send result
    if isinstance(query.message, Message):
        await query.message.reply_text(message, parse_mode="Markdown")


# Command handlers
async def standings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update.message, Message):
        await update.message.reply_text(get_f1_loading_message())
        message = get_current_standings()
        await update.message.reply_text(message, parse_mode="Markdown")





async def constructors_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update.message, Message):
        await update.message.reply_text(get_f1_loading_message())
        message = get_constructor_standings()
        await update.message.reply_text(message, parse_mode="Markdown")


async def lastrace_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update.message, Message):
        await update.message.reply_text(get_f1_loading_message())
        message = get_last_session_results()
        await update.message.reply_text(message, parse_mode="Markdown")


async def nextrace_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if isinstance(update.message, Message):
        await update.message.reply_text(get_f1_loading_message())
        message = get_next_race()
        await update.message.reply_text(message, parse_mode="Markdown")


async def live_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Live timing with auto-update using final scraper - optimized to only run during active sessions"""
    if isinstance(update.message, Message):
        loading_msg = await update.message.reply_text(get_f1_loading_message())

        # Check if there's an active F1 session before starting live updates
        if not check_active_f1_session():
            await loading_msg.edit_text("❌ Hal-hazırda aktiv F1 sessiyası yoxdur\n\n🔴 Canlı vaxt yalnız F1 yarış həftəsonlarında, sessiya gedərkən mövcuddur.\n\n⏰ Canlı vaxt sessiyadan 2 saat əvvəl başlayır və sessiyadan 1 saat sonra dayanır.\n\n📊 Canlı vaxt göstərir:\n• Sürücülərin mövqeləri\n• Dövrə vaxtları\n• Interval vaxtları\n• Təkər məlumatları\n• Hər 30 saniyədə avtomatik yeniləmə\n\nAlternativlər:\n• /nextrace - Gələn yarış və hava proqnozu\n• /lastrace - Son sessiya nəticələri")
            return

        if OPTIMIZED_SCRAPER_AVAILABLE:
            try:
                # Initial fetch using optimized scraper
                data = await get_optimized_live_timing()
                if data:
                    timing_message = format_timing_data_for_telegram(data)
                    await loading_msg.edit_text(timing_message)

                    # Track previous data to detect changes
                    previous_data_hash = hash(str(data))

                    # Auto-update every 30 seconds until session ends or no changes detected
                    while True:
                        await asyncio.sleep(30)
                        try:
                            data = await get_optimized_live_timing()
                            if data:
                                current_data_hash = hash(str(data))
                                # Only update if data has actually changed
                                if current_data_hash != previous_data_hash:
                                    timing_message = format_timing_data_for_telegram(data)
                                    try:
                                        await loading_msg.edit_text(timing_message, parse_mode="Markdown")
                                    except:
                                        # Delete old message and send new one
                                        try:
                                            await loading_msg.delete()
                                        except:
                                            pass
                                        loading_msg = await update.message.reply_text(timing_message, parse_mode="Markdown")
                                    previous_data_hash = current_data_hash
                                # Continue checking even if no changes (session still active)
                            else:
                                break  # No data = session ended
                        except Exception:
                            break
                else:
                    await loading_msg.edit_text("❌ No live timing data available\n\nTry /lastrace for recent results.")

            except Exception as e:
                await loading_msg.edit_text(f"❌ Optimized scraper error: {str(e)}\n\nTry /lastrace for recent results.")
        elif SCRAPER_AVAILABLE:
            try:
                # Fallback to original scraper
                data = await scrape_formula_timer_live_timing()
                if data:
                    timing_message = format_timing_data_for_telegram(data)
                    await loading_msg.edit_text(timing_message)

                    # Track previous data to detect changes
                    previous_data_hash = hash(str(data))

                    # Auto-update every 30 seconds until session ends or no changes detected
                    while True:
                        await asyncio.sleep(30)
                        try:
                            data = await scrape_formula_timer_live_timing()
                            if data:
                                current_data_hash = hash(str(data))
                                # Only update if data has actually changed
                                if current_data_hash != previous_data_hash:
                                    timing_message = format_timing_data_for_telegram(data)
                                    try:
                                        await loading_msg.edit_text(timing_message, parse_mode="Markdown")
                                    except:
                                        # Delete old message and send new one
                                        try:
                                            await loading_msg.delete()
                                        except:
                                            pass
                                        loading_msg = await update.message.reply_text(timing_message, parse_mode="Markdown")
                                    previous_data_hash = current_data_hash
                                # Continue checking even if no changes (session still active)
                            else:
                                break  # No data = session ended
                        except Exception:
                            break
                else:
                    await loading_msg.edit_text("❌ No live timing data available\n\nTry /lastrace for recent results.")

            except Exception as e:
                await loading_msg.edit_text(f"❌ Error: {str(e)}\n\nTry /lastrace for recent results.")
        else:
            await loading_msg.edit_text(TRANSLATIONS["live_not_available"])











async def weather_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get current weather information"""
    if isinstance(update.message, Message):
        await update.message.reply_text(get_f1_loading_message())
        message = get_weather_info()
        await update.message.reply_text(message, parse_mode="Markdown")





async def streams_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get available streams"""
    if isinstance(update.message, Message):
        user_id = update.message.from_user.id if update.message.from_user else None
        message, keyboard = get_streams(user_id)
        if keyboard:
            await update.message.reply_text(message, parse_mode="Markdown", reply_markup=keyboard)
        else:
            await update.message.reply_text(message, parse_mode="Markdown")


async def addstream_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a personal stream"""
    if not isinstance(update.message, Message) or update.message.from_user is None:
        return

    user_id = str(update.message.from_user.id)
    args = context.args

    if not args:
        await update.message.reply_text(TRANSLATIONS["usage_addstream"])
        return

    full_text = " ".join(args)
    if "|" not in full_text:
        await update.message.reply_text(TRANSLATIONS["use_format"])
        return

    name, url = full_text.split("|", 1)
    name = name.strip()
    url = url.strip()

    if not name or not url:
        await update.message.reply_text(TRANSLATIONS["name_url_required"])
        return

    user_streams = load_user_streams()
    if user_id not in user_streams:
        user_streams[user_id] = []

    user_streams[user_id].append({"name": name, "url": url})

    if save_user_streams(user_streams):
        await update.message.reply_text(TRANSLATIONS["stream_added"].format(name))
    else:
        await update.message.reply_text(TRANSLATIONS["stream_error"])


async def removestream_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a personal stream"""
    if not isinstance(update.message, Message) or update.message.from_user is None:
        return

    user_id = str(update.message.from_user.id)
    args = context.args

    if not args:
        await update.message.reply_text(TRANSLATIONS["usage_removestream"])
        return

    try:
        index = int(args[0]) - 1
    except ValueError:
        await update.message.reply_text(TRANSLATIONS["invalid_removestream"])
        return

    user_streams = load_user_streams()
    if user_id not in user_streams or not user_streams[user_id]:
        await update.message.reply_text(TRANSLATIONS["no_personal_streams"])
        return

    if index < 0 or index >= len(user_streams[user_id]):
        await update.message.reply_text(TRANSLATIONS["invalid_number_range"].format(len(user_streams[user_id])))
        return

    removed = user_streams[user_id].pop(index)

    if save_user_streams(user_streams):
        await update.message.reply_text(TRANSLATIONS["stream_removed"].format(removed['name']))
    else:
        await update.message.reply_text(TRANSLATIONS["error_removing"])


async def streamhelp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show stream help"""
    if not isinstance(update.message, Message):
        return

    help_text = f"""{TRANSLATIONS["stream_help_title"]}

{TRANSLATIONS["stream_help_best"]}

{TRANSLATIONS["stream_help_how"]}

{TRANSLATIONS["stream_help_vlc"]}"""

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def playstream_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send stream link"""
    if not isinstance(update.message, Message) or update.message.from_user is None:
        return

    user_id = str(update.message.from_user.id)
    args = context.args

    if not args:
        await update.message.reply_text(TRANSLATIONS["playstream_usage"])
        return

    arg = args[0]
    video_url = None
    stream_name = "Stream"

    if arg.startswith(("http://", "https://")):
        video_url = arg
        stream_name = TRANSLATIONS["direct_stream"]
    else:
        try:
            index = int(arg) - 1
            user_streams = load_user_streams()

            if user_id not in user_streams or not user_streams[user_id]:
                await update.message.reply_text(TRANSLATIONS["no_streams_found"])
                return

            if index < 0 or index >= len(user_streams[user_id]):
                await update.message.reply_text(TRANSLATIONS["invalid_number"])
                return

            stream = user_streams[user_id][index]
            video_url = stream.get("url")
            stream_name = stream.get("name", "Stream")
        except ValueError:
            await update.message.reply_text(TRANSLATIONS["invalid_input"])
            return

    if not video_url:
        await update.message.reply_text(TRANSLATIONS["no_url"])
        return

    # Send link
    await update.message.reply_text(
        f"🔗 *{stream_name}*\n\n"
        f"`{video_url}`\n\n"
        f"{TRANSLATIONS['copy_open_vlc']}",
        parse_mode="Markdown"
    )


# Global reference for bot application (needed for background threads)
BOT_APP = None

# ==================== MAIN ====================

# Flask app for Leapcell deployment
app = Flask(__name__)

@app.route('/')
def home():
    """Health check endpoint for Leapcell"""
    return {
        "status": "F1 Telegram Bot (Leapcell Test) is running!",
        "version": "1.0.0-leapcell",
        "timestamp": datetime.now().isoformat(),
        "deployment": "Leapcell",
        "features": {
            "containerized": True,
            "webhook_mode": True,
            "optimized_scraping": True,
            "enhanced_error_handling": True
        }
    }

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "F1 Telegram Bot Leapcell Test"}

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Handle Telegram webhook updates"""
    try:
        if BOT_APP is None:
            logging.error("Bot application not initialized")
            return 'ERROR', 500

        update_data = request.get_json()
        if update_data:
            update = Update.de_json(update_data, BOT_APP.bot)
            # Process update in the bot's event loop
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(BOT_APP.process_update(update))
            return 'OK', 200
        else:
            return 'NO DATA', 400
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return 'ERROR', 500

def setup_bot():
    """Setup and start the Telegram bot with webhooks"""
    try:
        from dotenv import load_dotenv
        load_dotenv(override=False)
    except ImportError:
        # Fallback: manually read .env file if python-dotenv is not installed
        if not os.getenv("TELEGRAM_BOT_TOKEN") and os.path.exists(".env"):
            try:
                with open(".env", "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if not os.getenv(key):
                                os.environ[key] = value
            except Exception:
                pass

    # Get bot token from environment variable
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

    if not BOT_TOKEN:
        try:
            print(TRANSLATIONS["token_not_set"])
            print(TRANSLATIONS["token_setup_instructions"])
        except UnicodeEncodeError:
            print("Error: TELEGRAM_BOT_TOKEN is not set!")
            print("Get your token from @BotFather: https://t.me/BotFather")
        return False

    # Create application
    application = Application.builder().token(BOT_TOKEN).build()

    # store global reference
    global BOT_APP
    BOT_APP = application

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", show_menu))
    application.add_handler(CommandHandler("standings", standings_cmd))
    application.add_handler(CommandHandler("constructors", constructors_cmd))
    application.add_handler(CommandHandler("lastrace", lastrace_cmd))
    application.add_handler(CommandHandler("nextrace", nextrace_cmd))
    application.add_handler(CommandHandler("live", live_cmd))
    application.add_handler(CommandHandler("weather", weather_cmd))
    application.add_handler(CommandHandler("streams", streams_cmd))
    application.add_handler(CommandHandler("addstream", addstream_cmd))
    application.add_handler(CommandHandler("removestream", removestream_cmd))
    application.add_handler(CommandHandler("playstream", playstream_cmd))
    application.add_handler(CommandHandler("streamhelp", streamhelp_cmd))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Setup webhook instead of polling
    def setup_webhook():
        try:
            # Get the webhook URL from environment or construct it
            webhook_url = os.getenv("WEBHOOK_URL")
            if not webhook_url:
                # Try to construct from Leapcell environment
                leapcell_url = os.getenv("LEAPCELL_URL")
                if leapcell_url:
                    webhook_url = f"{leapcell_url}/webhook"
                else:
                    # Fallback for local development
                    webhook_url = "https://your-leapcell-service-url/webhook"

            print("☁️ Leapcell F1 Bot is starting...")
            print(f"🔗 Setting up webhook: {webhook_url}")

            # Set webhook
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def set_webhook_async():
                try:
                    await application.bot.set_webhook(url=webhook_url)
                    print("✅ Webhook set successfully!")
                    print("🤖 Bot is ready and waiting for webhook updates...")
                except Exception as e:
                    print(f"❌ Failed to set webhook: {e}")
                    print("🔄 Falling back to polling mode...")
                    # Fallback to polling if webhook fails
                    try:
                        await application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None)
                    except Exception as poll_e:
                        print(f"❌ Polling also failed: {poll_e}")

            loop.run_until_complete(set_webhook_async())

        except Exception as e:
            print(f"❌ Webhook setup error: {e}")
            print("🔄 Falling back to polling mode...")
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(application.run_polling(allowed_updates=Update.ALL_TYPES, stop_signals=None))
            except Exception as poll_e:
                print(f"❌ Polling also failed: {poll_e}")

    # Start bot setup in background thread
    bot_thread = threading.Thread(target=setup_webhook, daemon=True)
    bot_thread.start()
    return True

# Initialize bot when app starts
if __name__ != "__main__":
    # When imported by gunicorn, start the bot
    setup_bot()

if __name__ == "__main__":
    # Local development mode
    setup_bot()
    app.run(host="0.0.0.0", port=8080)

