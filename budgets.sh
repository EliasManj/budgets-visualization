#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"
source ./venv/bin/activate

# Parse arguments
UPDATE=false
RESET=false
ACCUMULATE=false
MONTH=$(date +%m) # Default to current month
YEAR=$(date +%Y)  # Default to current year

# Check if any process is listening on port 8000
echo "Checking for processes on port 8000"
if sudo lsof -i :8000 | grep -q 'uvicorn'; then
    echo "Process 'uvicorn' is running on port 8000. Killing the process..."
    echo "Retrieving PIDs"
    PIDS=$(sudo lsof -t -i :8000 | xargs)
    for PID in $PIDS; do
        echo "Killing process with PID $PID"
        sudo kill -9 $PID
        echo "Killed process with PID $PID"
    done
else
    echo "No process named 'uvicorn' is running on port 8000."
fi


for arg in "$@"
do
    case $arg in
        -u|--update)
        UPDATE=true
        shift # Remove --update from processing
        ;;
        -r|--reset)
        RESET=true
        shift # Remove --reset from processing
        ;;
        -a|--acc)
        ACCUMULATE=true
        shift # Remove --acc from processing
        ;;
        -m=*|--month=*)
        MONTH="${arg#*=}"
        shift # Remove --month= from processing
        ;;
        -y=*|--year=*)
        YEAR="${arg#*=}"
        shift # Remove --year= from processing
        ;;
    esac
done

if [ "$RESET" = true ] ; then
    echo "Deleting sqlite database"
    rm -f db/database.db
    echo "Recreating sqlite database from schema.sql"
    sqlite3 db/database.db < schema.sql
fi

# If update flag is set, run the Python import scripts
if [ "$UPDATE" = true ] || [ "$RESET" = true ] ; then
    python amex.py
    python bbva.py
    python banamex.py
    python cetes.py
fi

sqlite3 db/database.db < db/modifications.sql
uvicorn api.main:app --host 0.0.0.0 --port 8000
