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


@router.message(Command("create_game"), F.chat.type.in_(['group', 'supergroup']))
async def start_collecting_players(message: Message):
    global game_status, day_count
    if game_status != "stopped":
        await message.answer("Игра уже идет или в процессе сбора игроков. Вы можете отменить текущую игру командой /cancel.")
        return

    game_status = "collecting"
    players.clear()
    day_count = 1  # Сброс счетчика дней при создании новой игры
    await message.answer("Игра 'Мафия' начинается! Нажмите кнопку 'Присоединиться', чтобы участвовать в игре.", reply_markup=kb.join_game_menu)

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
    global game_status
    if not players:
        await message.answer("Недостаточно игроков для начала игры.")
        return
    bot_info = await message.bot.get_me()
    bot_username = bot_info.username
    game_status = "running"
    await message.answer("Игра 'Мафия' начинается!",reply_markup=kb.create_starte_game_keyboard(bot_username))
    logging.info("Игра началась: распределение ролей.")
    await distribute_roles(message.chat.id, message.bot)


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

    player_list = '\n'.join([player['name'] for player in players])
    current_text = callback.message.text or ""
    new_text = f"Игроки, присоединившиеся к игре:\n{player_list}"
    if current_text != new_text:
        await callback.message.edit_text(new_text, reply_markup=kb.join_game_menu)
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
        4: ['role_civilian', 'role_civilian', 'role_doctor', 'role_mafia'],    ####role_don
        3: ['role_civilian',  'role_doctor', 'role_mafia'],    
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
        20: ['role_civilian', 'role_civilian', 'role_civilian', 'role_civilian', 'role_civilian', 'role_sergeant', 'role_lover', 'role_commissar', 'role_sergeant', 'role_doctor', 'role_kamikaze', 'role_mafia', 'role_mafia', 'role_mafia', 'role_don', 'role_maniac', 'role_hobo']
    }
    return roles.get(num_players, ['role_civilian'] * num_players)

async def distribute_roles(chat_id, bot: Bot):
    num_players = len(players)
    roles = get_roles(num_players)
    random.shuffle(roles)
    for player, role in zip(players, roles):
        player['role'] = role
        await bot.send_message(player['id'], f"Ваша роль: {role_descriptions[role]}")

    await bot.send_message(chat_id, "Роли распределены! Начинаем ночную фазу.")
    logging.info("Роли распределены.")
    await night_phase(chat_id, bot)

async def night_phase(chat_id, bot):
    await bot.send_animation(chat_id, "CgACAgIAAxkBAAIC72aowkm0WBCMMiOvX7s-3SduoKH0AALeRgACPEsYSdPGShSs6JwHNQQ")
    logging.info("Началась ночь {day_count}.")
    #         "🔍 Началось голосование. Выберите подозреваемого."
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    await bot.send_message(chat_id,f"Ночь {day_count}\nНа улицы города выходят лишь самые отважные и бесстрашные. Утром попробуем сосчитать их головы...", reply_markup=kb.create_starte_game_keyboard(bot_username))
    
    # Логика для мафии
    mafia_members = [player for player in players if player.get('role') == 'role_mafia']
    for member in mafia_members:
        victim_keyboard = kb.create_victim_keyboard(players)
        await bot.send_message(member['id'], "🔪 Выберите жертву.", reply_markup=victim_keyboard)
    
    # Логика для Комиссара
    commissar = next((player for player in players if player.get('role') == 'role_commissar'), None)
    if commissar:
        check_keyboard = kb.create_victim_keyboard(players)
        await bot.send_message(commissar['id'], "🔍 Выберите игрока для проверки.", reply_markup=check_keyboard)
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        await bot.send_message(chat_id, f"{commissar['name']}, перейдите в личный чат с ботом для выбора проверки: t.me/{bot_username}")

    # Логика для Доктора
    doctor = next((player for player in players if player.get('role') == 'role_doctor'), None)
    if doctor:
        heal_keyboard = kb.create_victim_keyboard(players)
        await bot.send_message(doctor['id'], "🩺 Выберите игрока для лечения.", reply_markup=heal_keyboard)
        bot_info = await bot.get_me()
        bot_username = bot_info.username
    
        # await bot.send_message(chat_id, f"{doctor['name']}, перейдите в личный чат с ботом для выбора лечения: t.me/{bot_username}")
    
    
    
    await bot.send_message(chat_id, "🕵️‍ Комиссар Каттани уже зарядил свой пистолет...")
    await asyncio.sleep(10)
    await bot.send_message(chat_id, "👨🏼‍⚕️ Доктор вышел на ночное дежурство...")
    await asyncio.sleep(10)
    await bot.send_message(chat_id, "🔪 Маньяк спрятался глубоко в кустах...")
    await asyncio.sleep(10)



    await process_night_results(chat_id, bot)
    await day_phase(chat_id, bot)

async def process_night_results(chat_id, bot):
    print(players)
    print("*************")
    # Список жертв, которые выбрала мафия
    mafia_target = [player['target'] for player in players if 'target' in player]

    # Логика для Доктора
    doctor_target = next((player['heal'] for player in players if player.get('heal')), None)

    # Логика для Комиссара
    commissar_check = next((player['check'] for player in players if player.get('check')), None)
    if commissar_check:
        check_result = "❌ Мафия" if next((player for player in players if player['id'] == commissar_check and player.get('role') in ['role_mafia', 'role_don']), None) else "✅ Не мафия"
        commissar = next(player for player in players if player.get('role') == 'role_commissar')
        await bot.send_message(commissar['id'], f"Результат проверки: {check_result}")

    # Проверка
    if doctor_target in mafia_target:
        await bot.send_message(chat_id, "💉 Доктор вылечил игрока, которого выбрала мафия.")
        logging.info("Доктор вылечил игрока.")
    else:
        victim = next((player for player in players if player['id'] in mafia_target), None)
        if victim:
            await bot.send_message(chat_id, f"💀 Игрок {victim['name']} был убит мафией.")
            logging.info(f"Игрок {victim['name']} был убит мафией.")
            players.remove(victim)

    # Очистка временных данных
    for player in players:
        player.pop('target', None)
        player.pop('heal', None)
        player.pop('check', None)

async def day_phase(chat_id, bot):
    global votes_count, votes_event, day_count
    votes_count = 0
    votes_event = asyncio.Event()

    
    await bot.send_animation(chat_id, "CgACAgIAAxkBAAIC8WaowkuPlOmPE5LP2V6E8zaae-8uAAJ0UQACOschSaNjpf2o3gABIzUE")

    #         "🔍 Началось голосование. Выберите подозреваемого."
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    await bot.send_message(chat_id, f"День {day_count}\nСолнце всходит, подсушивая на тротуарах пролитую ночью кровь...", reply_markup=kb.create_starte_game_keyboard(bot_username))
    logging.info(f"Начался День {day_count}.")
    
    # Логика для обсуждения и голосования
    vote_keyboard = kb.create_vote_keyboard(players)
    for player in players:
        await bot.send_message(player['id'], "🔍 Голосование: выберите подозреваемого.", reply_markup=vote_keyboard)
    
    await asyncio.wait([asyncio.create_task(asyncio.sleep(20)), asyncio.create_task(votes_event.wait())])  # Ожидание истечения времени или завершения голосования

    if votes_count < len(players):
        await bot.send_message(chat_id, "⏰ Время для голосования истекло. Подведение итогов.")
    await tally_votes(chat_id, bot)
    
    day_count += 1  # Увеличение счетчика дней после окончания дня

async def tally_votes(chat_id, bot):
    # Подсчет голосов
    vote_counts = {player['id']: 0 for player in players}
    
    for player in players:
        if 'vote' in player:
            vote_counts[player['vote']] += 1

    # Определение игрока с максимальным количеством голосов
    max_votes = max(vote_counts.values())
    voted_out = [player_id for player_id, votes in vote_counts.items() if votes == max_votes]
    
    if len(voted_out) > 1:
        await bot.send_message(chat_id, "Ничья! Голосование переходит в следующую фазу.")
        logging.info("Голосование завершилось вничью.")
        await day_phase(chat_id, bot)
    else:
        voted_out_player = next(player for player in players if player['id'] == voted_out[0])
        await bot.send_message(chat_id, f"👤 Игрок {voted_out_player['name']} изгнан из города.")
        logging.info(f"Игрок {voted_out_player['name']} изгнан из города.")
        players.remove(voted_out_player)
        await check_game_status(chat_id, bot)

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
    global game_status
    await bot.send_message(chat_id, "🏁 Игра окончена. Спасибо за участие!")
    logging.info("Игра окончена.")
    # Очистка данных для новой игры
    # Очистка данных для новой игры
    print("#######################3")

    print(players)
    print("#######################3")
    players.clear()
    game_status = "stopped"
