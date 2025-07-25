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

# Check if any process named "panel" is listening on port 5006
echo "Checking for panel processes on port 5006"
if sudo lsof -i :5006 | grep -q 'panel'; then
    echo "Process 'panel' is running on port 5006. Killing the process..."
    # Get the PID of the process named "panel" listening on port 5006
    echo "Retrieving PIDs"
    PIDS=$(sudo lsof -t -i :5006 | xargs)
    # Kill the process
    for PID in $PIDS; do
        echo "Killing process with PID $PID"
        sudo kill -9 $PID
        echo "Killed process with PID $PID"
    done
else
    echo "No process named 'panel' is running on port 5006."
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
    python bbva_debit.py
    python banamex.py
    python cetes.py
fi

sqlite3 db/database.db < db/modifications.sql
panel serve Visualize.py --show --log-level debug
