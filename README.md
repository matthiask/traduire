# forum-pfarrblatt.ch

Link zur Preview-Umgebung:

[forum-pfarrblatt-preview.feinheit.dev](https://forum-pfarrblatt-preview.feinheit.dev/)


## Lokale Installation

Zusätzlich zu den gewöhnlichen Voraussetzungen müssen postgis und gdal
installiert werden, gemäss der Installationsanleitung in der offiziellen Django
Dokumentation: https://docs.djangoproject.com/en/5.0/ref/contrib/gis/

Im `.env` steht bei der `DATABASE_URL` als Protokoll `postgres://`, das muss
ersetzt werden durch  `postgis://`
