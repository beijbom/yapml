from fastapi import Request
from sqlmodel import Session, create_engine

from yamlp.config import sqlite_url

engine = create_engine(sqlite_url, echo=True)


def get_session(request: Request):

    with Session(engine) as session:
        request.state.session = session
        yield session
