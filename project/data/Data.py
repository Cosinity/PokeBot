# Holds various data and functions
from DataReader import DataReader
import json

POKEMON_DATA = DataReader.read_usage_stats()
TEAMS_DATA = DataReader.read_teams()

# Get the credentials for our training and testing accounts
f = open('credentials.json', 'r')
creds_json = f.read()
f.close()
CREDS = json.loads(creds_json)
TESTING_NAME = CREDS['ladderName']
TESTING_PASSWORD = CREDS['ladderPassword']
TRAINING_NAME_1 = CREDS['trainingName1']
TRAINING_NAME_2 = CREDS['trainingName2']
TRAINING_PASSWORD = CREDS['trainingPassword']
