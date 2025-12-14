import json
import os
import uuid
import requests
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from twilio.rest import Client
from .models import (
    Queue,
    QueueEntry,
    Notification,
    CustomUser,
    Room,
)
from .permissions import (
    IsQueueOwnerOrAdmin,
    IsAuthenticatedOrReadOnly,
    IsTeacherOrAdmin,
)
from .serializers import (
    CustomUserSerializer,
    LoginSerializer,
    QueueSerializer,
    QueueEntrySerializer,
    NotificationSerializer,
    RoomSerializer,
    QueueEntryDetailSerializer,
)
from .utils import send_notification_email

load_dotenv()

all_students = []


def logout_view(request):
    logout(request)
    return redirect("/")


def login_page(request):
    return render(request, "login.html")


def register_user(request):
    return render(request, "register.html")


def home(request):
    return render(request, "index.html")


@login_required(login_url="/login/")
def user_profile_page(request):
    user = request.user
    email = user.email if user.email else "Не вказано"
    phone = getattr(user, 'phone_number', '')

    return render(
        request,
        "profile.html",
        {
            "profile_username": user.username,
            "profile_email": email,
            "profile_role": getattr(user, "role", "student"),
            "profile_phone": phone,
        },
    )


def queue_page(request):
    user = request.user
    if user.is_staff or user.is_superuser or getattr(user, "role", "") == "admin":
        status_type = "admin"
        ck = uuid.uuid4().hex
        context = {
            "status": status_type,
            "auth": ck,
            "num": 0,
        }
        request.session["ck"] = ck
    else:
        status_type = "student"
        context = {"status": status_type}
    return render(request, "queue.html", context)


@login_required(login_url="/login/")
def queues(request):
    user = request.user
    is_teacher = user.is_staff or user.is_superuser or getattr(user, "role", "") in ["admin", "teacher"]

    context = {
        "status": "admin" if is_teacher else "student",
        "user_role": getattr(user, "role", "student"),
    }

    if is_teacher:
        context["auth"] = uuid.uuid4().hex
        request.session["ck"] = context["auth"]
        context["rooms"] = Room.objects.filter(teacher=user, is_active=True)
    else:
        context["available_rooms"] = Room.objects.filter(is_active=True)

    return render(request, "queues.html", context)


@csrf_exempt
@login_required(login_url="/login/")
def create_room(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "message": "Method not allowed"}, status=405)

    user = request.user
    if not (user.is_staff or user.is_superuser or getattr(user, "role", "") in ["teacher", "admin"]):
        return JsonResponse({"ok": False, "message": "Forbidden"}, status=403)

    try:
        body = json.loads(request.body.decode("utf-8"))
        name = body.get("name", "").strip()

        if not name:
            return JsonResponse({"ok": False, "message": "Назва кімнати обов'язкова"}, status=400)

        room = Room.objects.create(name=name, teacher=user)
        return JsonResponse({
            "ok": True,
            "id": room.id,
            "name": room.name
        }, status=201)
    except Exception as e:
        return JsonResponse({"ok": False, "message": str(e)}, status=500)


@csrf_exempt
@login_required(login_url="/login/")
def join_room(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "message": "Method not allowed"}, status=405)

    user = request.user

    try:
        body = json.loads(request.body.decode("utf-8"))
        room_id = body.get("room_id", "").strip()

        if not room_id:
            return JsonResponse({"ok": False, "message": "room_id required"}, status=400)

        try:
            room = Room.objects.get(id=room_id, is_active=True)
        except Room.DoesNotExist:
            return JsonResponse({"ok": False, "message": "Кімната не знайдена"}, status=404)

        existing = QueueEntry.objects.filter(
            user=user, room=room, status__in=['waiting', 'ready']
        ).first()
        if existing:
            return JsonResponse({"ok": False, "message": "Ви вже в цій черзі"}, status=400)

        position = QueueEntry.objects.filter(
            room=room, status__in=['waiting', 'ready']
        ).count() + 1

        entry = QueueEntry.objects.create(
            user=user,
            room=room,
            position=position,
            status='waiting'
        )

        return JsonResponse({
            "ok": True,
            "room_id": room.id,
            "room_name": room.name,
            "position": position
        }, status=201)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "message": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"ok": False, "message": str(e)}, status=500)


@csrf_exempt
@login_required(login_url="/login/")
def get_room_entries(request):
    if request.method != "GET":
        return JsonResponse({"ok": False}, status=405)

    room_id = request.GET.get("room_id")

    if not room_id:
        return JsonResponse({"ok": False, "message": "room_id required"}, status=400)

    try:
        room = Room.objects.get(id=room_id)
    except Room.DoesNotExist:
        return JsonResponse({"ok": False, "message": "Room not found"}, status=404)

    if room.teacher != request.user:
        return JsonResponse({"ok": False, "message": "Not authorized"}, status=403)

    entries = room.entries.filter(status__in=['waiting', 'ready']).order_by('created_at')
    serializer = QueueEntryDetailSerializer(entries, many=True)

    return JsonResponse(serializer.data, safe=False)


@csrf_exempt
@login_required(login_url="/login/")
def next_student_in_room(request):
    if request.method != "POST":
        return JsonResponse({"ok": False}, status=405)

    user = request.user

    try:
        body = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"ok": False}, status=400)

    room_id = body.get("room_id")

    if not room_id:
        return JsonResponse({"ok": False, "message": "room_id required"}, status=400)

    try:
        room = Room.objects.get(id=room_id)
    except Room.DoesNotExist:
        return JsonResponse({"ok": False, "message": "Room not found"}, status=404)

    if room.teacher != user:
        return JsonResponse({"ok": False, "message": "Not authorized"}, status=403)

    next_entry = room.entries.filter(status='waiting').order_by('created_at').first()

    if not next_entry:
        return JsonResponse({"ok": False, "message": "No more students"}, status=400)

    current_user = next_entry.user
    phone = getattr(current_user, 'phone_number', "+380961094823")

    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

        if account_sid and auth_token and twilio_number:
            client = Client(account_sid, auth_token)
            client.messages.create(
                body=f"E-Queue: {room.name} - Ти наступний!",
                from_=twilio_number,
                to=phone,
            )
    except Exception as e:
        print(f"Twilio Error: {e}")

    next_entry.status = 'ready'
    next_entry.save()

    remaining = room.entries.filter(status='waiting').order_by('created_at')
    for idx, entry in enumerate(remaining, 1):
        entry.position = idx
        entry.save()

    return JsonResponse({
        "ok": True,
        "current_student": f"{current_user.first_name or current_user.username} {current_user.last_name or ''}".strip()
    }, status=200)


@login_required(login_url="/login/")
def next_student(request):
    body = json.loads(request.body)

    if request.session.get("ck") == body.get("ck"):
        if not all_students:
            return JsonResponse({'ok': "No more students"}, status=400)
        current = all_students.pop()

        try:
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

            if account_sid and auth_token and twilio_number:
                client = Client(account_sid, auth_token)
                message = client.messages.create(
                    body='u are next',
                    from_=twilio_number,
                    to='+380961094823'
                )
                print(message.sid)
        except Exception as e:
            print(f"Twilio Error: {e}")

        return JsonResponse({'ok': current}, status=200)
    else:
        return JsonResponse({'ok': "False"}, status=400)


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
                    message = (
                        f"Вітаю {request.user.first_name or request.user.username}!\n\n"
                        f"{entry.queue.name}\n\nБудь готовим, орієнтовний час 2-3хв\n\nНомер: {position}"
                    )
                    notification_type = "ready"
                else:
                    subject = "Запис у чергу успішний"
                    message = (
                        f"Вітаю {request.user.first_name or request.user.username}!\n\n"
                        f"Ти записався(лась) у чергу: {entry.queue.name}\n\n"
                        f"Твій номер у черзі: {position}\n\nОчікуй свою чергу."
                    )
                    notification_type = "queue_joined"
                send_notification_email(request.user, subject, message, notification_type)
            except Exception as e:
                print(f"Email error: {e}")
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return Response({"status": "marked as read"}, status=status.HTTP_200_OK)


class Register(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            login(request, user)
            try:
                send_notification_email(
                    user,
                    "Реєстрація успішна",
                    (
                        f"Вітаю {user.first_name or user.username}!\n\n"
                        f"Welcome to E-Queue!\n\nТвій аккаунт успішно створений.\n\n"
                        f"Користувач: {user.username}\nПошта: {user.email}"
                    ),
                    "registration",
                )
            except Exception as e:
                print(f"Email error: {e}")
            return Response(
                {"message": "Success registration", "user_id": user.id, "authenticated": True},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    return Response({
        "username": user.username,
        "email": user.email,
        "role": getattr(request.user, 'role', 'student'),
        "phone": getattr(user, "phone_number", "")
    })


def login_page(request):
    return render(request, "login.html")


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']

            login(request, user)

            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            return Response(
                {
                    "access": str(access_token),
                    "refresh": str(refresh),
                    "username": user.username,
                    "authenticated": True,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def get_last_transs():
    headers = {
        "accept": "application/json",
        "x-token": "usqbA76ff6U0Fi6Z_QL3t2Xmh42lYCOUQ9h9v2PW51nM",
    }
    account_id = "WEzuUgHoGQVlmHaHagiU0w"
    start = 1759622400
    end = 1762214400
    url = f"https://api.monobank.ua/personal/statement/{account_id}/{start}/{end}"
    try:
        r = requests.get(url, headers=headers)
        ans = r.json()
        last_transs = []
        for i in ans:
            last_transs.append({i["description"]: i["amount"]})
        return last_transs
    except Exception as e:
        return str(e)


class MonoData(APIView):
    def get(self, request, data):
        if data == "trans":
            last_trns = get_last_transs()
            return JsonResponse(last_trns, safe=False)
        elif data == "balance":
            return JsonResponse({"status": "balance logic here"})
        else:
            return redirect("/")


@login_required
def delete_queue(request, queue_id):
    queue = get_object_or_404(Room, id=queue_id)
    if request.user == queue.teacher or request.user.is_superuser:
        queue.delete()

    return redirect('queues')