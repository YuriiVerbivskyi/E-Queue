from django.contrib.sites import requests
from django.http import HttpResponse, JsonResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from django.shortcuts import render, redirect, get_object_or_404
from .serializers import (
    CustomUserSerializer,
    LoginSerializer,
    QueueSerializer,
    QueueEntrySerializer,
    NotificationSerializer
)
from .permissions import IsQueueOwnerOrAdmin, IsAuthenticatedOrReadOnly
from .models import Queue, QueueEntry, Notification, CustomUser
from .utils import send_notification_email

import uuid
import json
from django.contrib.auth import get_user_model, login

all_students = []

def register_user(request):
    return render(request, 'register.html')

def home(request):
    return render(request, 'index.html')

def user_profile_page(request):
    return render(request, 'profile.html')

class QueueListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    def get(self, request):
        queues = Queue.objects.all()
        serializer = QueueSerializer(queues, many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = QueueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QueueDetailView(APIView):
    permission_classes = [IsQueueOwnerOrAdmin]
    def get_object(self, pk):
        return get_object_or_404(Queue, pk=pk)
    def get(self, request, pk):
        queue = self.get_object(pk)
        serializer = QueueSerializer(queue)
        return Response(serializer.data)
    def put(self, request, pk):
        queue = self.get_object(pk)
        self.check_object_permissions(request, queue)
        serializer = QueueSerializer(queue, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk):
        queue = self.get_object(pk)
        self.check_object_permissions(request, queue)
        queue.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class QueueEntryListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        entries = QueueEntry.objects.all()
        serializer = QueueEntrySerializer(entries, many=True)
        return Response(serializer.data)
    def post(self, request):
        serializer = QueueEntrySerializer(data=request.data)
        if serializer.is_valid():
            entry = serializer.save(user=request.user)
            position = QueueEntry.objects.filter(queue=entry.queue).count()
            entry.position = position
            entry.save()
            try:
                if position == 1:
                    subject = "Ти наступний до здачі завдання!"
                    message = f"Вітаю {request.user.first_name or request.user.username}!\n\n{entry.queue.name}\n\nБудь готовим, орієнтовний час 2-3хв\n\nНомер: {position}"
                    notification_type = 'ready'
                else:
                    subject = "Запис у чергу успішний"
                    message = f"Вітаю {request.user.first_name or request.user.username}!\n\nТи записався(лась) у чергу: {entry.queue.name}\n\nТвій номер у черзі: {position}\n\nОчікуй свою чергу."
                    notification_type = 'queue_joined'
                send_notification_email(request.user, subject, message, notification_type)
            except Exception as e:
                print(f"Помилка відправки email при записі в чергу: {e}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QueueEntryDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get_object(self, pk):
        return get_object_or_404(QueueEntry, pk=pk)
    def get(self, request, pk):
        entry = self.get_object(pk)
        serializer = QueueEntrySerializer(entry)
        return Response(serializer.data)
    def put(self, request, pk):
        entry = self.get_object(pk)
        serializer = QueueEntrySerializer(entry, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def delete(self, request, pk):
        entry = self.get_object(pk)
        entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return Response({'status': 'marked as read'}, status=status.HTTP_200_OK)

class Register(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            try:
                send_notification_email(
                    user,
                    "Реєстрація успішна",
                    f"Вітаю {user.first_name or user.username}!\n\nWelcome to E-Queue!\n\nТвій аккаунт успішно створений.\n\nКористувач: {user.username}\nПошта: {user.email}",
                    'registration'
                )
            except Exception as e:
                print(f"Помилка відправки email при реєстрації: {e}")
            return Response(
                {"message": "Success registration", "user_id": user.id},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    return Response({
        "username": user.username,
        "email": user.email,
        "role": getattr(request.user, 'role', 'student')
    })

def login_page(request):
    return render(request, 'login.html')

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            return Response({
                'access': str(access_token),
                'refresh': str(refresh),
                'username': user.username
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def get_last_transs():
    headers = {
        "accept": "application/json",
        "x-token": "usqbA76ff6U0Fi6Z_QL3t2Xmh42lYCOUQ9h9v2PW51nM"
    }
    account_id = "WEzuUgHoGQVlmHaHagiU0w"
    start = 1759622400
    end = 1762214400
    url = f"https://api.monobank.ua/personal/statement/{account_id}/{start}/{end}"
    r = requests.get(url, headers=headers)
    ans = r.json()
    last_transs = []
    try:
        for i in ans:
            last_transs.append({i["description"]: i["amount"]})
        return last_transs
    except Exception as e:
        return e

class MonoData(APIView):
    def get(self, requests, data):
        if data == "trans":
            print("gettting last transs..")
            last_trns = get_last_transs()
            print(last_trns)
        elif data == "balance":
            print("current balance")
        else:
            print("doesn't exist")
            return redirect("/")
        return JsonResponse({"status": "ok"})

def queues(request):
    user = request.user
    permission_classes = [IsAuthenticatedOrReadOnly]
    if user.is_staff or user.is_superuser:
        current = "admin"
    else:
        current = "student"
    current = "admin"
    if current == "admin":
        ck = uuid.uuid4().hex
        cntxt = {
            "status": current,
            "auth": ck,
            "num": 0,
        }
    else:
        cntxt = {"status": current}
    request.session["ck"] = ck
    User = get_user_model()
    for u in User.objects.all():
        if not u.is_staff and not u.is_superuser:
            all_students.append(u.username)
    return render(request, "queues.html", cntxt)

def next_student(request):
    body = json.loads(request.body)
    if request.session.get("ck") == body.get("ck"):
        if not all_students:
            return JsonResponse({'ok': "No more students"}, status=400)
        current = all_students.pop()
        print(current)
        return JsonResponse({'ok': current}, status=200)
    else:
        return JsonResponse({'ok': "False"}, status=400)