import boto3
from dotenv import load_dotenv
import os

load_dotenv() # loads environment variables from .env (this includes AWS keys)


# connecting to dynamodb 
dynamodb = boto3.resource('dynamodb', region_name = 'us-east-1')

# tring to create new table name : login
# if this exist then it will skip

try: 
    table = dynamodb.create_table(
        TableName = 'login',
        KeySchema = [
            {
                'AttributeName' : 'email',
                'KeyType' : 'HASH'
            }
        ],
        AttributeDefinitions = [
            {
                'AttributeName' : 'email',
                'AttributeType' : 'S' # string type
            }
        ],
        ProvisionedThroughput = {
            'ReadCapacityUnits' : 5, #Basic read capacity
            'WriteCapacityUnits' : 5 #Basic write capacity
        }
    )

    # Wait until AWS finishes creating the table
    table.wait_until_exists()
    print("Table 'login' created")

except dynamodb.meta.client.exceptions.ResourceInUseException:
    table = dynamodb.Table('login')
    print("Table 'login' already exists.")


# Student details to use for genearting test users

student_id = 's4035321'
first_name = 'Suyash'
last_name = 'Alekar'

with table.batch_writer() as batch:
    for i in range(10):
        email = f'{student_id}{i}@student.rmit.edu.au' 
        username = f'{first_name}{last_name}{i}'
        password = f'{i}01234'


        batch.put_item(
            Item = {
                'email' : email,
                'user_name' : username,
                'password' : password
            }
        )

        print(f'Added : {email}')

print("All users added.")