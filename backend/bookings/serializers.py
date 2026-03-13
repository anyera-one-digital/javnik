from rest_framework import serializers
import os
from django.conf import settings
from .models import Customer, Service, ServiceImage, Member, Event, Booking, WorkSchedule, WorkBreak, Review


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')


class ServiceImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ServiceImage
        fields = ['id', 'image', 'image_url', 'order', 'created_at']
        read_only_fields = ('id', 'created_at')
    
    def get_image_url(self, obj):
        """
        Возвращает полный URL изображения
        """
        try:
            # Проверяем наличие поля image
            if not hasattr(obj, 'image'):
                return None
            
            image = obj.image
            if not image:
                return None
            
            # Пытаемся получить URL изображения
            try:
                image_url = image.url
            except (ValueError, AttributeError) as e:
                print(f'Error getting image.url for ServiceImage {obj.id}: {e}')
                return None
            
            if not image_url:
                return None
            
            # Проверяем, существует ли файл (только для локальных файлов)
            try:
                if hasattr(image, 'path'):
                    file_path = image.path
                    if file_path and not os.path.exists(file_path):
                        print(f'Image file does not exist: {file_path}')
                        return None
            except (ValueError, AttributeError):
                # Если нет пути к файлу (например, файл хранится в S3), пропускаем проверку
                pass
            
            # Строим абсолютный URL
            request = self.context.get('request')
            if request:
                try:
                    url = request.build_absolute_uri(image_url)
                    # Заменяем внутренние Docker имена хостов на localhost для разработки
                    if '://backend:' in url:
                        url = url.replace('://backend:8000', '://localhost:8000')
                    elif '://backend/' in url:
                        url = url.replace('://backend/', '://localhost:8000/')
                    return url
                except Exception as e:
                    # Если не удалось построить абсолютный URL, возвращаем относительный
                    print(f'Error building absolute URI for image: {e}')
                    return image_url
            
            return image_url
        except Exception as e:
            # Обрабатываем любые ошибки при работе с изображением
            print(f'Error getting image URL for ServiceImage {obj.id}: {e}')
            import traceback
            traceback.print_exc()
            return None


class ServiceSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    portfolio_images = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at', 'cover_image_url', 'portfolio_images', 'active')
        # Исключаем cover_image из автоматической сериализации, используем только cover_image_url
        extra_kwargs = {
            'cover_image': {'write_only': True, 'required': False}
        }
    
    def to_representation(self, instance):
        """
        Переопределяем to_representation для обработки ошибок на уровне сериализации
        """
        try:
            return super().to_representation(instance)
        except Exception as e:
            print(f'Error in to_representation for service "{instance.name}" (ID: {instance.id}): {e}')
            import traceback
            traceback.print_exc()
            
            # Возвращаем базовое представление без изображений
            try:
                data = {
                    'id': instance.id,
                    'name': instance.name,
                    'description': instance.description,
                    'duration': instance.duration,
                    'price': str(instance.price),
                    'active': instance.active,
                    'cover_image': None,
                    'cover_image_url': None,
                    'portfolio_images': [],
                    'created_at': instance.created_at.isoformat() if instance.created_at else None,
                    'updated_at': instance.updated_at.isoformat() if instance.updated_at else None,
                }
                return data
            except Exception as fallback_error:
                print(f'Error in fallback representation: {fallback_error}')
                # Возвращаем минимальное представление
                return {
                    'id': instance.id,
                    'name': getattr(instance, 'name', 'Unknown'),
                    'description': getattr(instance, 'description', None),
                    'duration': getattr(instance, 'duration', 0),
                    'price': str(getattr(instance, 'price', 0)),
                    'active': getattr(instance, 'active', True),
                    'cover_image': None,
                    'cover_image_url': None,
                    'portfolio_images': [],
                }
    
    def get_portfolio_images(self, obj):
        """
        Возвращает сериализованные изображения портфолио с обработкой ошибок
        """
        try:
            portfolio_images = obj.portfolio_images.all()
            if not portfolio_images.exists():
                return []
            
            # Сериализуем каждое изображение отдельно с обработкой ошибок
            result = []
            for img in portfolio_images:
                try:
                    serializer = ServiceImageSerializer(img, context=self.context)
                    result.append(serializer.data)
                except Exception as img_error:
                    print(f'Error serializing portfolio image {img.id} for service "{obj.name}": {img_error}')
                    # Пропускаем проблемное изображение, продолжаем с остальными
                    continue
            
            return result
        except Exception as e:
            print(f'Error getting portfolio images for service "{obj.name}": {e}')
            import traceback
            traceback.print_exc()
            # Возвращаем пустой список вместо исключения
            return []
    
    def get_cover_image_url(self, obj):
        """
        Возвращает полный URL заглавного изображения
        """
        try:
            # Проверяем наличие поля cover_image
            if not hasattr(obj, 'cover_image'):
                print(f'Service "{obj.name}" does not have cover_image attribute')
                return None
            
            try:
                cover_image = obj.cover_image
            except Exception as e:
                print(f'Error accessing cover_image for service "{obj.name}": {e}')
                return None
            
            if not cover_image:
                print(f'Service "{obj.name}" has cover_image but it is None/empty')
                return None
            
            print(f'Service "{obj.name}" has cover_image: {cover_image}')
            
            # Пытаемся получить URL изображения
            try:
                image_url = cover_image.url
                print(f'Service "{obj.name}" cover_image.url: {image_url}')
            except (ValueError, AttributeError) as e:
                print(f'Error getting cover_image.url for service "{obj.name}": {e}')
                import traceback
                traceback.print_exc()
                return None
            except Exception as e:
                print(f'Unexpected error getting cover_image.url for service "{obj.name}": {e}')
                import traceback
                traceback.print_exc()
                return None
            
            if not image_url:
                return None
            
            # Проверяем, существует ли файл (только для локальных файлов)
            try:
                if hasattr(cover_image, 'path'):
                    file_path = cover_image.path
                    if file_path and not os.path.exists(file_path):
                        print(f'Cover image file does not exist: {file_path}')
                        return None
            except (ValueError, AttributeError):
                # Если нет пути к файлу (например, файл хранится в S3), пропускаем проверку
                pass
            
            # Строим абсолютный URL
            request = self.context.get('request')
            if request:
                try:
                    url = request.build_absolute_uri(image_url)
                    # Заменяем внутренние Docker имена хостов на localhost для разработки
                    if '://backend:' in url:
                        url = url.replace('://backend:8000', '://localhost:8000')
                    elif '://backend/' in url:
                        url = url.replace('://backend/', '://localhost:8000/')
                    return url
                except Exception as e:
                    # Если не удалось построить абсолютный URL, возвращаем относительный
                    print(f'Error building absolute URI for cover image: {e}')
                    return image_url
            
            return image_url
        except Exception as e:
            # Обрабатываем любые ошибки при работе с изображением
            print(f'Error getting cover image URL for service "{obj.name}": {e}')
            import traceback
            traceback.print_exc()
            return None


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')


class EventSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Event
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def validate(self, data):
        # Если услуга не указана, требуется указать стоимость
        if not data.get('service') and not data.get('price'):
            raise serializers.ValidationError({
                'price': 'Если услуга не выбрана, необходимо указать стоимость события.'
            })
        return data
    
    def to_representation(self, instance):
        # Преобразуем snake_case в camelCase для фронтенда
        representation = super().to_representation(instance)
        
        # Преобразуем start_time в startTime
        if 'start_time' in representation and instance.start_time:
            representation['startTime'] = instance.start_time.strftime('%H:%M')
            representation.pop('start_time', None)
        
        # Нормализуем формат даты (YYYY-MM-DD)
        if 'date' in representation and instance.date:
            representation['date'] = instance.date.strftime('%Y-%m-%d')
        
        # Преобразуем service в serviceId
        if 'service' in representation:
            representation['serviceId'] = representation.pop('service')
        
        # Преобразуем max_participants в maxParticipants
        if 'max_participants' in representation:
            representation['maxParticipants'] = representation.pop('max_participants')
        
        # Преобразуем booked_slots в bookedSlots
        if 'booked_slots' in representation:
            representation['bookedSlots'] = representation.pop('booked_slots')
        
        # Преобразуем service_name в serviceName
        if 'service_name' in representation:
            representation['serviceName'] = representation.pop('service_name')
        
        return representation
    
    def to_internal_value(self, data):
        # Преобразуем camelCase в snake_case для Django
        data_copy = data.copy() if isinstance(data, dict) else data
        
        if isinstance(data_copy, dict):
            if 'startTime' in data_copy:
                data_copy['start_time'] = data_copy.pop('startTime')
            if 'serviceId' in data_copy:
                service_id = data_copy.pop('serviceId')
                # Если serviceId null или None, передаем service как None (для nullable поля)
                data_copy['service'] = service_id if service_id is not None else None
            if 'maxParticipants' in data_copy:
                data_copy['max_participants'] = data_copy.pop('maxParticipants')
            if 'bookedSlots' in data_copy:
                data_copy['booked_slots'] = data_copy.pop('bookedSlots')
        
        return super().to_internal_value(data_copy)


class BookingSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    member_name = serializers.CharField(source='member.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')

    def to_internal_value(self, data):
        """Преобразуем camelCase в snake_case для Django"""
        data_copy = dict(data) if isinstance(data, dict) else {}
        if 'customerId' in data_copy:
            data_copy['customer'] = data_copy.pop('customerId')
        if 'serviceId' in data_copy:
            data_copy['service'] = data_copy.pop('serviceId')
        if 'memberId' in data_copy:
            data_copy['member'] = data_copy.pop('memberId')
        if 'eventId' in data_copy:
            data_copy['event'] = data_copy.pop('eventId')
        if 'startTime' in data_copy:
            data_copy['start_time'] = data_copy.pop('startTime')
        if 'endTime' in data_copy:
            data_copy['end_time'] = data_copy.pop('endTime')
        return super().to_internal_value(data_copy)
    
    def to_representation(self, instance):
        # Преобразуем snake_case в camelCase для фронтенда
        representation = super().to_representation(instance)
        
        # Преобразуем start_time и end_time в startTime и endTime
        if 'start_time' in representation and instance.start_time:
            representation['startTime'] = instance.start_time.strftime('%H:%M')
            representation.pop('start_time', None)
        if 'end_time' in representation and instance.end_time:
            representation['endTime'] = instance.end_time.strftime('%H:%M')
            representation.pop('end_time', None)
        
        # Нормализуем формат даты (YYYY-MM-DD)
        if 'date' in representation and instance.date:
            representation['date'] = instance.date.strftime('%Y-%m-%d')
        
        # Преобразуем customer_name в customerName
        if 'customer_name' in representation:
            representation['customerName'] = representation.pop('customer_name')
        
        # Преобразуем service_name в serviceName
        if 'service_name' in representation:
            representation['serviceName'] = representation.pop('service_name')
        
        # Преобразуем member_name в memberName (если есть)
        if 'member_name' in representation:
            representation['memberName'] = representation.pop('member_name')
        
        # Преобразуем customer, service, member в customerId, serviceId, memberId
        if 'customer' in representation:
            representation['customerId'] = representation.pop('customer')
        if 'service' in representation:
            representation['serviceId'] = representation.pop('service')
        if 'member' in representation:
            representation['memberId'] = representation.pop('member')
        if 'event' in representation:
            representation['eventId'] = representation.pop('event')
        
        return representation


class WorkBreakSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkBreak
        fields = ['id', 'start_time', 'end_time']
        read_only_fields = ('id',)
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['startTime'] = representation.pop('start_time')
        representation['endTime'] = representation.pop('end_time')
        return representation
    
    def to_internal_value(self, data):
        # Преобразуем camelCase в snake_case для Django
        data_copy = dict(data) if isinstance(data, dict) else data
        if isinstance(data_copy, dict):
            if 'startTime' in data_copy:
                data_copy['start_time'] = data_copy.pop('startTime')
            if 'endTime' in data_copy:
                data_copy['end_time'] = data_copy.pop('endTime')
        return super().to_internal_value(data_copy)


class WorkScheduleSerializer(serializers.ModelSerializer):
    breaks = WorkBreakSerializer(many=True, required=False, allow_null=True)
    
    class Meta:
        model = WorkSchedule
        fields = ['id', 'date', 'type', 'start_time', 'end_time', 'breaks', 'created_at', 'updated_at']
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def to_representation(self, instance):
        # Преобразуем snake_case в camelCase для фронтенда
        representation = super().to_representation(instance)
        
        # Преобразуем start_time и end_time в startTime и endTime (без секунд)
        if 'start_time' in representation and instance.start_time:
            representation['startTime'] = instance.start_time.strftime('%H:%M')
            representation.pop('start_time', None)
        if 'end_time' in representation and instance.end_time:
            representation['endTime'] = instance.end_time.strftime('%H:%M')
            representation.pop('end_time', None)
        
        # Преобразуем breaks
        breaks_list = []
        for break_item in instance.breaks.all():
            breaks_list.append({
                'id': break_item.id,
                'startTime': break_item.start_time.strftime('%H:%M'),
                'endTime': break_item.end_time.strftime('%H:%M')
            })
        representation['breaks'] = breaks_list
        
        return representation
    
    def to_internal_value(self, data):
        # Создаем копию данных, чтобы не изменять оригинал
        data_copy = data.copy() if isinstance(data, dict) else data
        
        # Преобразуем camelCase в snake_case для Django
        if isinstance(data_copy, dict):
            if 'startTime' in data_copy:
                data_copy['start_time'] = data_copy.pop('startTime')
            if 'endTime' in data_copy:
                data_copy['end_time'] = data_copy.pop('endTime')
            
            # Обрабатываем breaks, если они есть
            if 'breaks' in data_copy and isinstance(data_copy['breaks'], list):
                breaks_list = []
                for break_item in data_copy['breaks']:
                    if isinstance(break_item, dict):
                        break_copy = break_item.copy()
                        if 'startTime' in break_copy:
                            break_copy['start_time'] = break_copy.pop('startTime')
                        if 'endTime' in break_copy:
                            break_copy['end_time'] = break_copy.pop('endTime')
                        breaks_list.append(break_copy)
                    else:
                        breaks_list.append(break_item)
                data_copy['breaks'] = breaks_list
        
        return super().to_internal_value(data_copy)
    
    def create(self, validated_data):
        breaks_data = validated_data.pop('breaks', [])
        
        # Убеждаемся, что breaks_data это список
        if breaks_data is None:
            breaks_data = []
        
        schedule = WorkSchedule.objects.create(**validated_data)
        
        if breaks_data and len(breaks_data) > 0:
            for break_data in breaks_data:
                # Обрабатываем как camelCase, так и snake_case
                start_time = break_data.get('start_time') or break_data.get('startTime')
                end_time = break_data.get('end_time') or break_data.get('endTime')
                
                if start_time and end_time:
                    WorkBreak.objects.create(
                        schedule=schedule,
                        start_time=start_time,
                        end_time=end_time
                    )
        
        return schedule
    
    def update(self, instance, validated_data):
        breaks_data = validated_data.pop('breaks', None)
        
        # Обновляем основные поля
        instance.date = validated_data.get('date', instance.date)
        instance.type = validated_data.get('type', instance.type)
        instance.start_time = validated_data.get('start_time', instance.start_time)
        instance.end_time = validated_data.get('end_time', instance.end_time)
        instance.save()
        
        # Обновляем перерывы
        if breaks_data is not None:
            # Удаляем старые перерывы
            instance.breaks.all().delete()
            # Создаем новые перерывы
            if breaks_data:
                for break_data in breaks_data:
                    # Обрабатываем как camelCase, так и snake_case
                    start_time = break_data.get('start_time') or break_data.get('startTime')
                    end_time = break_data.get('end_time') or break_data.get('endTime')
                    
                    if start_time and end_time:
                        WorkBreak.objects.create(
                            schedule=instance,
                            start_time=start_time,
                            end_time=end_time
                        )
        
        return instance


class ReviewSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'customer', 'customer_name', 'service', 'service_name', 'rating', 'comment', 'photos', 'reply', 'reply_author', 'created_at', 'updated_at']
        read_only_fields = ('user', 'created_at', 'updated_at')
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # Преобразуем service в serviceId
        if 'service' in representation:
            representation['serviceId'] = representation.pop('service')
        
        # Преобразуем customer в customerId
        if 'customer' in representation:
            representation['customerId'] = representation.pop('customer')
        
        # Преобразуем customer_name в customerName (camelCase для фронтенда)
        # Если customer_name пустое, пытаемся взять из связанного customer
        customer_name = representation.get('customer_name', '')
        if not customer_name and instance.customer:
            customer_name = instance.customer.name
        
        representation['customerName'] = customer_name
        if 'customer_name' in representation:
            representation.pop('customer_name')
        
        # Преобразуем reply_author в replyAuthor (camelCase для фронтенда)
        if 'reply_author' in representation:
            representation['replyAuthor'] = representation.pop('reply_author')
        
        # Преобразуем service_name в serviceName
        if 'service_name' in representation:
            representation['serviceName'] = representation.pop('service_name')
        
        return representation
