from aiogram import Router, F, Bot
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.filters.state import StatesGroup, State

import logging
import os
# from datetime import datetime
from datetime import datetime
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from aiogram.filters import Command
from asgiref.sync import sync_to_async
from environs import Env

# from conf.settings import BASE_DIR
# from shopbot.models import Client, Advertisement, Staff, Bouquet, Order
from registration.management.commands.bot.user_keyboards import get_catalog_keyboard
from registration.management.commands.bot.user_menu import *
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from registration.models import *

from registration.management.commands.bot.user_keyboards import (
    get_catalog_keyboard,
    get_occasions_keyboard,
    get_price_ranges_keyboard,
    get_order_keybord
)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d - %(levelname)-8s - %(asctime)s - %(funcName)s - %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)

env: Env = Env()
env.read_env()

bot: Bot = Bot(token=env('TG_BOT_API'), parse_mode='HTML')

router = Router()


class OrderState(StatesGroup):
    user_occasion = State()
    user_name = State()
    user_adress = State()
    user_date_time_order = State()
    user_phonenumber_order = State()
    user_phonenumber_consultation = State()



@router.message(Command(commands=["start"]))
async def start_command_handler(message: Message):
    """
        Обработчик кнопки старт, если пользователя нет в БД - добавляю
    """
    user_id = await sync_to_async(DevmanUser.objects.filter(telegram_id=int(message.from_user.id)).first)()
    if not user_id:
        user_id = DevmanUser(telegram_id=int(message.from_user.id), first_name=message.from_user.first_name, created_at=datetime.datetime.now())
        await sync_to_async(user_id.save)()
        await bot.send_message(message.from_user.id, f'Привет {message.from_user.first_name}\nВас приветствует учебный бот DEVMAN', reply_markup=main_menu)
    else:
        await bot.send_message(message.from_user.id, f'Привет {message.from_user.first_name}\nРад снова видеть тебя!!!', reply_markup=main_menu)


@router.callback_query(F.data.startswith('occasion_'))
async def get_occasion_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f'start occasion handler - {callback.data}')
    occasion = callback.data.split('_')[-1]
    if occasion == '10':
        await callback.message.answer('В ответном сообщении напишите свой повод для заказа букета',
                                      reply_markup=ReplyKeyboardRemove()
                                      )
        await state.set_state(OrderState.user_occasion)
    else:
        await state.update_data(occasion=occasion, user_occasion=None)
        await callback.message.answer('На какую сумму рассчитываете?',
                                      reply_markup=await get_price_ranges_keyboard())


@router.message(OrderState.user_occasion)
async def get_user_occasion_handler(message: Message, state: FSMContext):
    await state.update_data(occasion='10', user_occasion=message.text)
    await state.clear()
    await message.answer('На какую сумму рассчитываете?',
                         reply_markup=await get_price_ranges_keyboard())

@router.callback_query(F.data.startswith == 'price_')
async def get_price_range_handler(callback: CallbackQuery):
    await callback.message.answer('На какую сумму рассчитываете?',
                                  reply_markup=await get_price_ranges_keyboard())



@router.callback_query(F.data.startswith('price_'))
async def send_bouquet_handler(callback: CallbackQuery, state: FSMContext):
    logger.info(f'start send_bouquet_handler')
    bouquet = await sync_to_async(Bouquet.objects.all().first)()
    image_path = os.path.join(BASE_DIR, bouquet.image.url.lstrip('/'))
    logger.info(f'picture path {image_path}')
    photo = FSInputFile(image_path)
    await bot.send_photo(
        chat_id=callback.from_user.id,
        caption=f'{bouquet.name.upper()}\n\n'
        f'<b>💡 Смысл букета</b>:\n\n{bouquet.meaning}\n\n'
        f'<b>💰 {bouquet.price} руб.</b>',
        photo=photo,
        reply_markup=await get_catalog_keyboard(bouquet.pk)
    )


@router.message(Command(commands=['catalog']))
async def show_start_catalog_handler(message: Message):
    bouquet = await sync_to_async(Bouquet.objects.all().first)()
    image_path = os.path.join(BASE_DIR, bouquet.image.url.lstrip('/'))
    logger.info(f'picture path {image_path}')
    photo = FSInputFile(image_path)
    await bot.send_photo(
        chat_id=message.from_user.id,
        caption=f'{bouquet.name.upper()}\n\n'
                f'<b>💡 Смысл букета</b>:\n\n{bouquet.meaning}\n\n'
                f'<b>💰 {bouquet.price} руб.</b>',
        photo=photo,
        reply_markup=await get_catalog_keyboard(bouquet.id)
    )


@router.callback_query(F.data.startswith('catalog_'))
async def show_more_catalog_handler(callback: CallbackQuery):
    bouquet_id = callback.data.split('_')[-1]
    logger.info(f'bouquet_id {bouquet_id}')
    bouquet = await sync_to_async(Bouquet.objects.filter(pk=bouquet_id).first)()
    image_path = os.path.join(BASE_DIR, bouquet.image.url.lstrip('/'))
    logger.info(f'picture path {image_path}')
    photo = FSInputFile(image_path)
    await bot.edit_message_media(chat_id=callback.from_user.id,
                                 message_id=callback.message.message_id,
                                 media=InputMediaPhoto(media=photo,
                                                       caption=f'{bouquet.name.upper()}\n\n'
                                                               f'<b>💡 Смысл букета</b>:\n\n{bouquet.meaning}\n\n'
                                                               f'<b>💰 {bouquet.price} руб.</b>'),
                                 reply_markup=await get_catalog_keyboard(bouquet.id))


@router.message(F.text == "О Devman...")
async def show_start_order(message: Message):
    await bot.send_message(message.from_user.id, str(message.from_user.id))


@router.message(F.text == "Главное меню")
async def show_main_menu(message: Message):
    await bot.send_message(message.from_user.id, 'и снова привет от бота...', reply_markup=main_menu)

@router.message(F.text == "О Devman...")
async def create_order(message: Message):
    await message.answer('https://dvmn.org/')

@router.message(F.text == "Записаться на время")
async def create_order(message: Message):
     #ODO тут необходимо предусмотреть проверку на то что пользователь уже ученик, пока этого нет
    await bot.send_message(message.from_user.id, 'и снова привет от бота...', reply_markup=main_menu)

    await message.answer('https://dvmn.org/')


@router.message(F.text.startswith('!'))
async def get_new_order_id(message: Message):
    id = message.text.split('-')[-1].replace('[','').replace(']','')
    await bot.send_message(message.from_user.id, "Укажите (при наличии) клиента для смены статуса - Отменен", reply_markup=order_main_menu)
    await sync_to_async(Order.objects.filter(pk=id).update)(status="canceled")


@router.message(F.text == "Принять 'Новый' в работу")
async def change_new_type(message: Message):
    builder = ReplyKeyboardBuilder()
    async for order in Order.objects.filter(status='new').order_by('delivery_date'):
        builder.add(types.KeyboardButton(text=f"*{order.contact_name}\nт.{order.contact_phone}-[{order.id}]", callback_data="*"))
    builder.adjust(1)
    await message.answer("Выберите клиента:",reply_markup=builder.as_markup(resize_keyboard=True))

@router.message(F.text == "Указать - Доставлен")
async def change_new_type(message: Message):
    builder = ReplyKeyboardBuilder()
    async for order in Order.objects.filter(status='processing').order_by('delivery_date'):
        builder.add(types.KeyboardButton(text=f"@{order.contact_name}\nт.{order.contact_phone}-[{order.id}]", callback_data="@"))
    builder.adjust(1)
    await message.answer("Выберите клиента которому доставлен заказ",reply_markup=builder.as_markup(resize_keyboard=True))

@router.message(F.text == "Указать - Отменен")
async def change_new_type(message: Message):
    builder = ReplyKeyboardBuilder()
    async for order in Order.objects.filter(status='processing').order_by('delivery_date'):
        builder.add(types.KeyboardButton(text=f"!{order.contact_name}\nт.{order.contact_phone}-[{order.id}]", callback_data="!"))
    builder.adjust(1)
    await message.answer("Выберите клиента у которого отменен заказ",reply_markup=builder.as_markup(resize_keyboard=True))

@router.message(F.text == "Заказы - В работе")
async def change_new_type(message: Message):
    builder = ReplyKeyboardBuilder()
    async for order in Order.objects.filter(status='processing').order_by('delivery_date'):
        builder.add(types.KeyboardButton(text=f"#{order.contact_name}\nт.{order.contact_phone}-[{order.id}]", callback_data="#"))
    builder.adjust(1)
    await message.answer("Заказы в работе\nУкажите клиента для подробной информации",reply_markup=builder.as_markup(resize_keyboard=True))

@router.message(F.text.startswith('#'))
async def get_new_order_id(message: Message):
    id = message.text.split('-')[-1].replace('[','').replace(']','')
    await bot.send_message(message.from_user.id, f"Укажите клиента (при наличии) для детализации заказа", reply_markup=order_main_menu)
    order_detail = await sync_to_async(Order.objects.filter(pk=id).first)()
    await message.answer(f"Заказ клиента №"
                         f"{order_detail.id} Статус [{order_detail.status}]\n"
                         f"Создан {order_detail.created_at}. Дата доставки {order_detail.delivery_date}\n"
                         f"{order_detail.delivery_address} {order_detail.contact_phone} {order_detail.contact_name}")


@router.callback_query(F.data.startswith('show_composition_'))
async def show_composition_handler(callback: CallbackQuery):
    bouquet_id = callback.data.split('_')[-1]
    bouquet = await sync_to_async(Bouquet.objects.filter(pk=bouquet_id)
                                  .first)()
    composition_flowers = await sync_to_async(FlowerComposition.objects.select_related('flower')
                                              .filter)(bouquet=bouquet)
    flowers = []
    async for composition_flower in composition_flowers:
        flowers.append(f'{composition_flower.flower.name} - {composition_flower.quantity} шт.\n')
    flowers = ''.join(flowers)
    composition_greeneries = await sync_to_async(GreeneryComposition.objects.select_related('greenery')
                                                 .filter)(bouquet=bouquet)
    greeneries = []
    async for composition_greenery in composition_greeneries:
        greeneries.append(f'{composition_greenery.greenery.name} - {composition_greenery.quantity} шт./упак.\n')
    greeneries = ''.join(greeneries)
    image_path = os.path.join(BASE_DIR, bouquet.image.url.lstrip('/'))
    logger.info(f'picture path {image_path}')
    photo = FSInputFile(image_path)
    await bot.edit_message_media(chat_id=callback.from_user.id,
                                 message_id=callback.message.message_id,
                                 media=InputMediaPhoto(media=photo,
                                                       caption=f'{bouquet.name.upper()}\n\n'
                                                               f'<b>🌹 Состав букета</b>:\n\n'
                                                               f'{flowers}\n{greeneries}\n'
                                                               f'Упаковка - {bouquet.wrapping}\n\n'
                                                               f'<b>💰 {bouquet.price} руб.</b>'),
                                 reply_markup=await get_catalog_keyboard(bouquet.id)
                                 )


@router.callback_query(F.data == 'start_order')
async def show_order_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Order.user_name)
    await callback.message.answer('👤 Укажите Ваше имя',
                                  reply_markup=ReplyKeyboardRemove()
                                  )


@router.message(OrderState.user_name)
async def show_adress_handler(message: Message, state: FSMContext):
    await state.set_state(OrderState.user_adress)
    await message.answer('🏠 Укажите Ваш адрес',
                         reply_markup=ReplyKeyboardRemove()
                         )


@router.message(OrderState.user_adress)
async def show_datetime_handler(message: Message, state: FSMContext):
    await state.set_state(Order.user_date_time_order)
    await message.answer('⏰ Укажите дату и время доставки',
                         reply_markup=ReplyKeyboardRemove()
                         )


@router.message(OrderState.user_date_time_order)
async def show_phonenumber_handler(message: Message, state: FSMContext):
    await state.set_state(Order.user_phonenumber_order)
    await message.answer('📲 Укажите Ваш номер телефона',
                         reply_markup=ReplyKeyboardRemove()
                         )


@router.message(OrderState.user_phonenumber_order)
async def show_phonenumber_handler(message: Message):
    await message.answer(
        text='Спасибо, за заказ 👍 Наш курьер свяжется с Вами в ближайшее время!\n\n'
             '<b>Хотите что-то еще более уникальное? '
             'Подберите другой букет из нашей коллекции или закажите консультацию флориста</b>',
        reply_markup=await get_order_keybord(),
        parse_mode='HTML'
    )


@router.callback_query(F.data == 'all_bouquets')
async def show_all_bouquets_handler(callback: CallbackQuery):
    bouquet = await sync_to_async(Bouquet.objects.all().first)()
    image_path = os.path.join(BASE_DIR, bouquet.image.url.lstrip('/'))
    logger.info(f'picture path {image_path}')
    photo = FSInputFile(image_path)
    await bot.send_photo(
        chat_id=callback.from_user.id,
        caption=f'{bouquet.name.upper()}\n\n'
                f'<b>💡 Смысл букета</b>:\n\n{bouquet.meaning}\n\n'
                f'<b>💰 {bouquet.price} руб.</b>',
        photo=photo,
        reply_markup=await get_catalog_keyboard(bouquet.id)
    )


@router.callback_query(F.data == 'consultation')
async def show_consultation_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Order.user_phonenumber_consultation)
    await callback.message.answer('📲 Укажите номер телефона, и наш флорист перезвонит Вами в течение 20 минут!',
                                  reply_markup=ReplyKeyboardRemove()
                                  )


@router.message(OrderState.user_phonenumber_consultation)
async def show_phonenumber_consultation_handler(message: Message):
    await message.answer(
        text='Флорист скоро свяжется с вами!\n\n'
             'А пока можете присмотреть что-нибудь из готовой коллекции ☝️',
        reply_markup=await show_all_bouquets_handler(message))
