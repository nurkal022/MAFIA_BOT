from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import User
import app.keyboards as kb

router = Router()

role_descriptions = {
    'role_civilian': 'Мирный житель: Обычный житель города, не обладающий особыми способностями.',
    'role_don': 'Дон: Глава мафии, имеет возможность проверять игроков на принадлежность к мафии.',
    'role_mafia': 'Мафия: Член мафии, цель - уничтожить всех мирных жителей.',
    'role_commissar': 'Комиссар Каттани: Может проверять игроков на принадлежность к мафии.',
    'role_sergeant': 'Сержант: Помогает комиссару в его расследованиях.',
    'role_doctor': 'Доктор: Может лечить игроков и спасать их от убийства.',
    'role_maniac': 'Маньяк: Убивает игроков, но не принадлежит ни к одной из сторон.',
    'role_lover': 'Любовница: Способна ночевать у игроков, предотвращая их убийство.',
    'role_lawyer': 'Адвокат: Защищает мафию в суде.',
    'role_suicide': 'Самоубийца: Может покончить с собой, убивая одного из игроков.',
    'role_hobo': 'Бомж: Не имеет дома и может ночевать у случайных игроков.',
    'role_lucky': 'Счастливчик: Обладает невероятной удачей, что помогает ему выживать.',
    'role_kamikaze': 'Камикадзе: Может взорваться, убивая себя и окружающих.'
}

# Check_Chat_Type
async def is_group(message: Message):
    return message.chat.type in ['group', 'supergroup']

async def is_private(message: Message):
    return message.chat.type == 'private'


@router.callback_query(F.data == 'roles')
async def roles(callback: CallbackQuery):
    await callback.message.edit_text('Выберите роль:', reply_markup=kb.roles_menu)


@router.callback_query(F.data.startswith('role_'))
async def show_role_description(callback: CallbackQuery):
    role = callback.data
    description = role_descriptions.get(role, 'Описание не найдено.')
    await callback.answer(description, show_alert=True)

@router.callback_query(F.data == 'back_to_main')
async def back_to_main(callback: CallbackQuery):
    await callback.message.edit_text('Привет! Я бот-ведущий для игры в Мафию.', reply_markup=kb.main_menu)
    
    
    

@router.callback_query(F.data == 'add_game')
async def add_game(callback: CallbackQuery, bot: Bot):
    bot_username = (await bot.get_me()).username
    link = f'https://t.me/{bot_username}?startgroup=true'
    await callback.answer('Добавить игру в свой чат')
    await callback.message.answer(f'Перейдите по ссылке чтобы добавить игру в чат: [Добавить игру]({link})', parse_mode='Markdown')

@router.callback_query(F.data == 'enter_chat')
async def enter_chat(callback: CallbackQuery):
    await callback.answer('Войти в чат')

@router.callback_query(F.data == 'language')
async def language(callback: CallbackQuery):
    await callback.answer('Сейчас доступен только русский язык!')

@router.callback_query(F.data == 'help')
async def help(callback: CallbackQuery):
    await callback.answer('Помощь')  
    

