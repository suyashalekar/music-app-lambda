import boto3.dynamodb
import boto3.dynamodb.conditions
from flask import Flask, render_template,request,redirect,url_for,session,flash
import boto3
from dotenv import load_dotenv
import os
import copy 

# Load AWS credentials from .env file
load_dotenv() 

app = Flask(__name__)
app.secret_key = "super-secret-key"

dynamodb = boto3.resource('dynamodb',region_name = 'us-east-1')
bucket_name = "suyash-music-image-bucket"
s3 = boto3.client('s3', region_name = 'us-east-1')

#Reference to 'login' table

login_table = dynamodb.Table('login')

# --------------------------
# ROUTE 1: Login Page (/)
# --------------------------
@app.route('/', methods = ["GET","POST"])
def login():
    if request.method == 'POST':
        # Get from input form
        email = request.form['email']
        password = request.form['password']

        print(email,'\n',password)

        # Searching email and passwords in DynamoDB
        response = login_table.get_item(Key = {'email' : email})
        user = response.get('Item') #This will be None if user not found

        #Validate password
        if user and user['password'] == password:

            #Store user information in session
            session['username'] = user['user_name']
            session['email'] = user['email']

            return redirect(url_for('main'))
        else:
            print('❌ Email or password is incorrect.')
            flash('❌ Email or password is incorrect.')

    return render_template('login.html') # Show the form

# --------------------------
# ROUTE 2: Dashboard Page (/dashboard)
# --------------------------
@app.route('/dashboard')
def dashboard():
    #Only allow access if user is logged in
    if 'username' in session:
        return f"Welcome, {session['username']}! Your logged in."
    else:
        return redirect(url_for('login'))

# --------------------------
# ROUTE 3: Register Page (/register)
# --------------------------
@app.route('/register', methods = ['GET','POST'])
def register():
    if request.method == "POST":
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']

        #Checking if email is already registerd
        response = login_table.get_item(Key = {'email' : email})
        existing_user = response.get('Item')

        if existing_user:
            flash('❌ Email already registered. Try logging in instead.')
            print('❌ Email already registered. Try logging in instead.')
            return redirect(url_for('register'))
        
        # if email not found, create new user
        login_table.put_item(Item = {
            'email' : email,
            'user_name' : username,
            'password' : password
        })
        
        flash('✅ Registered successfully! Please log in.')
        return  redirect(url_for('login'))
    return render_template('register.html')

# --------------------------
# ROUTE 4: Main Dashboard Page (/main)
# --------------------------

@app.route('/main')
def main():
    if 'username' not in session or 'email' not in session:
        return redirect(url_for('login'))
    
    email = session['email']
    username = session['username']

    # Get subscriptions
    subs_table = dynamodb.Table('subscriptions')
    sub_response = subs_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(email)
    )
    subscribed_titles = [item['song_title'] for item in sub_response['Items']]

    # Get all songs
    music_table = dynamodb.Table('music')
    music_response = music_table.scan()
    all_songs = music_response.get('Items', [])

    # Get subscribed songs only (with deepcopy to avoid shared refs)
    subscribed_songs = [copy.deepcopy(song) for song in all_songs if song['title'] in subscribed_titles]

    # Add image URLs
    for song in subscribed_songs:
        song['subscribed'] = True
        img = song.get('image_url', '')
        if img:
            filename = img.split('/')[-1]
            try:
                song['image_url'] = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': filename},
                    ExpiresIn=3600
                )
            except:
                song['image_url'] = ""

    return render_template(
        'main.html',
        user=username,
        subscribed_songs=subscribed_songs,
        query_results=[]  # nothing queried yet
    )


   

@app.route('/subscribe',methods=["POST"])
def subscribe():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    title = request.form['title']
    artist = request.form['artist']
    email = session['email']

    subs_table = dynamodb.Table('subscriptions')
    subs_table.put_item(Item = 
        {'email' : email,
        'song_title' : title,
        'artist' : artist})
    
    return redirect(url_for('main'))

@app.route('/unsubscribe',methods = ['POST'])
def unsubscribe():
    if 'email' not in session:
        return redirect(url_for('login'))
    title = request.form['title']
    email = session['email']

    subs_table = dynamodb.Table('subscriptions')
    subs_table.delete_item(
        Key = {
            'email' : email,
            'song_title' : title 
        }
    )
    return redirect(url_for('main'))



@app.route('/query', methods=['POST'])
def query():
    if 'email' not in session or 'username' not in session:
        return redirect(url_for('login'))

    email = session['email']
    username = session['username']

    # Form input
    title = request.form.get('title', '').strip().lower()
    artist = request.form.get('artist', '').strip().lower()
    year = request.form.get('year', '').strip().lower()
    album = request.form.get('album', '').strip().lower()

    if not (title or artist or year or album):
        flash("Please enter at least one field to search.")
        return redirect(url_for('main'))

    # Get all songs
    music_table = dynamodb.Table('music')
    response = music_table.scan()
    all_songs = response.get('Items', [])

    # Filter query results
    query_results = []
    for song in all_songs:
        if title and title not in song['title'].lower():
            continue
        if artist and artist not in song['artist'].lower():
            continue
        if year and year != song['year']:
            continue
        if album and album not in song['album'].lower():
            continue
        query_results.append(copy.deepcopy(song))  # Important!

    # Get subscriptions
    subs_table = dynamodb.Table('subscriptions')
    sub_response = subs_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('email').eq(email)
    )
    subscribed_titles = set(item['song_title'] for item in sub_response['Items'])

    # Add image URL and subscription flag to query results
    for song in query_results:
        song['subscribed'] = song['title'] in subscribed_titles
        img = song.get('image_url', '')
        if img:
            filename = img.split('/')[-1]
            try:
                song['image_url'] = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': filename},
                    ExpiresIn=3600
                )
            except:
                song['image_url'] = ""

    # Subscribed songs for display (again, deep copy!)
    subscribed_songs = [copy.deepcopy(song) for song in all_songs if song['title'] in subscribed_titles]
    for song in subscribed_songs:
        song['subscribed'] = True
        img = song.get('image_url', '')
        if img:
            filename = img.split('/')[-1]
            try:
                song['image_url'] = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': bucket_name, 'Key': filename},
                    ExpiresIn=3600
                )
            except:
                song['image_url'] = ""

    if not query_results:
        flash("No result is retrieved. Please query again.")

    return render_template(
        'main.html',
        user=username,
        subscribed_songs=subscribed_songs,
        query_results=query_results
    )

@app.route('/logout')
def logout():
    session.clear() #Clear all session variables
    return redirect(url_for('login'))

if __name__=='__main__':
    app.run(debug=True)

