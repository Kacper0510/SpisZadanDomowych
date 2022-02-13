<h1 align="center">Spis Zadań Domowych</h1>

## Podstawowe informacje
Jest to bot na platformie Discord służący do zarządzania spisem zadań domowych i go wyświetlania.

## Instalacja
Spis pisany jest pod **Pythona 3.10**, więc niekoniecznie będzie działał na poprzednich wersjach.

Bot jest przygotowany pod użycie w Heroku, aczkolwiek można go też zainstalować manualnie:
```sh
$ git clone https://github.com/Kacper0510/SpisZadanDomowych
$ cd SpisZadanDomowych
$ python3 -m pip install -r requirements.txt
```

Należy następnie ustawić zmienne środowiskowe:
```
Spis_Token = string z Discordowym tokenem
Spis_Edytor = rola odpowiadająca za edycję spisu (w formacie <id_roli>:<id_serwera>)
Spis_Dev = rola mająca dostęp do komend developerskich (w formacie <id_roli>:<id_serwera>)
Spis_Autosave = opcjonalne, prawda|fałsz (domyślnie: prawda)
Spis_LogLevel = opcjonalne, DEBUG|INFO|WARNING|ERROR|CRITICAL (domyślnie: INFO)
```

Wszystko gotowe! Uruchom bota za pomocą:
```sh
$ python3 spis.py
```

## Komendy

### Globalne

> **/spis** [dodatkowe_opcje: string do wyboru (domyślnie: Brak)]

![Wyświetla aktualny stan spisu](https://cdn.discordapp.com/attachments/931884001680031754/938780030874583060/unknown.png)

### Dla edytorów

> **/dodaj_zadanie <opis: string> <termin: data|godzina|dzień tygodnia>** [przedmiot: string do wyboru (domyślnie: Inny)]

![Dodaje nowe zadanie do spisu](https://cdn.discordapp.com/attachments/931884001680031754/938780752382918666/unknown.png)

> **/usun_zadanie <id: liczba w formacie szesnastkowym>**

![Usuwa zadanie o podanym ID ze spisu](https://cdn.discordapp.com/attachments/931884001680031754/938165033106538526/unknown.png)

### Dla developera

> **/zapisz_stan**

![Zapisuje stan bota do pliku i wysyła go do twórcy bota](https://cdn.discordapp.com/attachments/931884001680031754/938781136576999535/unknown.png)

> **/wczytaj_stan**

![Wczytuje stan bota z kanału prywatnego twórcy bota (liczy się tylko ostatnia wiadomość)](https://cdn.discordapp.com/attachments/931884001680031754/938785280188620800/unknown.png)

## Format daty

Data/godzina przekazywana do bota np. w komendzie **/dodaj_zadanie** zamieniana jest na obiekt typu datetime przez moduł `dateutil.parser`.
Dzięki temu większość polskich formatów dat zostaje przyjęta i poprawnie zamieniona.

Użytkownik może podać datę, godzinę, dzień tygodnia lub kilka z tych rzeczy naraz.
W przypadku niejednoznacznych dat (np. **01.02.03**), domyślny format to **DD.MM.RR**.

### Dozwolone oznaczenia miesięcy

| Numer | Skrót       | Odmieniona nazwa              | Pełna nazwa                 | Cyfra rzymska |
|-------|-------------|-------------------------------|-----------------------------|---------------|
| 01    | sty         | stycznia                      | styczeń<br/>styczen         | I             |
| 02    | lut         | lutego                        | luty                        | II            |
| 03    | mar         | marca                         | marzec                      | III           |
| 04    | kwi         | kwietnia                      | kwiecień<br/>kwiecien       | IV            |
| 05    | maj         | maja                          | maj                         | V             |
| 06    | cze         | czerwca                       | czerwiec                    | VI            |
| 07    | lip         | lipca                         | lipiec                      | VII           |
| 08    | sie         | sierpnia                      | sierpień<br/>sierpien       | VIII          |
| 09    | wrz         | września<br/>wrzesnia         | wrzesień<br/>wrzesien       | IX            |
| 10    | paź<br/>paz | października<br/>pazdziernika | październik<br/>pazdziernik | X             |
| 11    | lis         | listopada                     | listopad                    | XI            |
| 12    | gru         | grudnia                       | grudzień<br/>grudzien       | XII           |

### Dozwolone oznaczenia dni tygodnia

| Numer | 2-literowy skrót | Pełna nazwa                   | 3-literowy skrót |
|-------|------------------|-------------------------------|------------------|
| 1     | pn<br/>po        | poniedziałek<br/>poniedzialek | pon              |
| 2     | wt               | wtorek                        | wto              |
| 3     | śr<br/>sr        | środa<br/>sroda               | śro<br/>sro      |
| 4     | cz               | czwartek                      | czw              |
| 5     | pt<br/>pi        | piątek<br/>piatek             | pią<br/>pia      |
| 6     | sb<br/>so        | sobota                        | sob              |
| 7     | nd<br/>ni        | niedziela                     | nie<br/>ndz      |
