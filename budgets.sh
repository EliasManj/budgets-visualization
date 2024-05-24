#!/bin/bash

# Navigate to the project directory
cd /home/emanjarrez/code/python/budgets-visualization

# Parse arguments
UPDATE=false
RESET=false
ACCUMULATE=fasle
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
    esac
done

# If reset flag is set, run docker-compose down -v
if [ "$RESET" = true ] ; then
    echo "Resetting Docker Compose environment..."
    docker-compose down -v
fi

# Start Docker Compose
docker-compose up -d

# Wait for Docker Compose to fully start services
echo "Waiting for Docker services to start..."
sleep 10  # Adjust sleep time as needed

# Activate the Python virtual environment
source ./myenv/bin/activate

# If update flag is set, run the Python import scripts
if [ "$UPDATE" = true ] || [ "$RESET" = true ] ; then
    python import_amex.py
    python import_bbva.py
    python import_bbva_debit.py
fi

# Get the current year and month
YEAR=$(date +%Y)
MONTH=$(date +%m)

if [ "$ACCUMULATE" = true ] ; then
    # Run the accumulate_budget.py script with the current year and month
    python accumulate_budget.py --year "$YEAR" --month "$MONTH"
fi

# Convert the Jupyter notebook to a Python script and execute it
#jupyter nbconvert --to script Visualize.ipynb
panel serve Visualize.py
sleep 5  # Adjust sleep time as needed
echo "Running at http://localhost:5006/Visualize"