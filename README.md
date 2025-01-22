# HA-Contarina
[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=davidedz&repository=https%3A%2F%2Fgithub.com%2Fdavidedz%2FHA-Contarina&category=Integrations)

Inserire nel file configuration.yaml questa configurazione, andando a personalizzare ```zone_id``` e ```name```.

```
sensor:
  - platform: contarina
    zone_id: 20
    name: "Svuotamenti"
    api_url: "https://contarina.it/ajax/moduli/appbugfix/api.test/ecocalendari"
```


Valori possibili per ```zone_id```:

* Cornuda: 38
* Cavaso del Tomba: 37
* Crocetta del Montello: 40
* Fonte: 41
* Castello di Godego: 36
* Castelfranco Veneto: 34
* Castelfranco Veneto: 35
* Asolo: 29
* Asolo: 30
* Borso del Grappa: 31
* Caerano di San Marco: 32
* Castelcucco: 33
* Istrana: 42
* Loria: 43
* Resana: 51
* Possagno: 50
* Riese Pio X: 52
* San Zenone degli Ezzelini: 53
* Trevignano: 54
* Ponzano Veneto: 15
* Pederobba: 49
* Maser: 44
* Monfumo: 45
* Montebelluna: 46
* Montebelluna: 47
* Altivole: 28
* Arcade: 4
* Morgano: 12
* Monastier di Treviso: 11
* Nervesa della Battaglia: 13
* Paese: 14
* Ponzano Veneto: 15
* Maserada sul Piave: 10
* Giavera del Montello: 9
* Breda di Piave: 5
* Carbonera: 6
* Casale sul Sile: 7
* Casier: 8
* Povegliano: 16
* Preganziol: 17
* Villorba: 24
* Treviso: 1
* Treviso: 2
* Treviso: 3
* Volpago del Montello: 25
* Zenson di Piave: 26
* Zero Branco: 27
* Susegana: 23
* Spresiano: 22
* Quinto di Treviso: 18
* Roncade: 19
* San Biagio di Callalta: 20
* Silea: 21
* Vedelago: 55
* Pieve del Grappa: 56
