#!/bin/sh
# Baut aus neonkueste.html (Artifact-Quelle) die eigenständige index.html.
cd "$(dirname "$0")"
{ printf '<!doctype html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">\n'
  sed -n '1,/^<\/style>/p' neonkueste.html
  printf '</head>\n<body>\n'
  sed -n '/^<\/style>/,$p' neonkueste.html | tail -n +2
  printf '</body>\n</html>\n'; } > index.html
