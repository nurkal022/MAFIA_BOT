from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from aiogram.enums import ChatType
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import User
import app.keyboards as kb

start_router = Router()

async def is_private(message: types.Message):
    return message.chat.type == ChatType.PRIVATE

@start_router.message(CommandStart(), is_private)
async def cmd_start(message: types.Message, db: Session = next(get_db())):
    user = db.query(User).filter(User.tg_id == message.from_user.id).first()
    if not user:
        user = User(tg_id=message.from_user.id, name=message.from_user.full_name, phone_number=message.contact.phone_number if message.contact else None)
        db.add(user)
        db.commit()
    await message.answer('Привет! Я бот-ведущий для игры в Мафию.', reply_markup=kb.main_menu)
