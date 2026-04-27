#!/usr/bin/env python3
import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from excel_generator import generate_excel
from parser import parse_message

try:
    from sheets_sync import sync_to_sheets
    _SHEETS_OK = True
except ImportError:
    _SHEETS_OK = False

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
if not TOKEN:
    raise SystemExit('Errore: imposta la variabile TELEGRAM_BOT_TOKEN')

ALLOWED = {int(x) for x in os.environ.get('ALLOWED_CHAT_IDS', '').split(',') if x.strip()}
OUTPUT_DIR = os.environ.get('OUTPUT_DIR', 'contabilita')
SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')


def _allowed(chat_id: int) -> bool:
    return not ALLOWED or chat_id in ALLOWED


async def cmd_start(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Bot di contabilità pronto.\n\n'
        'Inviami il messaggio giornaliero nel formato:\n\n'
        'Data: GG MESE AAAA\n\n'
        'ENTRATE——\n'
        'Voce —> importo\n\n'
        'SPESE——\n'
        'Voce —> importo\n\n'
        'STIPENDI——\n'
        'Nome —> importo\n\n'
        'BORSELLI\n'
        'Voce —> importo'
    )


async def handle_text(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    if not _allowed(update.effective_chat.id):
        return

    text = update.message.text or ''
    record = parse_message(text)

    if not record:
        await update.message.reply_text(
            'Messaggio non riconosciuto.\n'
            'Assicurati di includere la riga:\n'
            'Data: GG MESE AAAA'
        )
        return

    await update.message.reply_text('Elaborazione in corso…')

    try:
        path = generate_excel(record, OUTPUT_DIR)

        sheets_note = ''
        if _SHEETS_OK and SHEET_ID:
            try:
                sync_to_sheets(record, SHEET_ID)
                sheets_note = '\n• Google Sheets aggiornato'
            except Exception as e:
                logger.warning(f'Sheets sync fallito: {e}')
                sheets_note = '\n• Sheets sync fallito'

        lines = [
            f'Data: {record.date.strftime("%d/%m/%Y")}',
            '',
            f'Entrate:   {record.totale_entrate:>10.2f} €',
            f'Spese:     {record.totale_spese:>10.2f} €',
            f'Stipendi:  {record.totale_stipendi:>10.2f} €',
            f'Borselli:  {record.totale_borselli:>10.2f} €',
            '─' * 30,
            f'Saldo:     {record.saldo:>10.2f} €',
            '',
            f'File: {os.path.basename(path)}{sheets_note}',
        ]
        await update.message.reply_text('\n'.join(lines))

        with open(path, 'rb') as fh:
            await update.message.reply_document(
                document=fh,
                filename=os.path.basename(path),
            )

    except Exception as e:
        logger.exception('Errore elaborazione messaggio')
        await update.message.reply_text(f'Errore: {e}')


def main() -> None:
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', cmd_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info('Bot avviato')
    app.run_polling()


if __name__ == '__main__':
    main()
