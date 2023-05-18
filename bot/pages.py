import os
from datetime import date as _date, datetime, timedelta
from babel.dates import format_date
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from requests.exceptions import RequestException, HTTPError
from lib.api.schemas import TimeTableDate
from lib.api.exceptions import HTTPApiException
from bot import remaining_time
from bot.data import ChatData
from bot.utils import array_split
from settings import api, langs, tg_logger, API_TYPE, API_TYPE_CACHED


def access_denied(context: ContextTypes.DEFAULT_TYPE) -> dict:
    buttons = [[
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.menu'],
                             callback_data='open.menu')
    ]]

    return {
        'text': context._chat_data.get_lang()['alert.no_permissions'],
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def admin_panel(context: ContextTypes.DEFAULT_TYPE) -> dict:
    buttons = [
        [InlineKeyboardButton(text=context._chat_data.get_lang()['button.admin.clear_expired_cache'],
                              callback_data='admin.clear_expired_cache')],
        [InlineKeyboardButton(text=context._chat_data.get_lang()['button.admin.clear_all_cache'],
                              callback_data='admin.clear_all_cache')],
        [InlineKeyboardButton(text=context._chat_data.get_lang()['button.admin.get_logs'],
                              callback_data='admin.get_logs')],
        [InlineKeyboardButton(text=context._chat_data.get_lang()['button.admin.clear_logs'],
                              callback_data='admin.clear_logs')],
        [InlineKeyboardButton(text=context._chat_data.get_lang()['button.back'],
                              callback_data='open.menu')]
    ]

    return {
        'text': context._chat_data.get_lang()['page.admin_panel'],
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def api_unavaliable(context: ContextTypes) -> dict:
    buttons = [[
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.menu'],
                             callback_data='open.menu'),
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.write_me'],
                             url='https://t.me/cubicbyte')
    ]]

    return {
        'text': context._chat_data.get_lang()['page.api_unavaliable'],
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def calls(context: ContextTypes.DEFAULT_TYPE) -> dict:
    try:
        schedule_section = _get_calls_section_text()
    except HTTPApiException:
        return api_unavaliable(context)

    buttons = [[
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.back'],
                             callback_data='open.more'),
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.menu'],
                             callback_data='open.menu')
    ]]

    return {
        'text': context._chat_data.get_lang()['page.calls'].format(schedule=schedule_section),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def classes_notification(chat_data: ChatData, day: TimeTableDate, remaining: str) -> dict:
    buttons = [[
        InlineKeyboardButton(text=chat_data.get_lang()['button.open_schedule'],
                             callback_data=f'open.schedule.day#date={day.date}'),
        InlineKeyboardButton(text=chat_data.get_lang()['button.settings'],
                             callback_data='open.settings')
    ]]

    return {
        'text': chat_data.get_lang()['page.classes_notification'].format(
            remaining=remaining,
            schedule=_get_notification_schedule_section(day)),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def course_list(context: ContextTypes.DEFAULT_TYPE, structure_id: int, faculty_id: int) -> dict:
    try:
        courses = api.list_courses(faculty_id)
    except HTTPApiException:
        return api_unavaliable(context)

    buttons = [[
        InlineKeyboardButton(
            text=context._chat_data.get_lang()['button.back'],
            callback_data=f'select.schedule.structure#structureId={structure_id}')
    ]]

    for course in courses:
        buttons.append([
            InlineKeyboardButton(
                text=str(course.course),
                callback_data=f'select.schedule.course#structureId={structure_id}&facultyId={faculty_id}&course={course.course}')
        ])

    return {
        'text': context._chat_data.get_lang()['page.course'],
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def faculty_list(context: ContextTypes.DEFAULT_TYPE, structure_id: int) -> dict:
    try:
        faculties = api.list_faculties(structure_id)
        structures = api.list_structures()
    except HTTPApiException:
        return api_unavaliable(context)

    buttons = []

    if len(structures) > 1:
        buttons.append([
            InlineKeyboardButton(
                text=context._chat_data.get_lang()['button.back'],
                callback_data='open.select_group')
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                text=context._chat_data.get_lang()['button.back'],
                callback_data='open.menu')
        ])

    for faculty in faculties:
        buttons.append([
            InlineKeyboardButton(
                text=faculty.fullName,
                callback_data=f'select.schedule.faculty#structureId={structure_id}&facultyId={faculty.id}')
        ])

    return {
        'text': context._chat_data.get_lang()['page.faculty'],
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def greeting(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return {
        'text': context._chat_data.get_lang()['page.greeting'],
        'parse_mode': 'MarkdownV2'
    }


def group_list(context: ContextTypes.DEFAULT_TYPE, structure_id: int, faculty_id: int, course: int) -> dict:
    try:
        groups = api.list_groups(faculty_id, course)
    except HTTPApiException:
        return api_unavaliable(context)

    buttons = [[
        InlineKeyboardButton(
            text=context._chat_data.get_lang()['button.back'],
            callback_data=f'select.schedule.faculty#structureId={structure_id}&facultyId={faculty_id}')
    ]]

    group_btns = []
    for group in groups:
        group_btns.append(
            InlineKeyboardButton(
                text=group.name,
                callback_data=f'select.schedule.group#groupId={group.id}')
        )

    # Make many 3-wide button rows like this: [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    buttons.extend(array_split(group_btns, 3))

    return {
        'text': context._chat_data.get_lang()['page.group'],
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def info(context: ContextTypes.DEFAULT_TYPE) -> dict:
    try:
        api_ver = escape_markdown(api.version().name, version=2)
    except RequestException:
        api_ver = context._chat_data.get_lang()['text.unknown']

    message_text = context._chat_data.get_lang()['page.info'].format(
        api_ver=api_ver,
        api_ver_supported=escape_markdown(api.VERSION, version=2)
    )

    buttons = [[
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.back'],
                             callback_data='open.more'),
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.menu'],
                             callback_data='open.menu')
    ]]

    return {
        'text': message_text,
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def invalid_group(context: ContextTypes.DEFAULT_TYPE) -> dict:
    buttons = [[
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.select_group'],
                             callback_data='open.select_group'),
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.menu'],
                             callback_data='open.menu')
    ]]

    return {
        'text': context._chat_data.get_lang()['page.invalid_group'],
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def lang_selection(context: ContextTypes.DEFAULT_TYPE) -> dict:
    buttons = []

    for i in langs:
        buttons.append([
            InlineKeyboardButton(text=langs[i]['lang_name'],
                                 callback_data=f'select.lang#lang={i}')
        ])

    buttons.append([
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.back'],
                             callback_data='open.settings'),
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.menu'],
                             callback_data='open.menu')
    ])

    return {
        'text': context._chat_data.get_lang()['page.lang_select'].format(
            lang=context._chat_data.get_lang()['lang_name']),
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def left(context: ContextTypes.DEFAULT_TYPE) -> dict:
    if context._chat_data.get('group_id') is None:
        return invalid_group(context)

    try:
        rem_time = remaining_time.get_time_formatted(context._chat_data.get('lang_code'),
                                                     context._chat_data.get('group_id'))
    except HTTPApiException:
        return api_unavaliable(context)

    # Show "no more classes" page
    if rem_time['time'] is None or rem_time['time']['status'] == 3:
        page_text = context._chat_data.get_lang()['page.left.no_more']

    # Show "left to end" page
    elif rem_time['time']['status'] == 1:
        page_text = context._chat_data.get_lang()['page.left.to_end'].format(
            left=escape_markdown(rem_time['text'], version=2))

    # Show "left to start" page
    else:
        page_text = context._chat_data.get_lang()['page.left.to_start'].format(
            left=escape_markdown(rem_time['text'], version=2))

    # Disable "refresh" button if there is no classes
    if rem_time['time'] is None or rem_time['time']['status'] == 3:
        buttons = [[
            InlineKeyboardButton(text=context._chat_data.get_lang()['button.back'], callback_data='open.more'),
            InlineKeyboardButton(text=context._chat_data.get_lang()['button.menu'], callback_data='open.menu')
        ]]
    else:
        buttons = [[
            InlineKeyboardButton(text=context._chat_data.get_lang()['button.menu'], callback_data='open.menu'),
            InlineKeyboardButton(text=context._chat_data.get_lang()['button.refresh'], callback_data='open.left')
        ]]

    return {
        'text': page_text,
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def menu(context: ContextTypes.DEFAULT_TYPE) -> dict:
    buttons = [[
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.schedule'],
                             callback_data='open.schedule.today')
    ], [
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.settings'],
                             callback_data='open.settings'),
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.more'],
                             callback_data='open.more')
    ]]

    # If user is admin, then add "control panel" button
    if context._user_data.get('admin'):
        buttons.append([
            InlineKeyboardButton(text=context._chat_data.get_lang()['button.admin.panel'],
                                 callback_data='admin.open_panel')
        ])

    return {
        'text': context._chat_data.get_lang()['page.menu'],
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def more(context: ContextTypes.DEFAULT_TYPE) -> dict:
    buttons = [[
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.calls'],
                             callback_data='open.calls'),
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.left'],
                             callback_data='open.left')
    ], [
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.info'],
                             callback_data='open.info')
    ], [
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.back'],
                             callback_data='open.menu')
    ]]

    return {
        'text': context._chat_data.get_lang()['page.more'],
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def notification_feature_suggestion(context: ContextTypes.DEFAULT_TYPE) -> dict:
    buttons = [[
        InlineKeyboardButton(text=context._chat_data.get_lang()['text.yes'],
                             callback_data='set.cl_notif_15m#state=1&suggestion=1'),
        InlineKeyboardButton(text=context._chat_data.get_lang()['text.no'],
                             callback_data='close_page')
    ]]

    return {
        'text': context._chat_data.get_lang()['page.notification_feature_suggestion'],
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def schedule(context: ContextTypes.DEFAULT_TYPE, date: _date | str) -> dict:
    # Create "date_str" and "date" variables
    if isinstance(date, _date):
        date_str = date.strftime('%Y-%m-%d')
    else:
        date_str = date
        date = datetime.strptime(date, '%Y-%m-%d').date()

    # Get schedule
    try:
        date_start = date - timedelta(days=date.weekday() + 7)
        date_end = date_start + timedelta(days=20)
        schedule = api.timetable_group(context._chat_data.get('group_id'), date_start, date_end)

    except HTTPError as err:
        if err.response.status_code == 422:
            return invalid_group(context)
        return api_unavaliable(context)

    except HTTPApiException:
        return api_unavaliable(context)

    # Find schedule of current day
    cur_day_schedule = None
    for day in schedule:
        if day.date == date_str:
            cur_day_schedule = day
            break

    # Create the schedule page content
    lang = context._chat_data.get_lang()
    if cur_day_schedule is not None:
        msg_text = lang['page.schedule'].format(
            date=_get_localized_date(context, date),
            schedule=_create_schedule_section(context, cur_day_schedule)
        )

    # If there is no lesson for the current day
    else:
        # Variables with the number of days you need to skip to reach a day with lessons
        skip_left = _count_no_lesson_days(schedule, date, direction_right=False)
        skip_right = _count_no_lesson_days(schedule, date, direction_right=True)
        if skip_right is None:
            skip_right = (date_end - date + timedelta(days=1)).days
        if skip_left is None:
            skip_left = (date - date_start + timedelta(days=1)).days

        # If there are no lessons for multiple days
        # Then combine all the days without lessons into one page
        if skip_left > 1 or skip_right > 1:
            msg_text = lang['page.schedule.empty.multiple_days'].format(
                dateStart=_get_localized_date(context, date - timedelta(days=skip_left - 1)),
                dateEnd=  _get_localized_date(context, date + timedelta(days=skip_right - 1)),
            )
        # If no lessons for only one day
        else:
            msg_text = lang['page.schedule.empty'].format(date=_get_localized_date(context, date))

    # Decide whether to show the "today" button, and also
    # decide the "next" and "previous" buttons skip values
    if cur_day_schedule is not None:
        next_day_date = date + timedelta(days=1)
        prev_day_date = date - timedelta(days=1)
        enable_today_button = date != _date.today()
    else:
        next_day_date = date + timedelta(days=skip_right)
        prev_day_date = date - timedelta(days=skip_left)
        enable_today_button = not next_day_date > _date.today() > prev_day_date

    # Create buttons
    buttons = [
        InlineKeyboardButton(text=lang['button.navigation.day_previous'],
                             callback_data='open.schedule.day#date=' + prev_day_date.strftime('%Y-%m-%d')),
        InlineKeyboardButton(text=lang['button.navigation.day_next'],
                             callback_data='open.schedule.day#date=' + next_day_date.strftime('%Y-%m-%d')),
        InlineKeyboardButton(text=lang['button.navigation.week_previous'],
                             callback_data='open.schedule.day#date=' + (date - timedelta(days=7)).strftime('%Y-%m-%d')),
        InlineKeyboardButton(text=lang['button.navigation.week_next'],
                             callback_data='open.schedule.day#date=' + (date + timedelta(days=7)).strftime('%Y-%m-%d')),
        InlineKeyboardButton(text=lang['button.menu'], callback_data='open.menu')
    ]

    if enable_today_button:
        buttons.append(InlineKeyboardButton(text=lang['button.navigation.today'], callback_data='open.schedule.today'))

    # Split buttons into 2-wide rows
    buttons = array_split(buttons, 2)

    return {
        'text': msg_text,
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def settings(context: ContextTypes.DEFAULT_TYPE) -> dict:
    lang = context._chat_data.get_lang()
    cl_notif_15m_enabled = context._chat_data.get('cl_notif_15m')
    cl_notif_1m_enabled = context._chat_data.get('cl_notif_1m')

    # Get chat group name
    if context._chat_data.get('group_id') is not None:
        if API_TYPE == API_TYPE_CACHED:
            group = escape_markdown(api._cache.get_group(context._chat_data.get('group_id'))[2], version=2)
        else:
            group = context._chat_data.get('group_id')
    else:
        group = lang['text.not_selected']

    buttons = [[
        InlineKeyboardButton(text=lang['button.select_group'],
                             callback_data='open.select_group'),
        InlineKeyboardButton(text=lang['button.select_lang'],
                             callback_data='open.select_lang')
    ], [
        InlineKeyboardButton(text=lang['button.settings.cl_notif_15m'],
                             callback_data=f'set.cl_notif_15m#state={int(not cl_notif_15m_enabled)}')
    ], [
        InlineKeyboardButton(text=lang['button.settings.cl_notif_1m'],
                             callback_data=f'set.cl_notif_1m#state={int(not cl_notif_1m_enabled)}')
    ], [
        InlineKeyboardButton(text=lang['button.back'],
                             callback_data='open.menu')
    ]]

    def get_icon(setting: bool) -> str:
        return '✅' if setting else '❌'

    page_text = lang['page.settings'].format(
        group_id=group,
        cl_notif_15m=get_icon(cl_notif_15m_enabled),
        cl_notif_1m=get_icon(cl_notif_1m_enabled)
    )

    return {
        'text': page_text,
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def statistic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict:
    chat_dir = tg_logger.get_chat_log_dir(update.effective_chat.id)

    # Get first message date and message count
    with open(os.path.join(chat_dir, 'messages.txt')) as fp:
        for messages, line in enumerate(fp):
            if messages == 0:
                first_msg_date = line[1:line.index(']')]

    # Get number of button clicks
    with open(os.path.join(chat_dir, 'cb_queries.txt')) as fp:
        for clicks, _ in enumerate(fp):
            pass

    message_text = '*Statistic*\n\nThis chat ID: {chat_id}\nYour ID: {user_id}\nMessages: {messages}\nButton clicks: {clicks}\nFirst message: {first}'.format(
        chat_id=update.effective_chat.id,
        user_id=update.effective_user.id,
        messages=messages,
        clicks=clicks,
        first=escape_markdown(first_msg_date, version=2)
    )

    buttons = [[
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.menu'],
                             callback_data='open.menu'),
        InlineKeyboardButton(text='How Did We Get Here?',
                             url='https://github.com/cubicbyte/dteubot')
    ]]

    return {
        'text': message_text,
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }


def structure_list(context: ContextTypes.DEFAULT_TYPE) -> dict:
    try:
        structures = api.list_structures()
    except HTTPApiException:
        return api_unavaliable(context)

    # If there is only one structure, show faculties page
    if len(structures) == 1:
        return faculty_list(context, structures[0].id)

    buttons = [[
        InlineKeyboardButton(text=context._chat_data.get_lang()['button.back'], callback_data=f'open.menu')
    ]]

    for structure in structures:
        buttons.append([
            InlineKeyboardButton(text=structure.fullName,
                                 callback_data=f'select.schedule.structure#structureId={structure.id}')
        ])

    return {
        'text': context._chat_data.get_lang()['page.structure'],
        'reply_markup': InlineKeyboardMarkup(buttons),
        'parse_mode': 'MarkdownV2'
    }









def _get_calls_section_text() -> str:
    """
    Get calls section text in the calls page

    ## Example:
    ```
    1) 08:20 - 09:40
    2) 10:05 - 11:25
    3) 12:05 - 13:25
    4) 13:50 - 15:10
    5) 15:25 - 16:45
    6) 17:00 - 18:20
    7) 18:30 - 19:50
    8) 19:55 - 21:40
    ```
    """

    parts = []

    for call in api.timetable_call_schedule():
        parts.append('`{number})` *{timeStart}* `-` *{timeEnd}*'.format(**call.__dict__))

    return '\n'.join(parts)


def _get_notification_schedule_section(day: TimeTableDate) -> str:
    """
    Creates a schedule section for the notification page

    ## Example:
    ```
    2) ІнМов за ПроСпр[КонсЕкз]
    3) "В" МатемЛогіка[КонсЕкз]
    ```
    """
    f = '`{0})` *{1}*`[{2}]`\n'
    section = ''

    for l in day.lessons:
        for p in l.periods:
            section += f.format(
                l.number,
                escape_markdown(p.disciplineShortName, version=2),
                escape_markdown(p.typeStr, version=2))

    return section[:-1]


def _count_no_lesson_days(
        schedule: list[TimeTableDate],
        date: _date,
        direction_right=True) -> int | None:
    """
    Counts the number of days without lessons
    """

    if not direction_right:
        schedule = reversed(schedule)

    res = None
    for day in schedule:
        day_date = datetime.strptime(day.date, '%Y-%m-%d').date()
        if direction_right:
            if day_date > date:
                res = day_date - date
                break
        else:
            if day_date < date:
                res = date - day_date
                break

    return res.days


def _get_localized_date(context: ContextTypes.DEFAULT_TYPE, date: _date) -> str:
    """
    Returns a localized date string

    Example:
    --------
    📅 18 трав. 2023 р. [П'ятниця] 📅
    """

    date_localized = escape_markdown(format_date(date, locale=context._chat_data.get('lang_code')), version=2)
    week_day_localized = context._chat_data.get_lang()['text.time.week_day.' + str(date.weekday())]
    full_date_localized = f"*{date_localized}* `[`*{week_day_localized}*`]`"

    return full_date_localized


def _create_schedule_section(context: ContextTypes.DEFAULT_TYPE, day: TimeTableDate) -> str:
    """
    Creates a schedule section for the schedule page

    ## Example:
    ```
    ———— 10:05 ——— 11:25 ————
      ІнМов за ПроСпр[КонсЕкз]
    2 Онлайн
      Кулаженко Олена Петрiвна +1
    ———— 12:05 ——— 13:25 ————
      "В" МатемЛогіка[КонсЕкз]
    3 Онлайн
      Котляр Валерій Юрійович
    —――—――——―—―――—―—―――――――――
    ```
    """

    schedule_section = ''

    for lesson in day.lessons:
        for period in lesson.periods:
            # Escape ONLY USED api result not to break telegram markdown
            # DO NOT DELETE COMMENTS
            period.typeStr = escape_markdown(period.typeStr, version=2)
            period.classroom = escape_markdown(period.classroom, version=2)
            # period.disciplineFullName = escape_markdown(period.disciplineFullName, version=2)
            period.disciplineShortName = escape_markdown(period.disciplineShortName, version=2)
            period.timeStart = escape_markdown(period.timeStart, version=2)
            period.timeEnd = escape_markdown(period.timeEnd, version=2)
            # period.teachersName = escape_markdown(period.teachersName, version=2)
            period.teachersNameFull = escape_markdown(period.teachersNameFull, version=2)
            # period.chairName = escape_markdown(period.chairName, version=2)
            # period.dateUpdated = escape_markdown(period.dateUpdated, version=2)
            # period.groups = escape_markdown(period.groups, version=2)

            # If there are multiple teachers, display the first one and add +n to the end
            if ',' in period.teachersName:
                count = str(period.teachersNameFull.count(','))
                period.teachersName = period.teachersName[:period.teachersName.index(',')] + ' \\+' + count
                period.teachersNameFull = period.teachersNameFull[:period.teachersNameFull.index(',')] + ' \\+' + count

            schedule_section += context._chat_data.get_lang()['text.schedule.period'].format(
                **period.__dict__,
                lessonNumber=lesson.number
            )

    schedule_section += '`—――—―``―——``―—―``――``—``―``—``――――``――``―――`'
    return schedule_section
