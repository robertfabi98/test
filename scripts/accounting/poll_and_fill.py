#!/usr/bin/env python3
"""
Polls Telegram for new accounting messages, fills the monthly Excel file,
and optionally syncs to Google Sheets.
Designed to run as a GitHub Actions job (every hour).
"""

import logging
import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser import parse_message
from excel_generator import generate_excel

try:
    from sheets_sync import sync_to_sheets
    _SHEETS_OK = True
except ImportError:
    _SHEETS_OK = False

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN     = os.environ['TELEGRAM_BOT_TOKEN']
CHAT_ID   = str(os.environ.get('TELEGRAM_CHAT_ID', ''))
SHEET_ID  = os.environ.get('GOOGLE_SHEET_ID', '')
OUTPUT_DIR = os.environ.get(
    'OUTPUT_DIR',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'contabilita')
)

_API         = f'https://api.telegram.org/bot{TOKEN}'
_OFFSET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.telegram_offset')


def _load_offset() -> int:
    try:
        with open(_OFFSET_FILE) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def _save_offset(offset: int) -> None:
    with open(_OFFSET_FILE, 'w') as f:
        f.write(str(offset))


def _get_updates(offset: int) -> list:
    params = {'limit': 100}
    if offset:
        params['offset'] = offset
    r = requests.get(f'{_API}/getUpdates', params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    if not data.get('ok'):
        raise RuntimeError(f'Telegram API error: {data}')
    return data['result']


def _send(chat_id: str, text: str) -> None:
    try:
        requests.post(f'{_API}/sendMessage',
                      json={'chat_id': chat_id, 'text': text},
                      timeout=10)
    except Exception as e:
        logger.warning(f'Invio risposta fallito: {e}')


def main() -> None:
    offset  = _load_offset()
    updates = _get_updates(offset)
    logger.info(f'{len(updates)} aggiornamenti ricevuti (offset={offset})')

    if not updates:
        _save_offset(offset)  # assicura che il file esista sempre
        return

    new_offset = max(u['update_id'] for u in updates) + 1

    for update in updates:
        msg = update.get('message') or update.get('edited_message')
        if not msg:
            continue

        msg_chat_id = str(msg.get('chat', {}).get('id', ''))
        if CHAT_ID and msg_chat_id != CHAT_ID:
            continue

        text = msg.get('text', '')
        if not text or 'data:' not in text.lower():
            continue

        record = parse_message(text)
        if not record:
            continue

        date_str = record.date.strftime('%d/%m/%Y')
        logger.info(f'Elaborazione contabilita per {date_str}')

        try:
            path = generate_excel(record, OUTPUT_DIR)
            logger.info(f'Excel aggiornato: {path}')

            sheets_note = ''
            if _SHEETS_OK and SHEET_ID:
                try:
                    sync_to_sheets(record, SHEET_ID)
                    sheets_note = '\n• Google Sheets aggiornato'
                except Exception as e:
                    logger.warning(f'Sheets sync fallito: {e}')
                    sheets_note = '\n• Sheets sync fallito'

            lines = [
                f'✅ Contabilità aggiornata — {date_str}',
                '',
                f'Entrate:   {record.totale_entrate:>10.2f} €',
                f'Spese:     {record.totale_spese:>10.2f} €',
                f'Stipendi:  {record.totale_stipendi:>10.2f} €',
                f'Borselli:  {record.totale_borselli:>10.2f} €',
                '─' * 30,
                f'Saldo:     {record.saldo:>10.2f} €',
                sheets_note,
            ]
            _send(msg_chat_id, '\n'.join(lines))

        except Exception as e:
            logger.exception(f'Errore elaborazione: {e}')
            _send(msg_chat_id, f'❌ Errore: {e}')

    _save_offset(new_offset)
    # Conferma a Telegram che i messaggi fino a new_offset sono stati letti
    requests.get(f'{_API}/getUpdates', params={'offset': new_offset}, timeout=10)
    logger.info(f'Offset aggiornato a {new_offset}')


if __name__ == '__main__':
    main()
