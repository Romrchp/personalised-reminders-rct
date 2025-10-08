from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from src.config.logging_config import Logger

logger = Logger('myfoodrepo.db_session').get_logger()

engine = None
Session = None


def init_db(db_uri):
    global engine
    global Session
    engine = create_engine(db_uri)
    Session = scoped_session(sessionmaker(bind=engine))


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    global Session
    if Session is None:
        raise RuntimeError("Session not initialized. Call init_db() before using session_scope.")
    session = Session()
    logger.debug("Session started")
    try:
        yield session
        session.commit()
        logger.debug("✅ Session committed")
    except Exception as e:
        session.rollback()
        logger.error("🛑 Session rollback due to exception: %s", e)
        raise
    # finally:
        # session.expunge_all()
        # logger.debug("Session closed")
