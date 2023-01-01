<h1 align="center">Spis Zadań Domowych</h1>

## Podstawowe informacje
Jest to bot na platformie Discord służący do zarządzania spisem zadań domowych i go wyświetlania.

## Instalacja
Spis pisany jest pod **Pythona 3.10**, więc niekoniecznie będzie działał na poprzednich wersjach.

Bot jest przygotowany pod użycie w Heroku, aczkolwiek można go też zainstalować manualnie:
```sh
$ git clone https://github.com/Kacper0510/SpisZadanDomowych
$ cd SpisZadanDomowych
$ python -m pip install -r requirements.txt
```

Należy następnie ustawić zmienne środowiskowe:
```
Spis_Token = string z Discordowym tokenem
Spis_Dev = opcjonalne; ID serwera, na którym rejestrowane są komendy developerskie
Spis_Autosave = opcjonalne; prawda|fałsz (domyślnie: prawda)
Spis_LogLevel = opcjonalne; DEBUG|INFO|WARNING|ERROR|CRITICAL (domyślnie: INFO)
```

Wszystko gotowe! Uruchom bota za pomocą:
```sh
$ python -m spis
```

## Komendy

### Globalne

> **/spis**

![Wyświetla aktualny stan spisu](https://cdn.discordapp.com/attachments/931884001680031754/1046541847713034342/image.png)

> **/info**

![Wyświetla statystyki i informacje o bocie](https://cdn.discordapp.com/attachments/931884001680031754/1046542237921722449/image.png)

### Dla edytorów

> **/dodaj zadanie**

![Dodaje nowe zadanie do spisu](https://cdn.discordapp.com/attachments/931884001680031754/1046542914056105984/image.png)

> **/dodaj ogloszenie**

![Dodaje nowe ogłoszenie do spisu](https://cdn.discordapp.com/attachments/931884001680031754/1046543246668595260/image.png)

> **/edytuj zadanie**

![Edytuje zadanie o podanym ID](https://cdn.discordapp.com/attachments/931884001680031754/1046544727945777202/image.png)

> **/edytuj ogloszenie**

![Edytuje ogłoszenie o podanym ID](https://cdn.discordapp.com/attachments/931884001680031754/1046544322012663839/image.png)

> **/usun**

![Usuwa zadanie lub ogłoszenie o podanym ID ze spisu](https://cdn.discordapp.com/attachments/931884001680031754/1046543944357519360/image.png)

### Dla developera

> **/dev zapisz**

![Zapisuje stan bota do pliku i wysyła go do twórcy bota](https://cdn.discordapp.com/attachments/931884001680031754/1046545104615252008/image.png)

> **/dev wczytaj**

![Wczytuje stan bota z kanału prywatnego twórcy bota (liczy się tylko ostatnia wiadomość)](https://cdn.discordapp.com/attachments/931884001680031754/1046545798558658650/image.png)

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
