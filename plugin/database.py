from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os


engine = None


def init_engine(**kwargs):
    """Initiate database engine."""
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    global engine
    engine = create_engine(SQLALCHEMY_DATABASE_URI, **kwargs)
    return engine


def get_db_session():
    """
    Create an independent database session/connection per request. Use the same session through all the request and
    then close it after the request is finished.
    """
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


