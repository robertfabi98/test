import json
import os

import gspread
from google.oauth2.service_account import Credentials

from parser import DayRecord, MESI_IT_INV

_SCOPES = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
]
_HEADERS = ['Data', 'Entrate', 'Spese', 'Stipendi', 'Borselli', 'Saldo']


def _client() -> gspread.Client:
    raw = os.environ.get('GOOGLE_CREDENTIALS_JSON', '')
    if not raw:
        raise EnvironmentError('GOOGLE_CREDENTIALS_JSON not set')
    creds = Credentials.from_service_account_info(json.loads(raw), scopes=_SCOPES)
    return gspread.Client(auth=creds)


def _get_or_create_ws(spreadsheet: gspread.Spreadsheet, title: str) -> gspread.Worksheet:
    try:
        return spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=title, rows=200, cols=10)
        ws.append_row(_HEADERS)
        return ws


def sync_to_sheets(record: DayRecord, sheet_id: str) -> None:
    client = _client()
    spreadsheet = client.open_by_key(sheet_id)

    month = MESI_IT_INV.get(record.date.month, '')
    tab_name = f'{month} {record.date.year}'
    ws = _get_or_create_ws(spreadsheet, tab_name)

    date_str = record.date.strftime('%d/%m/%Y')
    row_data = [
        date_str,
        round(record.totale_entrate, 2),
        round(record.totale_spese, 2),
        round(record.totale_stipendi, 2),
        round(record.totale_borselli, 2),
        round(record.saldo, 2),
    ]

    all_values = ws.get_all_values()
    for i, row in enumerate(all_values[1:], start=2):
        if row and row[0] == date_str:
            ws.update(f'A{i}:F{i}', [row_data])
            return

    ws.append_row(row_data)
