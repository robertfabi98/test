import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Optional

MESI_IT: Dict[str, int] = {
    'GENNAIO': 1, 'FEBBRAIO': 2, 'MARZO': 3, 'APRILE': 4,
    'MAGGIO': 5, 'GIUGNO': 6, 'LUGLIO': 7, 'AGOSTO': 8,
    'SETTEMBRE': 9, 'OTTOBRE': 10, 'NOVEMBRE': 11, 'DICEMBRE': 12,
}
MESI_IT_INV: Dict[int, str] = {v: k for k, v in MESI_IT.items()}

_SECTIONS = ('entrate', 'spese', 'stipendi', 'borselli')


@dataclass
class DayRecord:
    date: datetime
    entrate: Dict[str, float] = field(default_factory=dict)
    spese: Dict[str, float] = field(default_factory=dict)
    stipendi: Dict[str, float] = field(default_factory=dict)
    borselli: Dict[str, float] = field(default_factory=dict)

    @property
    def totale_entrate(self) -> float:
        return sum(self.entrate.values())

    @property
    def totale_spese(self) -> float:
        return sum(self.spese.values())

    @property
    def totale_stipendi(self) -> float:
        return sum(self.stipendi.values())

    @property
    def totale_borselli(self) -> float:
        return sum(self.borselli.values())

    @property
    def saldo(self) -> float:
        return self.totale_entrate - self.totale_spese - self.totale_stipendi - self.totale_borselli


def _parse_kv(line: str) -> Optional[tuple]:
    # Handles: 'Voce —> 100', 'Voce > 100', 'Voce——-> 100', 'Voce—> 100'
    m = re.match(r'^(.+?)\s*[-—>]+\s*([\d.,]+)\s*$', line.strip())
    if m:
        try:
            return m.group(1).strip(), float(m.group(2).replace(',', '.'))
        except ValueError:
            pass
    return None


def _parse_date(s: str) -> Optional[datetime]:
    parts = s.strip().split()
    if len(parts) == 3:
        month = MESI_IT.get(parts[1].upper())
        if month:
            try:
                return datetime(int(parts[2]), month, int(parts[0]))
            except ValueError:
                pass
    return None


def parse_message(text: str) -> Optional[DayRecord]:
    record: Optional[DayRecord] = None
    section: Optional[str] = None

    for raw in text.split('\n'):
        line = raw.strip()
        if not line:
            continue

        date_m = re.match(r'^data\s*:?\s*(.+)$', line, re.IGNORECASE)
        if date_m:
            dt = _parse_date(date_m.group(1))
            if dt:
                record = DayRecord(date=dt)
            continue

        if record is None:
            continue

        # Section headers: strip everything except letters and colon, then fullmatch keyword
        clean = re.sub(r'[^a-zA-Z:]', '', line).lower()
        new_sec = next((k for k in _SECTIONS if re.fullmatch(k + r':?', clean)), None)
        if new_sec:
            section = new_sec
            continue

        if section:
            kv = _parse_kv(line)
            if kv:
                getattr(record, section)[kv[0]] = kv[1]

    return record
