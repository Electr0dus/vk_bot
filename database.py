from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime


Base = declarative_base()

class SavedMessage(Base):
    __tablename__ = 'saved_messages'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    image_path = Column(String)
    image_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message {self.id} from user {self.user_id}>'


# инициализация БД
engine = create_engine('sqlite:///data_msg.db', echo=False)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
