import yaml
import re

def load_keywords():
    with open("keywords.yaml", "r") as file:
        keywords = yaml.safe_load(file)
        return keywords

def infer_tag(data, description):
    description = description.lower()
    description = ' '.join(description.split())
    # Iterate through each category and its keywords/regex
    for category, patterns in data.items():
        for pattern in patterns:
            # Check for match using regex (case-insensitive)
            if re.search(pattern, description, re.IGNORECASE):
                return category.capitalize()
    return "Other"