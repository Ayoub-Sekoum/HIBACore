#!/bin/bash
# HOBA Backend Startup — Fix antenv PATH

export PYTHONPATH=$(pwd):/home/site/wwwroot:$PYTHONPATH

echo "--- HOBA Backend Starting ---"
echo "Working dir: $(pwd)"
echo "Python system: $(python --version 2>&1)"

# Attiva l'antenv di Oryx (dove pip ha installato i pacchetti)
ANTENV="/home/site/wwwroot/antenv"
if [ -f "$ANTENV/bin/activate" ]; then
    echo "Attivazione antenv: $ANTENV"
    source "$ANTENV/bin/activate"
    echo "Python antenv: $(python --version 2>&1)"
    echo "Gunicorn: $(which gunicorn 2>&1)"
else
    echo "WARNING: antenv non trovato in $ANTENV, uso PATH di sistema"
    echo "PATH: $PATH"
    # Cerca gunicorn in percorsi alternativi
    for dir in /usr/local/bin /usr/bin /home/.local/bin; do
        if [ -f "$dir/gunicorn" ]; then
            export PATH="$dir:$PATH"
            echo "Trovato gunicorn in $dir"
            break
        fi
    done
fi

echo "PYTHONPATH: $PYTHONPATH"
echo "sys.path: $(python -c 'import sys; print(sys.path)' 2>&1)"
echo "Contenuto dir corrente:"
ls -la

if [ -d "app" ]; then
    echo "Siamo nella cartella dell'app: $(pwd)"
else
    echo "Spostamento in /home/site/wwwroot"
    cd /home/site/wwwroot
fi
echo "Port: ${PORT:-8000}"
echo "Avvio gunicorn app.main:app ..."

exec gunicorn app.main:app \
  --worker-class uvicorn.workers.UvicornWorker \
  --workers 1 \
  --bind 0.0.0.0:${PORT:-8000} \
  --timeout 60 \
  --access-logfile - \
  --error-logfile -
