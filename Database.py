from sqlalchemy import create_engine, Column, String, UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
import os

from sqlalchemy.orm import sessionmaker

Base = declarative_base()
class OriginalDocs(Base):
    __tablename__ = 'original_documents'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    originaldocs = Column(String)

class Database:
    conn_string = f"postgresql+psycopg://{os.getenv('USER')}:{os.getenv('PASSWORD')}@{os.getenv('HOST')}/{os.getenv('DATABASE')}"
    engine = None
    database = None
    @staticmethod
    def getEngine():
        if not Database.engine:
            engine = create_engine(Database.conn_string)
        return engine

    @staticmethod
    def insertOriginalDocumentIntoDatabase(doc):
        print("insert started", doc)
        curr_engine = Database.getEngine()
        Session = sessionmaker(bind=curr_engine)
        session = Session()
        try:
            new_doc = OriginalDocs(originaldocs=doc)
            session.add(new_doc)
            session.commit()
            print("commited")
            return new_doc.id
        except Exception as e:
            session.rollback()
            print("error during commit", e)
            return None
        finally:
            session.close()





