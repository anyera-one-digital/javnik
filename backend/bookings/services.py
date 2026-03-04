"""
Сервисы для работы с бронированиями и графиком работы.
"""
from datetime import date, time, timedelta

from .models import WorkSchedule, WorkBreak


def create_default_work_schedule(user):
    """
    Создаёт график работы по умолчанию для нового пользователя:
    - Пн–Пт: рабочий день 10:00–22:00, перерыв на обед 13:00–14:00
    - Сб–Вс: выходные

    Создаются записи на 6 месяцев вперёд от текущей даты.
    """
    today = date.today()
    end_date = today + timedelta(days=180)  # 6 месяцев

    schedules_to_create = []
    current = today

    while current <= end_date:
        # weekday(): Monday=0, Sunday=6
        is_weekday = current.weekday() < 5  # Пн=0..Пт=4

        if is_weekday:
            schedule = WorkSchedule(
                user=user,
                date=current,
                type='workday',
                start_time=time(10, 0),
                end_time=time(22, 0),
            )
        else:
            schedule = WorkSchedule(
                user=user,
                date=current,
                type='nonworkday',
                start_time=None,
                end_time=None,
            )

        schedules_to_create.append((schedule, is_weekday))
        current += timedelta(days=1)

    # Создаём расписания
    for schedule, is_weekday in schedules_to_create:
        schedule.save()
        if is_weekday:
            WorkBreak.objects.create(
                schedule=schedule,
                start_time=time(13, 0),
                end_time=time(14, 0),
            )
