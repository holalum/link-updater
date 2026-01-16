import asyncio
from aiogram import Router, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions
from states import LinkProcess
from playwright.async_api import async_playwright

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Отправить ссылку", callback_data="send_link")]
    ])
    await message.answer("Нажми кнопку, чтобы отправить ссылку для подтверждения.", reply_markup=kb)


@router.callback_query(F.data == "send_link")
async def ask_link(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Отправьте ссылку:")
    await state.set_state(LinkProcess.waiting_for_link)
    await callback.answer()


@router.message(LinkProcess.waiting_for_link)
async def handle_link(message: types.Message, state: FSMContext):
    url = message.text
    if not url.startswith("http"):
        await message.answer("Это не ссылка!")
        return

    status_msg = await message.answer(fr"⏳ Обработка ссылки `{url}`\.\.\.", parse_mode="MarkdownV2")
    await state.clear()

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(url, wait_until="load", timeout=60000)

            await page.wait_for_load_state("networkidle")

            await asyncio.sleep(5)

            title = await page.title()

            await status_msg.edit_text(
                fr"✅ Страница `{title}` обработана!",
                parse_mode="MarkdownV2",
                link_preview_options=LinkPreviewOptions(is_disabled=True)
            )
            await browser.close()

    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {str(e)}", parse_mode=None)