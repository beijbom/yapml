from fastapi import Request
from sqlmodel import Session, create_engine
from yamlp.config import sqlite_url

engine = create_engine(
    sqlite_url,
    echo=False,  # Set to False in production to avoid logging all SQL statements
    connect_args={
        "check_same_thread": False,  # Allows multiple threads to access the database
        "timeout": 30,  # Adds timeout for busy connections
    },
    pool_pre_ping=True,  # Validates connections before using them
    pool_recycle=3600,  # Recycle connections after 1 hour
)


def get_session(request: Request):

    with Session(engine) as session:
        request.state.session = session
        yield session
