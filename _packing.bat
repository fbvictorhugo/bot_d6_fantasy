@ECHO OFF
:: This CMD packing files.
TITLE Packing

set data=%date:~-4%%date:~3,2%%date:~0,2%%time:~0,2%%time:~3,2%%time:~6,2%
set zipname=ds_fantasy.zip

7z a -tzip %zipname% -r . -x!*.git* -x!*.md -x!*.bat -x!*.zip -x!__pycache__ -x!*.db