import re
from datetime import datetime, timedelta, date
from logging import getLogger

from dateutil.parser import parserinfo, ParserError, parser
from dateutil.relativedelta import relativedelta

__all__ = "PolskiDateParser", "ParserError"
logger = getLogger(__name__)

JUTRO_REGEX = re.compile("jutro", re.IGNORECASE)  # Regex do znajdowania słowa "jutro" w tekście


class _PolskiDateParser(parserinfo, parser):
    """Klasa rozszerzająca parser i przy okazji parserinfo z dateutil.
    Pozwala ona na wprowadzanie dat w polskim formacie."""

    MONTHS = [
        ('sty', 'stycznia', 'styczeń', 'styczen', 'I'),
        ('lut', 'lutego', 'luty', 'II'),
        ('mar', 'marca', 'marzec', 'III'),
        ('kwi', 'kwietnia', 'kwiecień', 'kwiecien', 'IV'),
        ('maj', 'maja', 'V'),
        ('cze', 'czerwca', 'czerwiec', 'VI'),
        ('lip', 'lipca', 'lipiec', 'VII'),
        ('sie', 'sierpnia', 'sierpień', 'sierpien', 'VIII'),
        ('wrz', 'września', 'wrzesnia', 'wrzesień', 'wrzesien', 'IX'),
        ('paź', 'października', 'paz', 'pazdziernika', 'październik', 'pazdziernik', 'X'),
        ('lis', 'listopada', 'listopad', 'XI'),
        ('gru', 'grudnia', 'grudzień', 'grudzien', 'XII')
    ]

    WEEKDAYS = [
        ('pn', 'poniedziałek', 'poniedzialek', 'pon', 'po'),
        ('wt', 'wtorek', 'wto'),
        ('śr', 'środa', 'sr', 'sroda', 'śro', 'sro'),
        ('cz', 'czwartek', 'czw'),
        ('pt', 'piątek', 'piatek', 'pią', 'pia', 'pi'),
        ('sb', 'sobota', 'sob', 'so'),
        ('nd', 'niedziela', 'nie', 'ni', 'ndz')
    ]

    def __init__(self):
        parserinfo.__init__(self, True, False)  # Poprawne ustawienie formatu DD.MM.RR
        parser.__init__(self, self)  # Ustawienie parserinfo na self

    # noinspection PyMethodMayBeStatic
    def _build_naive(self, res, default: datetime) -> tuple[datetime, datetime]:
        """Nadpisane, aby naprawić problem z datami w przeszłości.
        Teraz zwraca tuple dwóch dat, zgodnie z opisem w docstringu parse()."""
        logger.debug(f"Parsowanie daty - surowe dane: {res}")
        replacement = {}
        for attr in ("year", "month", "day", "hour", "minute", "second", "microsecond"):
            if (v := getattr(res, attr)) is not None:  # Note to self: nie zapominać o nawiasie w walrusie
                replacement[attr] = v

        default = default.replace(**replacement)
        now = datetime.now()

        if res.weekday is not None:
            if res.day is None:
                default += timedelta(days=1)  # Nie pozwalamy na zwrócenie dzisiaj
            # Znajduje następny oczekiwany przez użytkownika dzień tygodnia
            default += timedelta(days=(res.weekday + 7 - default.weekday()) % 7)

        if default < now:  # Naprawa błędu z datą w przeszłości zamiast z najbliższą datą
            if res.hour is not None and res.day is None and res.weekday is None:
                default += timedelta(days=1)
            elif res.day is not None and res.month is None:
                default += relativedelta(months=1)
            elif res.month is not None and res.year is None:
                default += relativedelta(years=1)

        # Data usunięcia przesunięta odpowiednio do przodu od daty podanej przez użytkownika, zgodnie z sugestiami KK
        data_usuniecia = default
        # Przesuń godzinę do przodu o 45 min, chyba że użytkownik naprawdę wie, co robi (podał dużą dokładność)
        if res.second is None and res.microsecond is None:
            data_usuniecia += timedelta(minutes=45)
            # Przesuń godzinę na 16:00, jeśli użytkownik nie podał w ogóle godziny
            if res.hour is None and res.minute is None:
                data_usuniecia += timedelta(hours=15, minutes=15)  # 15:15 + 45 min = 16:00

        logger.debug(f"Parsowanie daty - wynik: {default}, {data_usuniecia}")
        return default, data_usuniecia

    # noinspection PyUnresolvedReferences
    def parse(self, timestr, default=None, ignoretz=False, tzinfos=None, **kwargs) -> tuple[datetime, datetime]:
        """Nadpisanie parser.parse - zwraca dwie daty zamiast jednej.
        Pierwszy datetime to prawdziwa data podana przez użytkownika, a drugi - zmodyfikowana data usunięcia zadania."""
        # Zamiana "jutro" na odpowiednią datę z zachowaniem pozostałych parametrów
        timestr = JUTRO_REGEX.sub((date.today() + timedelta(days=1)).strftime("%d.%m.%y"), timestr)

        # Kod skopiowany w większości z oryginalnej implementacji
        if default is None:
            default = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        res = self._parse(timestr, **kwargs)[0]  # Ignorujemy resztę zwracanego tuple
        if res is None:
            raise ParserError("Unknown string format: %s", timestr)
        if len(res) == 0:
            raise ParserError("String does not contain a date: %s", timestr)
        try:
            p, m = self._build_naive(res, default)
        except ValueError as e:
            raise ParserError(str(e) + ": %s", timestr) from e
        if not ignoretz:
            p, m = self._build_tzaware(p, res, tzinfos), self._build_tzaware(m, res, tzinfos)
        return p, m


PolskiDateParser = _PolskiDateParser()  # Żeby nie tworzyć więcej niż jedną instancję
