from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional
from sqlalchemy import select

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Userfiles(db.Model):
    __tablename__ = "userfiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    encrypted: Mapped[bool]
    password_hash: Mapped[Optional[str]]
    filename: Mapped[str]
    uri: Mapped[str]
    salt: Mapped[Optional[bytes]]
    nonce: Mapped[Optional[bytes]]

def new_file(encrypted, filename, uri, password_hash='', salt='', nonce=''):
    if encrypted:
        file = Userfiles(encrypted=encrypted, filename=filename, uri=uri, password_hash=password_hash, salt=salt, nonce=nonce)
    else:
        file = Userfiles(encrypted=encrypted, filename=filename, uri=uri)
    db.session.add(file)
    db.session.commit()

def get_file(uri):
    statement = select(Userfiles).filter_by(uri=uri)
    userfiles_obj = db.one_or_404(statement)
    return userfiles_obj