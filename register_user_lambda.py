import boto3
import json 

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('login')

def lambda_handler(event,context):
    data = json.loads(event['body'])

    email = data['email']
    username = data['username']
    password = data['password']

    #Check if already registerd
    
    existing_user = table.get_item(Key = {'email' : email}).get('Item')
    if existing_user:
        return { 
            'statusCode' : 409,
            'body' : json.dumps({'message' : 'Email already registerd'})
        }
    
    table.put_item(Item = {
        'email' : email,
        'user_name' : username,
        'password' : password
    })

    return {
        'statusCode' : 200,
        'body' : json.dumps({'message': "User registered successfully"})
    }

