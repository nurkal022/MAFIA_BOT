from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    phone_number = Column(String)
    games_played = Column(Integer, default=0)
    mafia_games = Column(Integer, default=0)
    doctor_games = Column(Integer, default=0)
    crystals = Column(Integer, default=0)
    protection = Column(Integer, default=0)
    documents = Column(Integer, default=0)
    money = Column(Integer, default=0)

class Admin(Base):
    __tablename__ = 'admins'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False)
    user = relationship("User")

# Создание таблиц в базе данных
from app.database.db import engine
Base.metadata.create_all(bind=engine)
