from sqlmodel import SQLModel, Session, create_engine

from .config import get_settings


settings = get_settings()
connect_args = {'check_same_thread': False} if settings.database_url.startswith('sqlite') else {}
engine_kwargs = {}
if not settings.database_url.startswith('sqlite'):
    engine_kwargs = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
engine = create_engine(settings.database_url, echo=False, connect_args=connect_args, **engine_kwargs)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
