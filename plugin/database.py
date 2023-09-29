from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config import Config


# engine = None
#
#
# def init_engine(config=Config(), **kwargs):
#     """Initiate database engine."""
#     global engine
#     engine = create_engine(config.SQLALCHEMY_DATABASE_URI, **kwargs)
#     return engine
#
#
# def get_db_session():
#     """
#     Create an independent database session/connection per request. Use the same session through all the request and
#     then close it after the request is finished.
#     """
#     session_factory = sessionmaker(autocommit=False, autoflush=False, bind=init_engine())
#     session = session_factory()
#     try:
#         yield session
#     finally:
#         session.close()
#

def get_db_session(config=Config()):
    """
    Create an independent database session/connection per request. Use the same session through all the request and
    then close it after the request is finished.
    """
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI)

    with Session(engine) as session:
        return session
