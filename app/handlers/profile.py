from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import User
import app.keyboards as kb
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()

# Profile handlers
@router.callback_query(F.data == 'profile')
async def profile(callback: CallbackQuery, db: Session = next(get_db())):
    user = db.query(User).filter(User.tg_id == callback.from_user.id).first()
    if user:
        profile_text = (
            f"👤 *Имя:* {user.name}\n"
            f"\n"
            # f"🎮 *Сыграно игр:* {user.games_played}\n"
            # f"👥 *Мафия игр:* {user.mafia_games}\n"
            # f"👨‍⚕️ *Доктор игр:* {user.doctor_games}\n"
            f"💎 *Кристаллы:* {user.crystals}\n"
            f"💵 *Деньги:* {user.money}\n"
            f"\n"
            f"🛡️ *Защита:* {user.protection}\n"
            f"📁 *Документы:* {user.documents}\n"
        )
        await callback.message.edit_text(profile_text, reply_markup=kb.profile_buttons, parse_mode='Markdown')
    else:
        await callback.answer("Пользователь не найден.")

@router.callback_query(F.data == 'shop')
async def shop(callback: CallbackQuery):
    await callback.answer("Добро пожаловать в магазин! Выберите, что хотите купить.", show_alert=True)

@router.callback_query(F.data == 'buy_money')
async def buy_money(callback: CallbackQuery, db: Session = next(get_db())):
    user = db.query(User).filter(User.tg_id == callback.from_user.id).first()
    if user:
        user.protection += 1  # Пример, увеличиваем количество защиты на 1
        db.commit()
        await callback.answer("Вы купили деньги!", show_alert=True)
    else:
        await callback.answer("Пользователь не найден.", show_alert=True)

@router.callback_query(F.data == 'buy_crystals')
async def buy_crystals(callback: CallbackQuery, db: Session = next(get_db())):
    user = db.query(User).filter(User.tg_id == callback.from_user.id).first()
    if user:
        user.crystals += 10  # Пример, увеличиваем количество кристаллов на 10
        db.commit()
        await callback.answer("Вы купили кристаллы!", show_alert=True)
    else:
        await callback.answer("Пользователь не найден.", show_alert=True)
