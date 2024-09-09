from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from flask import Flask, flash, request, redirect, Response, render_template, abort, session
from werkzeug.utils import secure_filename
from sqlalchemy import URL
import mimetypes
from Cryptodome.Cipher import ChaCha20
from Cryptodome.Random import get_random_bytes
from Cryptodome.Protocol.KDF import scrypt
from argon2 import PasswordHasher
import random
import string
import os

import model

CONTAINER_NAME = 'userfiles'

default_credential = DefaultAzureCredential()

account_url = "https://trashcancy.blob.core.windows.net"
blob_service_client = BlobServiceClient(account_url, credential=default_credential)

app = Flask(__name__)
app.config.from_prefixed_env()

connection_string = os.getenv('AZURE_SQL_CONNECTIONSTRING')
connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
app.config['SQLALCHEMY_DATABASE_URI'] = connection_url
model.db.init_app(app)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash("No file part")
        return redirect('/')
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect('/')
    filename = secure_filename(file.filename)
    password = request.form['password']
    encrypt = password != ''
    if encrypt:
        salt = get_random_bytes(16)
        key = scrypt(password, salt, 32, 2**20, 8, 1)
        cipher = ChaCha20.new(key=key)
        nonce = cipher.nonce
        password_hash = PasswordHasher().hash(password)
        file = cipher.encrypt(file.read())
    uri = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=uri)
    blob_client.upload_blob(file)
    if encrypt:
        model.new_file(encrypt, filename, uri, password_hash, salt, nonce)
    else:
        model.new_file(encrypt, filename, uri)
    return render_template('file.html', uri=uri, filename=filename)

@app.route('/dl/<uri>', methods=['GET', 'POST'])
def download_file(uri):
    if request.method == 'GET':
        file = model.get_file(uri)
        if file.encrypted:
            session['file_id'] = file.id
            return render_template('encrypted.html', uri=uri, filename=file.filename)
    else:
        file = model.db.get_or_404(model.Userfiles, session.get('file_id'))
        password = request.form['password']
        try:
            ph = PasswordHasher()
            ph.verify(file.password_hash, password)
        except:
            return 'unauthorized', 401
        key = scrypt(password, file.salt, 32, 2**20, 8, 1)
        cipher = ChaCha20.new(key=key, nonce=file.nonce)

    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=uri)
    stream = blob_client.download_blob()
    def generate_file():
        if not file.encrypted:
            for chunk in stream.chunks():
                yield chunk
            return
        for chunk in stream.chunks():
            yield cipher.decrypt(chunk)
    
    return Response(generate_file(), mimetype=mimetypes.guess_type(file.filename)[0])

@app.route('/')
def index():
    return render_template('index.html')