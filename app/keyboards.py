from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🕵 Добавить игру в свой чат", callback_data='add_game')],
    [InlineKeyboardButton(text='🎲 Войти в чат', callback_data='enter_chat')],
    [InlineKeyboardButton(text='🇷🇺 Язык / Language', callback_data='language')],
    [InlineKeyboardButton(text='👤 Профиль', callback_data='profile'), InlineKeyboardButton(text='🃏 Роли', callback_data='roles')]
])

group_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🇷🇺 Язык / Language', callback_data='language')],
    [InlineKeyboardButton(text='Помощь', callback_data='help')],
])

join_game_menu = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Присоединиться', callback_data='join_game')],
])

def create_roles_keyboard():
    roles_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Мирный житель 👨🏼', callback_data='role_civilian'),
         InlineKeyboardButton(text='Дон 🤵🏻', callback_data='role_don')],
        [InlineKeyboardButton(text='Мафия 🤵🏼', callback_data='role_mafia'),
         InlineKeyboardButton(text='Комиссар Каттани 🕵️‍♂️', callback_data='role_commissar')],
        [InlineKeyboardButton(text='Сержант 👮', callback_data='role_sergeant'),
         InlineKeyboardButton(text='Доктор 👨‍⚕️', callback_data='role_doctor')],
        [InlineKeyboardButton(text='Маньяк 🔪', callback_data='role_maniac'),
         InlineKeyboardButton(text='Любовница 💃', callback_data='role_lover')],
        [InlineKeyboardButton(text='Адвокат 👨🏼‍💼', callback_data='role_lawyer'),
         InlineKeyboardButton(text='Самоубийца 😵', callback_data='role_suicide')],
        [InlineKeyboardButton(text='Бомж 🧙🏻‍♂️', callback_data='role_hobo'),
         InlineKeyboardButton(text='Счастливчик ✌️', callback_data='role_lucky')],
        [InlineKeyboardButton(text='Камикадзе 💣', callback_data='role_kamikaze')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_main')]
    ])
    return roles_keyboard

roles_menu = create_roles_keyboard()

get_number = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Отправить номер', request_contact=True)]], resize_keyboard=True)

def create_victim_keyboard(players):
    buttons = [InlineKeyboardButton(text=player['name'], callback_data=f'victim_{player["id"]}') for player in players]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

def create_vote_keyboard(players):
    buttons = [InlineKeyboardButton(text=player['name'], callback_data=f'vote_{player["id"]}') for player in players]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

def create_starte_game_keyboard(username):
    buttons = [InlineKeyboardButton(
        text="🤵🏻 Присодинится",
        url=f"https://t.me/{username}"
    )]
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


# Создание инлайн-кнопок
profile_buttons = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🛒 Магазин', callback_data='shop')],
    [InlineKeyboardButton(text='💰 Купить деньги', callback_data='buy_money'),InlineKeyboardButton(text='💎 Купить кристаллы', callback_data='buy_crystals')],
    [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_main')]
])

