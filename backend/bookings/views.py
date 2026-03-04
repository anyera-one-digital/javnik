from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from django.db.models import Q, Max
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from .models import Customer, Service, ServiceImage, Member, Event, Booking, WorkSchedule, Review
from .serializers import (
    CustomerSerializer,
    ServiceSerializer,
    MemberSerializer,
    EventSerializer,
    BookingSerializer,
    WorkScheduleSerializer,
    ReviewSerializer
)

User = get_user_model()


class CustomerViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления клиентами
    """
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Фильтруем только клиентов текущего пользователя
        return Customer.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Автоматически устанавливаем владельца при создании
        serializer.save(user=self.request.user)


class ServiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления услугами
    """
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Отключаем пагинацию для услуг

    def get_queryset(self):
        # Фильтруем только услуги текущего пользователя
        return Service.objects.filter(user=self.request.user).prefetch_related('portfolio_images').select_related('user')
    
    def get_serializer_context(self):
        """
        Добавляем request в context для формирования полных URL изображений
        """
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        # Автоматически устанавливаем владельца и активность при создании
        # Убеждаемся, что active=True для новых услуг
        service = serializer.save(user=self.request.user, active=True)
        
        # Обрабатываем изображения портфолио
        portfolio_images = self.request.FILES.getlist('portfolio_images')
        for index, image_file in enumerate(portfolio_images):
            ServiceImage.objects.create(
                service=service,
                image=image_file,
                order=index
            )

    def perform_update(self, serializer):
        service = serializer.save()
        
        # Обрабатываем удаление заглавного изображения
        if self.request.POST.get('remove_cover_image') == 'true':
            if service.cover_image:
                service.cover_image.delete()
                service.cover_image = None
                service.save()
        
        # Обрабатываем удаление изображений портфолио
        removed_ids_str = self.request.POST.get('removed_portfolio_image_ids')
        if removed_ids_str:
            try:
                import json
                removed_ids = json.loads(removed_ids_str)
                if isinstance(removed_ids, list):
                    ServiceImage.objects.filter(service=service, id__in=removed_ids).delete()
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Обрабатываем новые изображения портфолио
        portfolio_images = self.request.FILES.getlist('portfolio_images')
        if portfolio_images:
            # Получаем текущий максимальный порядок
            max_order = ServiceImage.objects.filter(service=service).aggregate(
                max_order=models.Max('order')
            )['max_order'] or -1
            
            # Добавляем новые изображения
            for index, image_file in enumerate(portfolio_images):
                ServiceImage.objects.create(
                    service=service,
                    image=image_file,
                    order=max_order + index + 1
                )


class MemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления сотрудниками
    """
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Фильтруем только сотрудников текущего пользователя
        return Member.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Автоматически устанавливаем владельца при создании
        serializer.save(user=self.request.user)


class EventViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления событиями
    """
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Фильтруем только события текущего пользователя
        queryset = Event.objects.filter(user=self.request.user)
        
        # Фильтрация по дате, если указана
        date = self.request.query_params.get('date', None)
        if date:
            queryset = queryset.filter(date=date)
        
        return queryset.order_by('date', 'start_time')

    def create(self, request, *args, **kwargs):
        """
        Переопределяем create для правильной обработки ValidationError из perform_create
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f'EventViewSet.create: Received data: {request.data}')
        
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f'EventViewSet.create: Validation errors: {serializer.errors}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            self.perform_create(serializer)
        except ValidationError as e:
            logger.error(f'EventViewSet.create: ValidationError in perform_create: {e}')
            # Возвращаем ValidationError как ошибку валидации
            if hasattr(e, 'detail'):
                if isinstance(e.detail, dict):
                    return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
                elif isinstance(e.detail, list):
                    return Response({'non_field_errors': e.detail}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'non_field_errors': [str(e.detail)]}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'non_field_errors': [str(e)]}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f'EventViewSet.create: Unexpected error: {e}', exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        from datetime import datetime, timedelta
        
        # Получаем данные из запроса
        data = serializer.validated_data
        date = data.get('date')
        start_time = data.get('start_time')
        duration = data.get('duration')
        
        # Вычисляем время окончания
        start_datetime = datetime.combine(date, start_time)
        end_datetime = start_datetime + timedelta(minutes=duration)
        end_time = end_datetime.time()
        
        # Проверяем график работы на эту дату
        try:
            work_schedule = WorkSchedule.objects.get(user=self.request.user, date=date)
            
            # Если это выходной день
            if work_schedule.type in ['nonworkday', 'sickleave', 'vacation']:
                type_names = {
                    'nonworkday': 'выходной день',
                    'sickleave': 'больничный',
                    'vacation': 'отпуск'
                }
                raise ValidationError({'non_field_errors': [f'Нельзя создать событие в {type_names.get(work_schedule.type, "нерабочий день")}.']})
            
            # Если это рабочий день, проверяем рабочее время
            if work_schedule.type == 'workday' and work_schedule.start_time and work_schedule.end_time:
                # Проверяем, что время начала и окончания попадают в рабочие часы
                if start_time < work_schedule.start_time or end_time > work_schedule.end_time:
                    raise ValidationError({
                        'non_field_errors': [
                            f'Время события выходит за пределы рабочего времени '
                            f'({work_schedule.start_time.strftime("%H:%M")} - {work_schedule.end_time.strftime("%H:%M")}).'
                        ]
                    })
                
                # Проверяем перерывы
                breaks = work_schedule.breaks.all()
                for break_item in breaks:
                    # Проверяем пересечение времени события с перерывом
                    if (start_time < break_item.end_time and end_time > break_item.start_time):
                        raise ValidationError({
                            'non_field_errors': [
                                f'Время события пересекается с перерывом '
                                f'({break_item.start_time.strftime("%H:%M")} - {break_item.end_time.strftime("%H:%M")}).'
                            ]
                        })
        except WorkSchedule.DoesNotExist:
            # Если графика нет, разрешаем создание
            pass
        
        # Проверяем конфликты с существующими бронированиями
        existing_bookings = Booking.objects.filter(
            user=self.request.user,
            date=date
        ).exclude(
            status__in=['cancelled', 'completed']
        )
        
        for existing_booking in existing_bookings:
            # Проверяем пересечение временных интервалов
            if (start_time < existing_booking.end_time and end_time > existing_booking.start_time):
                raise ValidationError(
                    f'Время уже занято другой записью '
                    f'({existing_booking.start_time.strftime("%H:%M")} - {existing_booking.end_time.strftime("%H:%M")}).'
                )
        
        # Проверяем конфликты с существующими событиями
        existing_events = Event.objects.filter(
            user=self.request.user,
            date=date
        )
        
        for existing_event in existing_events:
            existing_start = existing_event.start_time
            existing_end = (datetime.combine(existing_event.date, existing_start) + 
                          timedelta(minutes=existing_event.duration)).time()
            
            # Проверяем пересечение временных интервалов
            if (start_time < existing_end and end_time > existing_start):
                raise ValidationError({
                    'non_field_errors': [
                        f'Время уже занято другим событием '
                        f'({existing_start.strftime("%H:%M")} - {existing_end.strftime("%H:%M")}).'
                    ]
                })
        
        # Автоматически устанавливаем владельца при создании
        serializer.save(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        """
        Переопределяем update для правильной обработки ValidationError из perform_update
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            self.perform_update(serializer)
        except ValidationError as e:
            # Возвращаем ValidationError как ошибку валидации
            if hasattr(e, 'detail'):
                if isinstance(e.detail, dict):
                    raise ValidationError(e.detail)
                elif isinstance(e.detail, list):
                    raise ValidationError({'non_field_errors': e.detail})
                else:
                    raise ValidationError({'non_field_errors': [str(e.detail)]})
            else:
                raise ValidationError({'non_field_errors': [str(e)]})
        
        return Response(serializer.data)

    def perform_update(self, serializer):
        from datetime import datetime, timedelta
        
        # Получаем данные из запроса
        data = serializer.validated_data
        date = data.get('date', serializer.instance.date)
        start_time = data.get('start_time', serializer.instance.start_time)
        duration = data.get('duration', serializer.instance.duration)
        
        # Вычисляем время окончания
        start_datetime = datetime.combine(date, start_time)
        end_datetime = start_datetime + timedelta(minutes=duration)
        end_time = end_datetime.time()
        
        # Проверяем график работы на эту дату
        try:
            work_schedule = WorkSchedule.objects.get(user=self.request.user, date=date)
            
            # Если это выходной день
            if work_schedule.type in ['nonworkday', 'sickleave', 'vacation']:
                type_names = {
                    'nonworkday': 'выходной день',
                    'sickleave': 'больничный',
                    'vacation': 'отпуск'
                }
                raise ValidationError({'non_field_errors': [f'Нельзя создать событие в {type_names.get(work_schedule.type, "нерабочий день")}.']})
            
            # Если это рабочий день, проверяем рабочее время
            if work_schedule.type == 'workday' and work_schedule.start_time and work_schedule.end_time:
                # Проверяем, что время начала и окончания попадают в рабочие часы
                if start_time < work_schedule.start_time or end_time > work_schedule.end_time:
                    raise ValidationError({
                        'non_field_errors': [
                            f'Время события выходит за пределы рабочего времени '
                            f'({work_schedule.start_time.strftime("%H:%M")} - {work_schedule.end_time.strftime("%H:%M")}).'
                        ]
                    })
                
                # Проверяем перерывы
                breaks = work_schedule.breaks.all()
                for break_item in breaks:
                    # Проверяем пересечение времени события с перерывом
                    if (start_time < break_item.end_time and end_time > break_item.start_time):
                        raise ValidationError({
                            'non_field_errors': [
                                f'Время события пересекается с перерывом '
                                f'({break_item.start_time.strftime("%H:%M")} - {break_item.end_time.strftime("%H:%M")}).'
                            ]
                        })
        except WorkSchedule.DoesNotExist:
            # Если графика нет, разрешаем создание
            pass
        
        # Проверяем конфликты с существующими бронированиями
        existing_bookings = Booking.objects.filter(
            user=self.request.user,
            date=date
        ).exclude(
            status__in=['cancelled', 'completed']
        )
        
        for existing_booking in existing_bookings:
            # Проверяем пересечение временных интервалов
            if (start_time < existing_booking.end_time and end_time > existing_booking.start_time):
                raise ValidationError(
                    f'Время уже занято другой записью '
                    f'({existing_booking.start_time.strftime("%H:%M")} - {existing_booking.end_time.strftime("%H:%M")}).'
                )
        
        # Проверяем конфликты с существующими событиями (исключая текущее)
        existing_events = Event.objects.filter(
            user=self.request.user,
            date=date
        ).exclude(id=serializer.instance.id)
        
        for existing_event in existing_events:
            existing_start = existing_event.start_time
            existing_end = (datetime.combine(existing_event.date, existing_start) + 
                          timedelta(minutes=existing_event.duration)).time()
            
            # Проверяем пересечение временных интервалов
            if (start_time < existing_end and end_time > existing_start):
                raise ValidationError({
                    'non_field_errors': [
                        f'Время уже занято другим событием '
                        f'({existing_start.strftime("%H:%M")} - {existing_end.strftime("%H:%M")}).'
                    ]
                })
        
        # Сохраняем обновление
        serializer.save()

    @action(detail=True, methods=['patch'])
    def update_booked_slots(self, request, pk=None):
        """
        Обновление количества забронированных мест
        """
        event = self.get_object()
        booked_slots = request.data.get('booked_slots', event.booked_slots)
        event.booked_slots = booked_slots
        event.save()
        serializer = self.get_serializer(event)
        return Response(serializer.data)


class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления бронированиями
    """
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Фильтруем только бронирования текущего пользователя
        queryset = Booking.objects.filter(user=self.request.user)
        
        # Фильтрация по дате, если указана
        date = self.request.query_params.get('date', None)
        if date:
            queryset = queryset.filter(date=date)
        
        # Фильтрация по сотруднику, если указан
        employee_id = self.request.query_params.get('employeeId', None)
        if employee_id:
            queryset = queryset.filter(member_id=employee_id)
        
        return queryset.order_by('date', 'start_time')

    def create(self, request, *args, **kwargs):
        """
        Переопределяем create для валидации конфликтов
        """
        import traceback
        try:
            return self._create_booking(request)
        except Exception as e:
            tb = traceback.format_exc()
            print(f'[BookingViewSet.create] Unexpected error: {e}\n{tb}')
            return Response({
                'error': str(e),
                'detail': tb if settings.DEBUG else 'Ошибка при создании записи. Проверьте логи сервера.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_booking(self, request):
        """Внутренняя логика создания бронирования"""
        # Получаем данные из запроса
        customer_id = request.data.get('customerId')
        service_id = request.data.get('serviceId')
        date = request.data.get('date')
        start_time = request.data.get('startTime')
        duration = request.data.get('duration')
        
        if not all([customer_id, service_id, date, start_time, duration]):
            return Response({
                'error': 'Необходимо указать клиента, услугу, дату, время начала и длительность.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем существование клиента
        try:
            customer = Customer.objects.get(id=customer_id, user=request.user)
        except Customer.DoesNotExist:
            return Response({
                'error': 'Клиент не найден.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Получаем услугу для определения длительности
        try:
            service = Service.objects.get(id=service_id, user=request.user)
        except Service.DoesNotExist:
            return Response({
                'error': 'Услуга не найдена.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Вычисляем время окончания
        start_datetime = datetime.strptime(f'{date} {start_time}', '%Y-%m-%d %H:%M')
        end_datetime = start_datetime + timedelta(minutes=int(duration))
        end_time = end_datetime.strftime('%H:%M')
        
        # Проверяем график работы на эту дату
        try:
            work_schedule = WorkSchedule.objects.get(user=request.user, date=date)
            
            # Если это выходной день
            if work_schedule.type in ['nonworkday', 'sickleave', 'vacation']:
                type_names = {
                    'nonworkday': 'выходной день',
                    'sickleave': 'больничный',
                    'vacation': 'отпуск'
                }
                return Response({
                    'error': f'Нельзя создать запись в {type_names.get(work_schedule.type, "нерабочий день")}.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Если это рабочий день, проверяем рабочее время
            if work_schedule.type == 'workday' and work_schedule.start_time and work_schedule.end_time:
                # Проверяем, что время начала и окончания попадают в рабочие часы
                if start_time < work_schedule.start_time.strftime('%H:%M') or end_time > work_schedule.end_time.strftime('%H:%M'):
                    return Response({
                        'error': f'Время записи выходит за пределы рабочего времени ({work_schedule.start_time.strftime("%H:%M")} - {work_schedule.end_time.strftime("%H:%M")}).'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Проверяем перерывы
                breaks = work_schedule.breaks.all()
                for break_item in breaks:
                    break_start = break_item.start_time.strftime('%H:%M')
                    break_end = break_item.end_time.strftime('%H:%M')
                    # Проверяем пересечение времени записи с перерывом
                    if (start_time < break_end and end_time > break_start):
                        return Response({
                            'error': f'Время записи пересекается с перерывом ({break_start} - {break_end}).'
                        }, status=status.HTTP_400_BAD_REQUEST)
        except WorkSchedule.DoesNotExist:
            # Если графика нет, разрешаем создание (можно добавить проверку по умолчанию)
            pass
        
        # Проверяем конфликты с существующими бронированиями
        # Проверяем только активные бронирования (не отмененные и не завершенные)
        existing_bookings = Booking.objects.filter(
            user=request.user,
            date=date
        ).exclude(
            status__in=['cancelled', 'completed']
        )
        
        for existing_booking in existing_bookings:
            existing_start = existing_booking.start_time.strftime('%H:%M')
            existing_end = existing_booking.end_time.strftime('%H:%M')
            
            # Проверяем пересечение временных интервалов
            if (start_time < existing_end and end_time > existing_start):
                return Response({
                    'error': f'Время уже занято другой записью ({existing_start} - {existing_end}).'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Проверяем конфликты с существующими событиями
        existing_events = Event.objects.filter(
            user=request.user,
            date=date
        )
        
        for existing_event in existing_events:
            existing_start = existing_event.start_time.strftime('%H:%M')
            existing_end_datetime = datetime.combine(existing_event.date, existing_event.start_time) + timedelta(minutes=existing_event.duration)
            existing_end = existing_end_datetime.strftime('%H:%M')
            
            # Проверяем пересечение временных интервалов
            if (start_time < existing_end and end_time > existing_start):
                return Response({
                    'error': f'Время уже занято событием "{existing_event.name}" ({existing_start} - {existing_end}).'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Если все проверки пройдены, создаем бронирование
        serializer = self.get_serializer(data={
            'customer': customer_id,
            'service': service_id,
            'date': date,
            'start_time': start_time,
            'end_time': end_time,
            'notes': request.data.get('notes', ''),
            'status': 'pending'
        })
        
        if serializer.is_valid():
            booking = serializer.save(user=request.user)
            
            # Если это бронирование на событие, увеличиваем счетчик забронированных мест
            if booking.event:
                booking.event.booked_slots += 1
                booking.event.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def perform_create(self, serializer):
        # Этот метод больше не используется напрямую, но оставляем для совместимости
        booking = serializer.save(user=self.request.user)
        
        # Если это бронирование на событие, увеличиваем счетчик забронированных мест
        if booking.event:
            booking.event.booked_slots += 1
            booking.event.save()


# Публичные endpoints (не требуют авторизации)
@api_view(['GET'])
@permission_classes([AllowAny])
def public_events_view(request, username):
    """
    Получение публичных событий пользователя по username
    GET /api/public/events/<username>/
    """
    try:
        user = User.objects.get(username=username, is_active=True)
    except User.DoesNotExist:
        return Response({
            'error': 'Пользователь не найден.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    queryset = Event.objects.filter(user=user)
    
    # Фильтрация по дате, если указана
    date = request.query_params.get('date', None)
    if date:
        queryset = queryset.filter(date=date)
    
    serializer = EventSerializer(queryset.order_by('date', 'start_time'), many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_services_view(request, username):
    """
    Получение публичных услуг пользователя по username
    GET /api/public/services/<username>/
    """
    try:
        user = User.objects.get(username=username, is_active=True)
    except User.DoesNotExist:
        return Response({
            'error': 'Пользователь не найден.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Получаем все услуги пользователя (включая неактивные для отладки)
    all_services = Service.objects.filter(user=user).prefetch_related('portfolio_images')
    
    # ВРЕМЕННО: для отладки показываем ВСЕ услуги, не только активные
    # Это поможет понять, есть ли услуги с изображениями, которые неактивны
    if settings.DEBUG:
        print(f'\n=== DEBUG: Checking ALL services (including inactive) ===')
        all_services_list = list(all_services)
        for svc in all_services_list:
            try:
                cover_check = svc.cover_image if hasattr(svc, 'cover_image') else None
                cover_str = str(cover_check) if cover_check else 'None'
                print(f'  Service "{svc.name}": active={svc.active}, cover_image="{cover_str[:50]}"')
            except Exception as e:
                print(f'  Service "{svc.name}": active={svc.active}, ERROR: {e}')
    
    # Фильтруем только активные услуги
    queryset = all_services.filter(active=True)
    
    # Логируем для отладки
    if settings.DEBUG:
        print(f'\n=== Public services for {username} ===')
        print(f'  Total services: {all_services.count()}')
        print(f'  Active services: {queryset.count()}')
        for service in all_services:
            try:
                # Более детальная проверка cover_image
                has_cover_attr = hasattr(service, 'cover_image')
                cover_image_value = None
                has_cover = False
                
                if has_cover_attr:
                    try:
                        cover_image_value = service.cover_image
                        has_cover = bool(cover_image_value)
                        if has_cover:
                            # Пытаемся получить имя файла или путь
                            try:
                                cover_file_name = str(cover_image_value) if cover_image_value else None
                                print(f'    - {service.name}: active={service.active}, has_cover={has_cover}, cover_file="{cover_file_name}"')
                            except:
                                print(f'    - {service.name}: active={service.active}, has_cover={has_cover}, cover_file="<error getting name>"')
                        else:
                            print(f'    - {service.name}: active={service.active}, has_cover={has_cover} (cover_image is None/empty)')
                    except Exception as cover_error:
                        print(f'    - {service.name}: active={service.active}, ERROR accessing cover_image: {cover_error}')
                else:
                    print(f'    - {service.name}: active={service.active}, has_cover_attr={has_cover_attr}')
                
                portfolio_count = service.portfolio_images.count() if hasattr(service, 'portfolio_images') else 0
                if has_cover:
                    print(f'      portfolio_count={portfolio_count}')
            except Exception as e:
                print(f'    - {service.name}: active={service.active}, ERROR checking images: {e}')
                import traceback
                traceback.print_exc()
    
    # Сериализуем услуги по одной с обработкой ошибок для каждой
    # Это гарантирует, что ошибка в одной услуге не помешает сериализации остальных
    services_data = []
    for service in queryset:
        service_name = getattr(service, 'name', f'Service #{service.id}')
        service_id = getattr(service, 'id', 'unknown')
        
        try:
            # Пытаемся безопасно проверить наличие изображений перед сериализацией
            try:
                has_cover = bool(service.cover_image) if hasattr(service, 'cover_image') else False
                portfolio_count = service.portfolio_images.count() if hasattr(service, 'portfolio_images') else 0
            except Exception as check_error:
                print(f'  ⚠ Warning checking images for "{service_name}": {check_error}')
                has_cover = False
                portfolio_count = 0
            
            serializer = ServiceSerializer(service, context={'request': request})
            service_data = serializer.data
            services_data.append(service_data)
            
            if settings.DEBUG:
                print(f'  ✓ Serialized service "{service_name}" (ID: {service_id}): has_cover={has_cover}, portfolio_count={portfolio_count}')
        except Exception as service_error:
            print(f'  ✗ Error serializing service "{service_name}" (ID: {service_id}): {service_error}')
            import traceback
            traceback.print_exc()
            
            # Пытаемся создать минимальную версию услуги без изображений
            try:
                minimal_data = {
                    'id': service.id,
                    'name': getattr(service, 'name', 'Unknown'),
                    'description': getattr(service, 'description', None),
                    'duration': getattr(service, 'duration', 0),
                    'price': str(getattr(service, 'price', 0)),
                    'active': getattr(service, 'active', True),
                    'cover_image': None,
                    'cover_image_url': None,
                    'portfolio_images': [],
                    'created_at': service.created_at.isoformat() if hasattr(service, 'created_at') and service.created_at else None,
                    'updated_at': service.updated_at.isoformat() if hasattr(service, 'updated_at') and service.updated_at else None,
                }
                services_data.append(minimal_data)
                print(f'  → Added minimal version of service "{service_name}"')
            except Exception as minimal_error:
                print(f'  ✗✗ Failed to create minimal version: {minimal_error}')
                import traceback
                traceback.print_exc()
                # Пропускаем эту услугу полностью
                continue
    
    if settings.DEBUG:
        print(f'  Total services serialized: {len(services_data)}/{queryset.count()}')
    
    return Response(services_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_bookings_view(request, username):
    """
    Получение публичных бронирований пользователя по username
    GET /api/public/bookings/<username>/
    """
    try:
        user = User.objects.get(username=username, is_active=True)
    except User.DoesNotExist:
        return Response({
            'error': 'Пользователь не найден.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    queryset = Booking.objects.filter(user=user).exclude(status__in=['cancelled'])
    
    # Фильтрация по дате, если указана
    date = request.query_params.get('date', None)
    if date:
        queryset = queryset.filter(date=date)
    
    # Фильтрация по диапазону дат
    start_date = request.query_params.get('start_date', None)
    end_date = request.query_params.get('end_date', None)
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
    
    serializer = BookingSerializer(queryset.order_by('date', 'start_time'), many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_schedule_view(request, username):
    """
    Получение публичного графика работы пользователя по username
    GET /api/public/schedule/<username>/
    """
    try:
        user = User.objects.get(username=username, is_active=True)
    except User.DoesNotExist:
        return Response({
            'error': 'Пользователь не найден.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    queryset = WorkSchedule.objects.filter(user=user).prefetch_related('breaks')
    
    # Фильтрация по дате, если указана
    date = request.query_params.get('date', None)
    if date:
        queryset = queryset.filter(date=date)
    
    # Фильтрация по диапазону дат
    start_date = request.query_params.get('start_date', None)
    end_date = request.query_params.get('end_date', None)
    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)
    
    serializer = WorkScheduleSerializer(queryset.order_by('date'), many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def public_booking_create_view(request, username):
    """
    Создание публичного бронирования для пользователя по username
    POST /api/public/bookings/<username>/
    """
    try:
        user = User.objects.get(username=username, is_active=True)
    except User.DoesNotExist:
        return Response({
            'error': 'Пользователь не найден.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Получаем данные из запроса
    customer_name = request.data.get('customerName')
    customer_email = request.data.get('customerEmail')
    customer_phone = request.data.get('customerPhone')
    service_id = request.data.get('serviceId')
    event_id = request.data.get('eventId')
    date = request.data.get('date')
    start_time = request.data.get('startTime')
    duration = request.data.get('duration', 60)
    notes = request.data.get('notes', '')
    
    # Валидация обязательных полей
    if not customer_name or not customer_email or not customer_phone:
        return Response({
            'error': 'Необходимо указать имя, email и телефон клиента.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Получаем или создаем клиента
    customer, created = Customer.objects.get_or_create(
        user=user,
        email=customer_email,
        defaults={
            'name': customer_name,
            'phone': customer_phone,
            'status': 'first-time'
        }
    )
    
    # Обновляем данные клиента, если он уже существует
    if not created:
        customer.name = customer_name
        customer.phone = customer_phone
        customer.save()
    
    # Получаем услугу или событие
    service = None
    event = None
    member = None
    
    if event_id:
        try:
            event = Event.objects.get(id=event_id, user=user)
            service = event.service
            member = event.member
            # Используем данные из события
            date = event.date
            start_time = event.start_time
            duration = event.duration
        except Event.DoesNotExist:
            return Response({
                'error': 'Событие не найдено.'
            }, status=status.HTTP_404_NOT_FOUND)
    elif service_id:
        try:
            service = Service.objects.get(id=service_id, user=user, active=True)
        except Service.DoesNotExist:
            return Response({
                'error': 'Услуга не найдена.'
            }, status=status.HTTP_404_NOT_FOUND)
    else:
        return Response({
            'error': 'Необходимо указать услугу или событие.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Нормализуем время и длительность
    try:
        duration_min = int(duration) if duration is not None else 60
    except (TypeError, ValueError):
        duration_min = 60
    start_time_str = (start_time or '10:00').strip()
    if len(start_time_str) > 5:
        start_time_str = start_time_str[:5]  # "13:00:00" -> "13:00"
    
    # Вычисляем время окончания
    try:
        start_datetime = datetime.strptime(f'{date} {start_time_str}', '%Y-%m-%d %H:%M')
    except ValueError as e:
        return Response({
            'error': f'Неверный формат даты или времени: {date} {start_time_str}. Ожидается YYYY-MM-DD и HH:MM.'
        }, status=status.HTTP_400_BAD_REQUEST)
    end_datetime = start_datetime + timedelta(minutes=duration_min)
    # В БД передаём date/time объекты — так надёжно для всех бэкендов
    booking_date = start_datetime.date()
    booking_start_time = start_datetime.time()
    booking_end_time = end_datetime.time()
    
    # Создаем бронирование
    try:
        booking = Booking.objects.create(
            user=user,
            customer=customer,
            service=service,
            member=member,
            event=event,
            date=booking_date,
            start_time=booking_start_time,
            end_time=booking_end_time,
            status='pending',
            notes=notes or ''
        )
    except Exception as e:
        import traceback
        return Response({
            'error': 'Не удалось создать бронирование.',
            'detail': str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Если это бронирование на событие, увеличиваем счетчик забронированных мест
    if event:
        event.booked_slots += 1
        event.save()
    
    serializer = BookingSerializer(booking)
    return Response({
        'booking': serializer.data,
        'message': 'Бронирование успешно создано.'
    }, status=status.HTTP_201_CREATED)


class WorkScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления графиком работы
    """
    serializer_class = WorkScheduleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Отключаем пагинацию

    def get_queryset(self):
        # Фильтруем только графики текущего пользователя
        queryset = WorkSchedule.objects.filter(user=self.request.user).prefetch_related('breaks')
        
        # Фильтрация по дате, если указана
        date = self.request.query_params.get('date', None)
        if date:
            queryset = queryset.filter(date=date)
        
        # Фильтрация по диапазону дат
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.order_by('date')

    def create(self, request, *args, **kwargs):
        """
        Переопределяем create для лучшей обработки ошибок
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'Creating schedule with data: {request.data}')
        
        serializer = self.get_serializer(data=request.data)
        
        if not serializer.is_valid():
            logger.error(f'Serializer validation failed')
            logger.error(f'Serializer errors: {serializer.errors}')
            logger.error(f'Request data: {request.data}')
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        logger.info(f'Schedule created successfully: {serializer.data}')
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_create(self, serializer):
        # Автоматически устанавливаем владельца при создании
        serializer.save(user=self.request.user)
    
    def get_serializer(self, *args, **kwargs):
        # Поддерживаем создание нескольких графиков за раз
        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)


@api_view(['GET'])
@permission_classes([AllowAny])
def public_reviews_view(request, username):
    """
    Получение публичных отзывов пользователя по username
    GET /api/public/reviews/<username>/
    """
    try:
        user = User.objects.get(username=username, is_active=True)
    except User.DoesNotExist:
        return Response({
            'error': 'Пользователь не найден.'
        }, status=status.HTTP_404_NOT_FOUND)
    
    queryset = Review.objects.filter(user=user).select_related('service', 'customer')
    
    serializer = ReviewSerializer(queryset.order_by('-created_at'), many=True, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)
