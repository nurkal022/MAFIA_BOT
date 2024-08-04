from aiogram import Router, Bot, types
from aiogram.types import Message, BotCommand
from aiogram.filters import Command
from sqlalchemy.orm import Session
from app.database.models import Admin, User
from app.database.db import get_db

router = Router()

# Постоянные администраторы
PERMANENT_ADMINS = [7086332349, 889928782]

# Функция для проверки, является ли пользователь администратором
def is_admin(user_id: int, db: Session) -> bool:
    if user_id in PERMANENT_ADMINS:
        return True
    admin = db.query(Admin).join(User).filter(User.tg_id == user_id).first()
    return admin is not None

# Команда для добавления нового администратора (доступна только текущим администраторам)
@router.message(Command("add_admin"))
async def add_admin(message: Message, db: Session = next(get_db())):
    if not is_admin(message.from_user.id, db):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    try:
        new_admin_id = int(message.text.split()[1])
        user = db.query(User).filter(User.tg_id == new_admin_id).first()
        if user:
            admin = Admin(user_id=user.id)
            db.add(admin)
            db.commit()
            await message.answer(f"Пользователь {new_admin_id} добавлен в администраторы.")
        else:
            await message.answer("Пользователь с таким ID не найден.")
    except (IndexError, ValueError):
        await message.answer("Пожалуйста, укажите действительный ID пользователя.")

# Команда для удаления администратора (доступна только текущим администраторам)
@router.message(Command("remove_admin"))
async def remove_admin(message: Message, db: Session = next(get_db())):
    if not is_admin(message.from_user.id, db):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    try:
        admin_id = int(message.text.split()[1])
        if admin_id in PERMANENT_ADMINS:
            await message.answer("Этот пользователь не может быть удален из администраторов.")
            return

        admin = db.query(Admin).join(User).filter(User.tg_id == admin_id).first()
        if admin:
            db.delete(admin)
            db.commit()
            await message.answer(f"Пользователь {admin_id} удален из администраторов.")
        else:
            await message.answer("Администратор с таким ID не найден.")
    except (IndexError, ValueError):
        await message.answer("Пожалуйста, укажите действительный ID пользователя.")

# Команда для остановки бота (доступна только администраторам)
@router.message(Command("stop_bot"))
async def stop_bot(message: Message, bot: Bot, db: Session = next(get_db())):
    if not is_admin(message.from_user.id, db):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    await message.answer("Бот остановлен.")
    await bot.session.close()
    
    
# Команда для остановки бота (доступна только администраторам)
@router.message(Command("admin"))
async def stop_bot(message: Message, bot: Bot, db: Session = next(get_db())):
    if not is_admin(message.from_user.id, db):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    await message.answer("Ты бог.")

# Команда для начисления кристаллов пользователям (доступна только администраторам)
@router.message(Command("add_crystals"))
async def add_crystals(message: Message, db: Session = next(get_db())):
    if not is_admin(message.from_user.id, db):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return

    try:
        user_id, amount = map(int, message.text.split()[1:])
        user = db.query(User).filter(User.tg_id == user_id).first()
        if user:
            user.crystals += amount
            db.commit()
            await message.answer(f"Пользователю {user_id} начислено {amount} кристаллов.")
        else:
            await message.answer("Пользователь с таким ID не найден.")
    except (IndexError, ValueError):
        await message.answer("Пожалуйста, укажите действительный ID пользователя и количество кристаллов.")
