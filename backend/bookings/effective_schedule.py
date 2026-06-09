"""
Эффективный график: явная запись WorkSchedule в БД переопределяет шаблон из профиля пользователя.
Логика шаблонов совпадает с app/utils/workScheduleTemplates.ts (date-fns getDay: вс=0 … сб=6).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, List, Optional, Tuple

from django.contrib.auth import get_user_model

User = get_user_model()

ALLOWED_TEMPLATE_IDS = frozenset({
    'standard-5',
    'peak-wed-sun',
    'shift-cycle',
    'flex-evening',
    'intensive-6',
})
ALLOWED_SHIFT_CYCLES = frozenset({'2-2', '3-3', '4-4'})


def _js_weekday(d: date) -> int:
    """Соответствие JS getDay: 0=вс … 6=сб."""
    return (d.weekday() + 1) % 7


def _is_in_cycle_work_slot(
    d: date,
    anchor: date,
    work_days: int,
    off_days: int,
) -> bool:
    a = datetime(anchor.year, anchor.month, anchor.day).date()
    t = datetime(d.year, d.month, d.day).date()
    diff = (t - a).days
    cycle = work_days + off_days
    if cycle == 0:
        return False
    m = (diff % cycle + cycle) % cycle
    return m < work_days


@dataclass
class DayConfig:
    type: str
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    breaks: List[Tuple[time, time]] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.breaks is None:
            self.breaks = []


def _t(h: int, m: int) -> time:
    return time(h, m)


def resolve_day_config_from_user_template(user, d: date) -> DayConfig:
    """Правило дня по полям шаблона на пользователе (без учёта WorkSchedule)."""
    template_id = getattr(user, 'work_schedule_template', None) or 'standard-5'
    if template_id not in ALLOWED_TEMPLATE_IDS:
        template_id = 'standard-5'

    shift = getattr(user, 'shift_cycle', None) or '2-2'
    if shift not in ALLOWED_SHIFT_CYCLES:
        shift = '2-2'

    anchor: Optional[date] = getattr(user, 'shift_anchor_date', None)
    if anchor is None:
        anchor = date.today()

    day = _js_weekday(d)
    no_break: List[Tuple[time, time]] = []

    if template_id == 'standard-5':
        if 1 <= day <= 5:
            return DayConfig('workday', _t(10, 0), _t(20, 0), no_break)
        return DayConfig('nonworkday', None, None, no_break)

    if template_id == 'peak-wed-sun':
        if day in (0, 3, 4, 5, 6):
            return DayConfig('workday', _t(11, 0), _t(21, 0), no_break)
        return DayConfig('nonworkday', None, None, no_break)

    if template_id == 'shift-cycle':
        parts = shift.split('-')
        w, o = int(parts[0]), int(parts[1])
        work = _is_in_cycle_work_slot(d, anchor, w, o)
        if work:
            return DayConfig('workday', _t(10, 0), _t(22, 0), no_break)
        return DayConfig('nonworkday', None, None, no_break)

    if template_id == 'flex-evening':
        if 1 <= day <= 5:
            return DayConfig('workday', _t(17, 0), _t(21, 0), no_break)
        if day == 6:
            return DayConfig('workday', _t(10, 0), _t(20, 0), no_break)
        return DayConfig('nonworkday', None, None, no_break)

    if template_id == 'intensive-6':
        if 1 <= day <= 6:
            return DayConfig('workday', _t(9, 0), _t(21, 0), no_break)
        return DayConfig('nonworkday', None, None, no_break)

    return DayConfig('nonworkday', None, None, no_break)


def day_config_to_public_dict(
    d: date,
    cfg: DayConfig,
) -> dict[str, Any]:
    """JSON для API в формате WorkSchedule (camelCase полей)."""
    out: dict[str, Any] = {
        'id': None,
        'date': d.isoformat(),
        'type': cfg.type,
    }
    if cfg.type == 'workday' and cfg.start_time and cfg.end_time:
        out['startTime'] = cfg.start_time.strftime('%H:%M')
        out['endTime'] = cfg.end_time.strftime('%H:%M')
    else:
        out['startTime'] = None
        out['endTime'] = None
    out['breaks'] = [
        {'id': None, 'startTime': a.strftime('%H:%M'), 'endTime': b.strftime('%H:%M')}
        for a, b in (cfg.breaks or [])
    ]
    return out


class EffectiveForValidation:
    __slots__ = ('type', 'start_time', 'end_time', 'breaks')

    def __init__(
        self,
        type_: str,
        start_time: Optional[time],
        end_time: Optional[time],
        breaks: List[Any],
    ):
        self.type = type_
        self.start_time = start_time
        self.end_time = end_time
        self.breaks = breaks


def get_effective_schedule_for_validation(user, d: date) -> EffectiveForValidation:
    """Явная запись WorkSchedule или шаблон профиля."""
    from .models import WorkSchedule

    try:
        ws = WorkSchedule.objects.prefetch_related('breaks').get(user=user, date=d)
        return EffectiveForValidation(
            ws.type,
            ws.start_time,
            ws.end_time,
            list(ws.breaks.all()),
        )
    except WorkSchedule.DoesNotExist:
        cfg = resolve_day_config_from_user_template(user, d)
        return EffectiveForValidation(cfg.type, cfg.start_time, cfg.end_time, [])


def merge_schedule_range_for_public_api(user, start: date, end: date) -> List[dict[str, Any]]:
    """
    Все дни в диапазоне [start, end]: сначала проверяется WorkSchedule, иначе шаблон.
    """
    from .models import WorkSchedule
    from .serializers import WorkScheduleSerializer

    rows = (
        WorkSchedule.objects.filter(user=user, date__gte=start, date__lte=end)
        .prefetch_related('breaks')
        .order_by('date')
    )
    by_date = {r.date: r for r in rows}

    out: List[dict[str, Any]] = []
    cur = start
    while cur <= end:
        if cur in by_date:
            inst = by_date[cur]
            data = WorkScheduleSerializer(inst).data
            out.append(data)
        else:
            cfg = resolve_day_config_from_user_template(user, cur)
            out.append(day_config_to_public_dict(cur, cfg))
        cur += timedelta(days=1)
    return out
