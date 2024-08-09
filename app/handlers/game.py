import logging
from aiogram import Router, F, Bot, types
from aiogram.types import Message, CallbackQuery, BotCommand
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.database.models import User
import app.keyboards as kb
from aiogram.filters import Command
import asyncio
import random
from aiogram.types import InputFile
import time
from aiogram.exceptions import TelegramBadRequest

# Добавляем переменную для отслеживания начала игры
start_time = None
# Настройка логирования
logging.basicConfig(level=logging.INFO)

router = Router()
players = []
game_status = "stopped" 
votes_count = 0
votes_event = asyncio.Event()
day_count = 1 

role_descriptions = {
    'role_civilian': 'Мирный житель: Обычный житель города, не обладающий особыми способностями.',
    'role_don': 'Дон: Глава мафии, имеет возможность проверять игроков на принадлежность к мафии.',
    'role_mafia': 'Мафия: Член мафии, цель - уничтожить всех мирных жителей.',
    'role_commissar': 'Комиссар Каттани: Может проверять игроков на принадлежность к мафии или убивать.',
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

def generate_player_list(players):
    roles_icons = {
        'role_civilian': '👨🏼 Мирный житель',
        'role_don': '🤵🏻 Дон',
        'role_mafia': '👹 Мафия',
        'role_commissar': '👮‍♂️ Комиссар',
        'role_sergeant': '👮‍♂️ Сержант',
        'role_doctor': '👨🏼‍⚕️ Доктор',
        'role_maniac': '🔪 Маньяк',
        'role_lover': '❤️ Любовница',
        'role_lawyer': '👨‍⚖️ Адвокат',
        'role_suicide': '💣 Самоубийца',
        'role_hobo': '🧙🏼‍♂️ Бомж',
        'role_lucky': '🍀 Счастливчик',
        'role_kamikaze': '💥 Камикадзе'
    }

    player_links = []
    for i, player in enumerate(players, start=1):
        player_link = f'<a href="tg://user?id={player["id"]}">{i}. {player["name"]}</a>'
        player_links.append(player_link)

    roles_list = ", ".join(roles_icons[role['role']] for role in players)
    total_players = len(players)

    return f"<b>Живые игроки:</b>\n" + "\n".join(player_links) + f"\n\nКто-то из них:\n{roles_list}\nВсего: {total_players} чел.\n\nСейчас самое время обсудить результаты ночи, разобраться в причинах и следствиях..."

@router.message(Command("game"), F.chat.type.in_(['group', 'supergroup']))
async def start_collecting_players(message: Message):
    global game_status, day_count
    if game_status != "stopped":
        await message.answer("Игра уже идет или в процессе сбора игроков. Вы можете отменить текущую игру командой /cancel.")
        return

    game_status = "collecting"
    players.clear()
    day_count = 1  # Сброс счетчика дней при создании новой игры
    bot_info = await message.bot.get_me()
    join_button = kb.join_game_menu
    await message.answer("<b>Ведется набор в игру!</b>", reply_markup=join_button, parse_mode="HTML")



@router.message(Command("cancel"), F.chat.type.in_(['group', 'supergroup']))
async def cancel_game(message: Message):
    global game_status
    if game_status == "stopped":
        await message.answer("Нет активной игры для отмены.")
        return

    game_status = "stopped"
    players.clear()
    await message.answer("Игра отменена.")
    await message.delete()

@router.message(Command("start_game"), F.chat.type.in_(['group', 'supergroup']))
async def start_game(message: Message):
    global game_status, start_time
    if not players:
        await message.answer("Недостаточно игроков для начала игры.")
        return
    bot_info = await message.bot.get_me()
    bot_username = bot_info.username
    game_status = "running"
    start_time = time.time()  # Запоминаем время начала игры
    await message.answer("Игра 'Мафия' начинается!", reply_markup=kb.create_starte_game_keyboard(bot_username))
    logging.info("Игра началась: распределение ролей.")
    await distribute_roles(message.chat.id, message.bot)



@router.message(Command("share"), F.chat.type.in_(['group', 'supergroup']))
async def share_group(message: Message):
    group_invite_link = "https://t.me/joinchat/XXXXXXXXXXXXXXX"  # Замените на реальную ссылку приглашения в вашу группу
    share_keyboard = kb.create_social_share_keyboard(group_invite_link)
    await message.answer("Пригласи в этот чат друзей из других мессенджеров и социальных сетей:", reply_markup=share_keyboard)




@router.callback_query(F.data == 'join_game')
async def join_game(callback: CallbackQuery, db: Session = next(get_db())):
    user = callback.from_user
    player = db.query(User).filter(User.tg_id == user.id).first()
    if not player:
        player = User(tg_id=user.id, name=user.full_name)
        db.add(player)
        db.commit()
    if user.id not in [player['id'] for player in players]:
        players.append({'id': user.id, 'name': user.full_name})
        await callback.answer('Вы присоединились к игре!')
        try:
            await callback.message.bot.send_message(user.id, "Вы успешно зарегистрировались в игре 'Мафия'!")
        except Exception:
            await callback.message.edit_text(
                f"{user.full_name}, пожалуйста, начните чат с ботом, чтобы продолжить участие в игре: ")
    else:
        await callback.answer('Вы уже в игре!')

    # Генерация кликабельного списка игроков
    player_list = ', '.join([f'<a href="tg://user?id={player["id"]}">{player["name"]}</a>' for player in players])
    current_text = callback.message.text or ""
    new_text = f"<b>Ведётся набор в игру</b>\n\nЗарегистрировались:\n{player_list}\n\nИтого <b>{len(players)}</b>."
    if current_text != new_text:
        await callback.message.edit_text(new_text, reply_markup=kb.join_game_menu, parse_mode='HTML')
    logging.info(f"Игрок {user.full_name} присоединился к игре.")



@router.callback_query(F.data.startswith('victim_'))
async def handle_victim_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    target_id = int(callback.data.split('_')[1])
    
    for player in players:
        if player['id'] == user_id and player.get('role') == 'role_mafia':
            player['target'] = target_id
            break
    
    target_name = next(player['name'] for player in players if player['id'] == target_id)
    await callback.message.edit_text(f"🔪 Вы выбрали жертву: {target_name}.")
    await callback.answer("Цель выбрана.")
    logging.info(f"Мафия выбрала жертву: {target_name}.")
    await callback.message.bot.send_message(callback.message.chat.id, f"{callback.from_user.full_name} проголосовал за {target_name}.")

@router.callback_query(F.data.startswith('heal_'))
async def handle_heal_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    heal_id = int(callback.data.split('_')[1])
    
    for player in players:
        if player['id'] == user_id and player.get('role') == 'role_doctor':
            player['heal'] = heal_id
            break
    
    heal_name = next(player['name'] for player in players if player['id'] == heal_id)
    await callback.message.edit_text(f"🩺 Вы выбрали для лечения: {heal_name}.")
    await callback.answer("Игрок выбран для лечения.")
    logging.info(f"Доктор выбрал для лечения: {heal_name}.")
    await callback.message.bot.send_message(callback.message.chat.id, f"{callback.from_user.full_name} выбрал для лечения {heal_name}.")



@router.callback_query(F.data.startswith('check_'))
async def handle_check_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    check_id = int(callback.data.split('_')[1])
    
    for player in players:
        if player['id'] == user_id and player.get('role') == 'role_commissar':
            player['check'] = check_id
            break
    
    check_name = next(player['name'] for player in players if player['id'] == check_id)
    await callback.message.edit_text(f"🔍 Вы выбрали для проверки: {check_name}.")
    await callback.answer("Игрок выбран для проверки.")
    logging.info(f"Комиссар выбрал для проверки: {check_name}.")
    await callback.message.bot.send_message(callback.message.chat.id, f"{callback.from_user.full_name} выбрал для проверки {check_name}.")

@router.callback_query(F.data.startswith('kill_'))
async def handle_kill_selection(callback: CallbackQuery):
    user_id = callback.from_user.id
    kill_id = int(callback.data.split('_')[1])
    
    for player in players:
        if player['id'] == user_id and player.get('role') == 'role_commissar':
            player['kill'] = kill_id
            break
    
    kill_name = next(player['name'] for player in players if player['id'] == kill_id)
    await callback.message.edit_text(f"🔫 Вы выбрали для убийства: {kill_name}.")
    await callback.answer("Игрок выбран для убийства.")
    logging.info(f"Комиссар выбрал для убийства: {kill_name}.")
    # await callback.message.bot.send_message(callback.message.chat.id, f"{callback.from_user.full_name} выбрал для убийства {kill_name}.")
    
@router.callback_query(F.data.startswith('commissar_action_'))
async def handle_commissar_action(callback: CallbackQuery):
    action = callback.data.split('_')[2]
    user_id = callback.from_user.id

    if action == 'check':
        await callback.message.edit_text("🔍 Выберите игрока для проверки.", reply_markup=kb.create_victim_keyboard(players, 'check'))
    elif action == 'kill':
        await callback.message.edit_text("🔫 Выберите игрока для убийства.", reply_markup=kb.create_victim_keyboard(players, 'kill'))

    await callback.answer()



@router.callback_query(F.data.startswith('vote_'))
async def handle_vote(callback: CallbackQuery):
    global votes_count
    voter_id = callback.from_user.id
    votee_id = int(callback.data.split('_')[1])
    
    for player in players:
        if player['id'] == voter_id:
            player['vote'] = votee_id
            break
    
    votes_count += 1
    votee_name = next(player['name'] for player in players if player['id'] == votee_id)
    await callback.message.edit_text(f"🔍 Вы проголосовали за {votee_name}.")
    await callback.answer(f"Вы проголосовали за {votee_name}.")
    logging.info(f"Игрок {callback.from_user.full_name} проголосовал за {votee_name}.")

    if votes_count == len(players):
        votes_event.set()

def get_roles(num_players):
    roles = {
        2: ['role_don' , 'role_mafia'],    ####role_don
        3: ['role_civilian',  'role_doctor', 'role_don'],    
        4: ['role_civilian', 'role_civilian', 'role_doctor', 'role_mafia'],    ####role_don
        5: ['role_civilian', 'role_civilian', 'role_civilian', 'role_doctor', 'role_don'],
        6: ['role_civilian', 'role_civilian', 'role_mafia', 'role_don', 'role_doctor', 'role_commissar'],
        7: ['role_civilian', 'role_civilian', 'role_sergeant', 'role_doctor', 'role_commissar', 'role_mafia', 'role_don'],
        8: ['role_civilian', 'role_civilian', 'role_sergeant', 'role_doctor', 'role_lover', 'role_commissar', 'role_mafia', 'role_don'],
        9: ['role_civilian', 'role_civilian', 'role_mafia', 'role_mafia', 'role_don', 'role_sergeant', 'role_lover', 'role_doctor', 'role_commissar'],
        10: ['role_civilian', 'role_sergeant', 'role_kamikaze', 'role_doctor', 'role_hobo', 'role_mafia', 'role_mafia', 'role_don', 'role_commissar', 'role_lover'],
        11: ['role_civilian', 'role_civilian', 'role_hobo', 'role_sergeant', 'role_commissar', 'role_doctor', 'role_lover', 'role_mafia', 'role_mafia', 'role_don', 'role_kamikaze'],
        12: ['role_civilian', 'role_hobo', 'role_commissar', 'role_sergeant', 'role_lover', 'role_doctor', 'role_sergeant', 'role_kamikaze', 'role_mafia', 'role_mafia', 'role_mafia', 'role_don'],
        13: ['role_civilian', 'role_civilian', 'role_commissar', 'role_sergeant', 'role_sergeant', 'role_hobo', 'role_kamikaze', 'role_doctor', 'role_mafia', 'role_mafia', 'role_mafia', 'role_don', 'role_lover'],
        14: ['role_civilian', 'role_civilian', 'role_sergeant', 'role_doctor', 'role_lover', 'role_mafia', 'role_mafia', 'role_mafia', 'role_don', 'role_hobo', 'role_maniac', 'role_kamikaze', 'role_sergeant', 'role_commissar'],
        15: ['role_civilian', 'role_civilian', 'role_doctor', 'role_sergeant', 'role_hobo', 'role_commissar', 'role_sergeant', 'role_lover', 'role_kamikaze', 'role_mafia', 'role_mafia', 'role_mafia', 'role_don', 'role_maniac'],
        16: ['role_civilian', 'role_civilian', 'role_civilian', 'role_commissar', 'role_sergeant', 'role_sergeant', 'role_kamikaze', 'role_doctor', 'role_hobo', 'role_maniac', 'role_mafia', 'role_mafia', 'role_mafia', 'role_don', 'role_lover'],
        17: ['role_civilian', 'role_civilian', 'role_civilian', 'role_civilian', 'role_kamikaze', 'role_lover', 'role_sergeant', 'role_hobo', 'role_commissar', 'role_sergeant', 'role_mafia', 'role_mafia', 'role_mafia', 'role_don', 'role_maniac', 'role_doctor'],
        18: ['role_civilian', 'role_civilian', 'role_civilian', 'role_civilian', 'role_kamikaze', 'role_sergeant', 'role_commissar', 'role_sergeant', 'role_lover', 'role_mafia', 'role_mafia', 'role_mafia', 'role_don', 'role_maniac', 'role_doctor', 'role_hobo'],
        19: ['role_civilian', 'role_civilian', 'role_civilian', 'role_civilian', 'role_civilian', 'role_hobo', 'role_commissar', 'role_sergeant', 'role_doctor', 'role_sergeant', 'role_kamikaze', 'role_lover', 'role_maniac', 'role_mafia', 'role_mafia', 'role_mafia', 'role_don', 'role_maniac'],
        20: ['role_civilian', 'role_civilian', 'role_civilian', 'role_civilian', 'role_civilian', 'role_sergeant', 'role_lover', 'role_commissar', 'role_sergeant', 'role_doctor', 'role_kamikaze', 'role_mafia', 'role_mafia', 'role_mafia', 'role_don', 'role_maniак', 'role_hobo']
    }
    return roles.get(num_players, ['role_civilian'] * num_players)

async def distribute_roles(chat_id, bot: Bot):
    global players
    num_players = len(players)
    roles = get_roles(num_players)
    random.shuffle(roles)
    mafia_members = []
    don = None
    for player, role in zip(players, roles):
        player['role'] = role
        if role in ['role_mafia', 'role_don']:
            mafia_members.append(player)
            if role == 'role_don':
                don = player
        await bot.send_message(player['id'], f"Ваша роль: {role_descriptions[role]}")
    
    # Отправка списка союзников мафии с кликабельными ссылками
    for mafia in mafia_members:
        allies = [f"<a href='tg://user?id={p['id']}'>{p['name']}</a> - {'Дон' if p['role'] == 'role_don' else 'Мафия'}" for p in mafia_members if p['id'] != mafia['id']]
        allies_message = "Ваши союзники:\n" + "\n".join(allies)
        await bot.send_message(mafia['id'], allies_message, parse_mode='HTML')
    
    logging.info("Роли распределены.")
    await night_phase(chat_id, bot)
    
    
    
async def handle_mafia_vote(bot: Bot, player: dict, keyboard, chat_id: int):
    msg = await bot.send_message(player['id'], "🔪 У вас есть 30 секунд, чтобы выбрать жертву.", reply_markup=keyboard)
    
    try:
        future = asyncio.get_running_loop().create_future()

        async def process_callback(callback: CallbackQuery):
            if callback.from_user.id == player['id'] and callback.data.startswith('victim_'):
                await callback.answer()
                future.set_result(callback.data)

        router.callback_query.register(process_callback)
        choice = await asyncio.wait_for(future, timeout=30)
        router.callback_query.handlers.pop()

        player['target'] = int(choice.split('_')[1])
        await bot.send_message(player['id'], f"Вы выбрали жертву.")
        
    except asyncio.TimeoutError:
        await bot.edit_message_text("Время истекло. Вы пропустили свой ход.", chat_id=player['id'], message_id=msg.message_id)
        if process_callback in router.callback_query.handlers:
            router.callback_query.handlers.pop()
    except Exception as e:
        logging.error(f"Ошибка при обработке голосования мафии для игрока {player['name']}: {e}")
        if process_callback in router.callback_query.handlers:
            router.callback_query.handlers.pop()






from aiogram import Bot, Router
from aiogram.types import CallbackQuery
import asyncio

async def handle_role_action(bot: Bot, player: dict, action_type: str, keyboard, chat_id: int, action_message: str):
    msg = await bot.send_message(player['id'], f"У вас есть 30 секунд, чтобы сделать выбор.", reply_markup=keyboard)
    
    try:
        # Создаем future для ожидания callback
        future = asyncio.get_running_loop().create_future()

        # Функция для обработки callback query
        async def process_callback(callback: CallbackQuery):
            if callback.from_user.id == player['id'] and callback.data.startswith(action_type):
                await callback.answer()
                future.set_result(callback.data)

        # Регистрируем временный обработчик
        router.callback_query.register(process_callback)

        # Ожидаем результат с таймаутом
        choice = await asyncio.wait_for(future, timeout=30)

        # Удаляем временный обработчик
        router.callback_query.handlers.pop()

        await bot.send_message(chat_id, action_message)
        
        # Обновляем данные игрока на основе выбора
        player[action_type] = choice.split('_')[1]
        
    except asyncio.TimeoutError:
        await bot.edit_message_text("Время истекло. Вы пропустили свой ход.", chat_id=player['id'], message_id=msg.message_id)
        # Удаляем временный обработчик в случае таймаута
        if process_callback in router.callback_query.handlers:
            router.callback_query.handlers.pop()
    except Exception as e:
        logging.error(f"Ошибка при обработке действия {action_type} для игрока {player['name']}: {e}")
        # Удаляем временный обработчик в случае ошибки
        if process_callback in router.callback_query.handlers:
            router.callback_query.handlers.pop()

import asyncio
from aiogram import Bot

async def night_phase(chat_id: int, bot: Bot):
    global day_count, router
    await bot.send_animation(chat_id, "CgACAgIAAxkBAAIC72aowkm0WBCMMiOvX7s-3SduoKH0AALeRgACPEsYSdPGShSs6JwHNQQ")
    logging.info(f"Началась ночь {day_count}.")
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    await bot.send_message(chat_id, f"Ночь {day_count}\nНа улицы города выходят лишь самые отважные и бесстрашные. У всех есть 30 секунд на свои ночные дела...", reply_markup=kb.create_starte_game_keyboard(bot_username))
    
    await bot.send_message(chat_id, generate_player_list(players), parse_mode='HTML', reply_markup=kb.create_starte_game_keyboard(bot_username))
    
    night_actions = []
    
    # Логика для мафии и Дона
    mafia_members = [player for player in players if player.get('role') in ['role_mafia', 'role_don']]
    # victim_keyboard = kb.create_victim_keyboard([p for p in players if p not in mafia_members], 'victim')
    # don_keyboard = kb.create_victim_keyboard([p for p in players if p not in mafia_members], 'don_victim')
    victim_keyboard = kb.create_victim_keyboard([p for p in players], 'victim')
    don_keyboard = kb.create_victim_keyboard([p for p in players], 'don_victim')
    
    for member in mafia_members:
        if member['role'] == 'role_don':
            night_actions.append(handle_don_vote(bot, member, don_keyboard, chat_id))
        else:
            night_actions.append(handle_mafia_vote(bot, member, victim_keyboard, chat_id))
    
    # Логика для Комиссара
    commissar = next((player for player in players if player.get('role') == 'role_commissar'), None)
    if commissar:
        commissar_keyboard = kb.create_commissar_action_keyboard()
        night_actions.append(handle_role_action(bot, commissar, 'commissar_action', commissar_keyboard, chat_id, "🕵️‍♂️ Комиссар Каттани закончил свои поиски..."))
    
    # Логика для Доктора
    doctor = next((player for player in players if player.get('role') == 'role_doctor'), None)
    if doctor:
        heal_keyboard = kb.create_victim_keyboard(players, 'heal')
        night_actions.append(handle_role_action(bot, doctor, 'heal', heal_keyboard, chat_id, "👨🏼‍⚕️ Доктор закончил ночное дежурство..."))
    
    # Запускаем все действия параллельно и ждем их завершения или истечения таймаута
    try:
        await asyncio.wait_for(asyncio.gather(*night_actions), timeout=30)
    except asyncio.TimeoutError:
        logging.info("Ночная фаза завершена по таймауту")

    await bot.send_message(chat_id, "🌅 Ночь подходит к концу...")
    
    # Обрабатываем результаты ночи
    await process_night_results(chat_id, bot)
    await bot.send_message(chat_id, generate_player_list(players), parse_mode='HTML')

    await day_phase(chat_id, bot)

    
    
@router.callback_query(lambda c: c.data and c.data.startswith('don_victim_'))
async def handle_don_vote(callback: CallbackQuery):
    user_id = callback.from_user.id
    target_id = int(callback.data.split('_')[2])
    
    don = next((player for player in players if player['id'] == user_id and player.get('role') == 'role_don'), None)
    if don:
        don['target'] = target_id
        target_name = next(player['name'] for player in players if player['id'] == target_id)
        await callback.message.edit_text(f"🎩 Вы, как Дон, выбрали жертву: {target_name}.")
        await callback.answer("Цель выбрана.")
        logging.info(f"Дон выбрал жертву: {target_name}.")
    else:
        await callback.answer("Вы не являетесь Доном или произошла ошибка.")

async def handle_mafia_vote(bot: Bot, player: dict, keyboard, chat_id: int):
    msg = await bot.send_message(player['id'], "🔪 У вас есть 30 секунд, чтобы выбрать жертву.", reply_markup=keyboard)
    
    try:
        future = asyncio.get_running_loop().create_future()

        async def process_callback(callback: CallbackQuery):
            if callback.from_user.id == player['id'] and callback.data.startswith('victim_'):
                await callback.answer()
                future.set_result(callback.data)

        router.callback_query.register(process_callback)
        choice = await asyncio.wait_for(future, timeout=30)
        router.callback_query.handlers.pop()

        player['target'] = int(choice.split('_')[1])
        await bot.send_message(player['id'], f"Вы выбрали жертву.")
        
    except asyncio.TimeoutError:
        await bot.edit_message_text("Время истекло. Вы пропустили свой ход.", chat_id=player['id'], message_id=msg.message_id)
        if process_callback in router.callback_query.handlers:
            router.callback_query.handlers.pop()
    except Exception as e:
        logging.error(f"Ошибка при обработке голосования мафии для игрока {player['name']}: {e}")
        if process_callback in router.callback_query.handlers:
            router.callback_query.handlers.pop()

async def handle_don_vote(bot: Bot, player: dict, keyboard, chat_id: int):
    msg = await bot.send_message(player['id'], "🎩 У вас, как у Дона, есть 30 секунд, чтобы выбрать жертву.", reply_markup=keyboard)
    
    try:
        future = asyncio.get_running_loop().create_future()

        async def process_callback(callback: CallbackQuery):
            if callback.from_user.id == player['id'] and callback.data.startswith('don_victim_'):
                await callback.answer()
                future.set_result(callback.data)

        router.callback_query.register(process_callback)
        choice = await asyncio.wait_for(future, timeout=30)
        router.callback_query.handlers.pop()

        player['target'] = int(choice.split('_')[2])
        await bot.send_message(player['id'], f"Вы, как Дон, выбрали жертву.")
        
    except asyncio.TimeoutError:
        await bot.edit_message_text("Время истекло. Вы пропустили свой ход.", chat_id=player['id'], message_id=msg.message_id)
        if process_callback in router.callback_query.handlers:
            router.callback_query.handlers.pop()
    except Exception as e:
        logging.error(f"Ошибка при обработке голосования Дона: {e}")
        if process_callback in router.callback_query.handlers:
            router.callback_query.handlers.pop()
            






from collections import Counter
import logging
from collections import Counter
import random

async def process_night_results(chat_id, bot):
    global players
    logging.info("Начало обработки результатов ночной фазы")

    # Обработка выбора мафии и Дона
    don = next((player for player in players if player.get('role') == 'role_don'), None)
    mafia_members = [player for player in players if player.get('role') == 'role_mafia']
    
    mafia_votes = [player.get('target') for player in mafia_members if player.get('target')]
    don_target = don.get('target') if don else None

    logging.info(f"Голоса мафии: {mafia_votes}")
    logging.info(f"Выбор Дона: {don_target}")

    victim = None
    if don_target:
        # Если Дон сделал выбор, его голос имеет приоритет
        victim_id = don_target
        logging.info(f"Дон ({don['name']}) выбрал жертву: {victim_id}")
    elif mafia_votes:
        # Если Дон не сделал выбор, но есть голоса обычной мафии
        vote_counts = Counter(mafia_votes)
        max_votes = max(vote_counts.values())
        potential_victims = [v for v, count in vote_counts.items() if count == max_votes]
        
        if len(potential_victims) == 1:
            victim_id = potential_victims[0]
        else:
            victim_id = random.choice(potential_victims)
        logging.info(f"Жертва выбрана голосованием мафии: {victim_id}")
    else:
        logging.info("Мафия не смогла выбрать жертву")

    if victim_id:
        victim = next((player for player in players if player['id'] == victim_id), None)

    # Логика для Доктора
    doctor = next((player for player in players if player.get('role') == 'role_doctor'), None)
    doctor_target = doctor.get('heal') if doctor else None
    logging.info(f"Цель доктора: {doctor_target}")

    # Логика для Комиссара
    commissar = next((player for player in players if player.get('role') == 'role_commissar'), None)
    commissar_check = commissar.get('check') if commissar else None
    commissar_kill = commissar.get('kill') if commissar else None
    
    if commissar_check:
        check_result = "❌ Мафия" if next((player for player in players if player['id'] == commissar_check and player.get('role') in ['role_mafia', 'role_don']), None) else "✅ Не мафия"
        checked_player = next((player for player in players if player['id'] == commissar_check), None)
        if checked_player:
            await bot.send_message(commissar['id'], f"Результат проверки: {checked_player['name']} - {check_result}")
            logging.info(f"Комиссар проверил игрока {checked_player['name']}: {check_result}")

    # Обработка результатов
    killed_players = []
    if victim and victim['id'] == doctor_target:
        await bot.send_message(chat_id, "💉 Доктор вылечил игрока, которого выбрала мафия.")
        logging.info("Доктор вылечил цель мафии")
    elif victim:
        killed_players.append(victim)
        logging.info(f"Игрок {victim['name']} убит мафией")

    if commissar_kill:
        kill_victim = next((player for player in players if player['id'] == commissar_kill), None)
        if kill_victim and kill_victim not in killed_players:
            killed_players.append(kill_victim)
            logging.info(f"Игрок {kill_victim['name']} убит комиссаром")

    # Отправка сообщений об убийствах
    for killed in killed_players:
        death_reason = 'мафией' if killed == victim else 'комиссаром'
        await bot.send_message(chat_id, f"💀 Игрок {killed['name']} был убит {death_reason}.")
        await bot.send_message(chat_id, f"Сегодня был жестоко убит {killed['name']}.\nГоворят, у него в гостях был {death_reason}.")

    # Удаление убитых игроков из списка
    players = [player for player in players if player not in killed_players]

    if not killed_players:
        await bot.send_message(chat_id, "Этой ночью никто не погиб.")
        logging.info("Ночью никто не погиб")

    # Очистка временных данных
    for player in players:
        for key in ['target', 'heal', 'check', 'kill']:
            player.pop(key, None)

    logging.info("Завершение обработки результатов ночной фазы")
    
    
    
    

async def handle_night_action(bot: Bot, chat_id: int, message_id: int, timeout: int):
    """
    Обрабатывает ночные действия игроков и голосование, автоматически изменяя сообщение по истечении времени.
    
    :param bot: Экземпляр бота Telegram
    :param chat_id: ID чата, в котором находится сообщение
    :param message_id: ID сообщения, которое нужно изменить
    :param timeout: Время ожидания в секундах
    """
    try:
        # Ждем указанное время
        await asyncio.sleep(timeout)
        
        # Пытаемся изменить сообщение
        await bot.edit_message_text(
            text="Время прошло. Вы пропустили свой ход.",
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=None  # Убираем клавиатуру
        )
    except TelegramBadRequest as e:
        # Сообщение уже было изменено (пользователь успел сделать выбор)
        # или было удалено
        print(f"Не удалось изменить сообщение: {e}")
    except asyncio.CancelledError:
        # Задача была отменена
        print("Задача handle_night_action была отменена")
    except Exception as e:
        # Обрабатываем любые другие исключения
        print(f"Произошла ошибка в handle_night_action: {e}")


async def day_phase(chat_id, bot):
    global votes_count, day_count
    votes_count = 0
    
    await bot.send_animation(chat_id, "CgACAgIAAxkBAAIC8WaowkuPlOmPE5LP2V6E8zaae-8uAAJ0UQACOschSaNjpf2o3gABIzUE")

    bot_info = await bot.get_me()
    bot_username = bot_info.username
    await bot.send_message(chat_id, f"День {day_count}\nСолнце всходит, подсушивая на тротуарах пролитую ночью кровь...", reply_markup=kb.create_starte_game_keyboard(bot_username))
    logging.info(f"Начался День {day_count}.")
    
    await bot.send_message(chat_id, generate_player_list(players), parse_mode='HTML')

    await bot.send_message(chat_id, "<b>Пришло время определить и наказать виновных.\nГолосование продлится ровно 30 секунд</b>", reply_markup=kb.create_starte_game_keyboard(bot_username), parse_mode='HTML')
    
    vote_keyboard = kb.create_vote_keyboard(players)
    voting_tasks = []
    for player in players:
        try:
            msg = await bot.send_message(player['id'], "🔍 У вас есть 30 секунд, чтобы выбрать подозреваемого.", reply_markup=vote_keyboard)
            voting_tasks.append(asyncio.create_task(handle_night_action(bot, player['id'], msg.message_id, 30)))
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение игроку {player['name']}: {e}")
            continue
    await asyncio.gather(*voting_tasks)

    await bot.send_message(chat_id, "⏰ Время для голосования истекло. Подведение итогов.")
    await tally_votes(chat_id, bot)
    
    day_count += 1
    await check_game_status(chat_id, bot)

async def tally_votes(chat_id, bot):
    # Подсчет голосов
    vote_counts = {player['id']: 0 for player in players}
    
    for player in players:
        if 'vote' in player:
            vote_counts[player['vote']] += 1

    # Определение игрока с максимальным количеством голосов
    max_votes = max(vote_counts.values())
    voted_out = [player_id for player_id, votes in vote_counts.items() if votes == max_votes]
    
    if len(voted_out) > 1 or max_votes == 0:
        # Ничья или никто не проголосовал
        await bot.send_message(chat_id, "Город не смог принять решение. Никто не будет изгнан сегодня.")
        logging.info("Голосование завершилось без результата.")
    else:
        voted_out_player = next(player for player in players if player['id'] == voted_out[0])
        await bot.send_message(chat_id, f"👤 Игрок {voted_out_player['name']} изгнан из города.")
        logging.info(f"Игрок {voted_out_player['name']} изгнан из города.")
        players.remove(voted_out_player)

    # Очистка голосов
    for player in players:
        player.pop('vote', None)

async def check_game_status(chat_id, bot):
    # Логика для проверки условий победы
    civilians = [player for player in players if player.get('role') not in ['role_mafia', 'role_don']]
    mafia = [player for player in players if player.get('role') in ['role_mafia', 'role_don']]
    
    if not mafia:
        await bot.send_message(chat_id, "🎉 Мирные жители победили!")
        logging.info("Мирные жители победили.")
        await end_game(chat_id, bot)
    elif len(mafia) >= len(civilians):
        await bot.send_message(chat_id, "😈 Мафия победила!")
        logging.info("Мафия победила.")
        await end_game(chat_id, bot)
    else:
        await night_phase(chat_id, bot)

async def end_game(chat_id, bot):
    global game_status, start_time, players
    end_time = time.time()
    duration = end_time - start_time
    duration_str = time.strftime("%M мин. %S сек.", time.gmtime(duration))

    mafia_team = [player for player in players if player.get('role') in ['role_mafia', 'role_don']]
    civilian_team = [player for player in players if player.get('role') not in ['role_mafia', 'role_don']]

    # Определение победившей команды
    if len(mafia_team) >= len(civilian_team):
        winning_team = "Мафия"
        winners = mafia_team
        losers = civilian_team
    else:
        winning_team = "Мирные жители"
        winners = civilian_team
        losers = mafia_team

    # Функция для форматирования строки игрока
    def format_player(player):
        role_icon = {
            'role_civilian': '👨🏼 Мирный житель',
            'role_don': '🤵🏻 Дон',
            'role_mafia': '🤵🏼 Мафия',
            'role_commissar': '🕵️‍ Комиссар Каттани',
            'role_doctor': '👨🏼‍⚕️ Доктор',
            'role_hobo': '🧙🏼‍♂️ Бомж',
            # Добавьте другие роли по необходимости
        }.get(player.get('role'), '❓ Неизвестная роль')
        return f"    <a href='tg://user?id={player['id']}'>{player['name']}</a> - {role_icon}"

    # Формирование списков победителей и проигравших
    winners_list = '\n'.join([format_player(player) for player in winners])
    losers_list = '\n'.join([format_player(player) for player in losers])

    message = (
        f"Игра окончена!\n"
        f"Победила {winning_team}\n\n"
        f"Победители:\n{winners_list}\n\n"
        f"Остальные участники:\n{losers_list}\n\n"
        f"Игра длилась: {duration_str}"
    )

    await bot.send_message(chat_id, message, parse_mode='HTML')
    logging.info(f"Игра окончена. Победила {winning_team}. Длительность: {duration_str}")

    # Очистка данных для новой игры
    players.clear()
    game_status = "stopped"