#!/bin/bash

# Navigate to the project directory
cd /home/emanjarrez/code/python/budgets-visualization
source myenv/bin/activate

# Parse arguments
UPDATE=false
RESET=false
ACCUMULATE=false
MONTH=$(date +%m) # Default to current month
YEAR=$(date +%Y)  # Default to current year

# Check if any process named "panel" is listening on port 5006
if sudo lsof -i :5006 | grep -q 'panel'; then
    echo "Process 'panel' is running on port 5006. Killing the process..."
    
    # Get the PID of the process named "panel" listening on port 5006
    PIDS=$(sudo lsof -t -i :5006 | xargs)

    # Kill the process
    for PID in $PIDS; do
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

# Activate the Python virtual environment
source ./myenv/bin/activate

# If update flag is set, run the Python import scripts
if [ "$UPDATE" = true ] || [ "$RESET" = true ] ; then
    python import_amex.py
    python import_bbva.py
    python import_bbva_debit.py
fi

sqlite3 db/database.db < db/modifications.sql

if [ "$ACCUMULATE" = true ] ; then
    # Run the accumulate_budget.py script with the specified year and month
    python accumulate_budget.py --year "$YEAR" --month "$MONTH"
fi

# Convert the Jupyter notebook to a Python script and execute it
jupyter nbconvert --to script Visualize.ipynb
panel serve Visualize.py &
