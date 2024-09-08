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

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'docx'}
CONTAINER_NAME = 'userfiles'

try:
    account_url = "https://trashcancy.blob.core.windows.net"
    default_credential = DefaultAzureCredential()

    blob_service_client = BlobServiceClient(account_url, credential=default_credential)

except Exception as ex:
    print('Exception:')
    print(ex)

app = Flask(__name__)
app.secret_key = 'super secret key'

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
    if password:
        salt = get_random_bytes(16)
        key = scrypt(password, salt, 32, 2**20, 8, 1)
        cipher = ChaCha20.new(key=key)
        password_hash = PasswordHasher().hash(password)
        file = cipher.encrypt(file.read())
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=filename)
    blob_client.upload_blob(file)
    url = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    return render_template('file.html', filename=filename)

@app.route('/file/<name>')
def download_file(name):
    def generate_file():
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=name)
        stream = blob_client.download_blob()
        for chunk in stream.chunks():
            yield chunk
    return Response(generate_file(), mimetype=mimetypes.guess_type(name)[0])

@app.route('/')
def index():
    return render_template('index.html')