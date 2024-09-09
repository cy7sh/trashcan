from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from flask import Flask, flash, request, redirect, Response, render_template
from werkzeug.utils import secure_filename
import mimetypes
from Cryptodome.Cipher import ChaCha20
from Cryptodome.Random import get_random_bytes
from Cryptodome.Protocol.KDF import scrypt
from argon2 import PasswordHasher
import random
import string
import struct

import model

CONTAINER_NAME = 'userfiles'
SQL_COPT_SS_ACCESS_TOKEN = 1256

default_credential = DefaultAzureCredential()

account_url = "https://trashcancy.blob.core.windows.net"
blob_service_client = BlobServiceClient(account_url, credential=default_credential)

app = Flask(__name__)

token_bytes = default_credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
token_struct = struct.pack(f'<I{len(token_bytes)}s', len(token_bytes), token_bytes)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc:///?odbc_connect=Driver%3D%7BODBC+Driver+18+for+SQL+Server%7D%3BServer%3Dtcp%3Atrashcan.database.windows.net%2C1433%3BDatabase%3Dtrashcandb%3BEncrypt%3Dyes%3BTrustServerCertificate%3Dno%3BConnection+Timeout%3D30'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'connect_args': {'attrs_before': {SQL_COPT_SS_ACCESS_TOKEN: token_struct}}}
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

@app.route('/dl/<uri>')
def download_file(uri):
    file = model.get_file(uri)
    if file.encrypted:
        return
    def generate_file():
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=uri)
        stream = blob_client.download_blob()
        for chunk in stream.chunks():
            yield chunk
    
    return Response(generate_file(), mimetype=mimetypes.guess_type(file.filename)[0])

@app.route('/')
def index():
    return render_template('index.html')