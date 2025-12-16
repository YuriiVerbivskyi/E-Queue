import json
import os
import uuid
import datetime
import requests
from django.contrib.auth import login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.urls import reverse
from dotenv import load_dotenv
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from twilio.rest import Client

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from .models import (
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
    QueueEntrySerializer,
    NotificationSerializer,
    RoomSerializer,
    QueueEntryDetailSerializer,
)
from .utils import send_notification_email

load_dotenv()

CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
REDIRECT_URI = 'http://127.0.0.1:8000/oauth2callback/'

all_students = []


def get_user_role_name(user):
    if user.is_superuser:
        return "Admin"
    elif user.is_staff:
        return "Organizer"
    else:
        return "Guest"


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
    email = user.email if user.email else "Not specified"

    phone = user.phone_number
    if not phone:
        phone = "Not specified"

    role_name = get_user_role_name(user)

    return render(
        request,
        "profile.html",
        {
            "profile_username": user.username,
            "profile_email": email,
            "profile_role": role_name,
            "profile_phone": phone,
        },
    )


def queue_page(request):
    user = request.user
    if user.is_staff or user.is_superuser:
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
    can_manage = user.is_staff or user.is_superuser

    context = {
        "status": "admin" if can_manage else "student",
        "user_role": get_user_role_name(user),
    }

    if can_manage:
        context["auth"] = uuid.uuid4().hex
        request.session["ck"] = context["auth"]
        if user.is_superuser:
            context["rooms"] = Room.objects.filter(is_active=True)
        else:
            context["rooms"] = Room.objects.filter(teacher=user, is_active=True)
    else:
        context["available_rooms"] = Room.objects.filter(is_active=True).order_by('event_date')

    return render(request, "queues.html", context)


def google_calendar_auth(request):
    room_id = request.GET.get('room_id')
    if room_id:
        request.session['calendar_room_id'] = room_id

    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        request.session['state'] = state
        return HttpResponseRedirect(authorization_url)
    except FileNotFoundError:
        return HttpResponse("File client_secret.json not found", status=500)


def oauth2callback(request):
    state = request.session.get('state')
    if not state:
        return redirect('queues')

    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            state=state,
            redirect_uri=REDIRECT_URI
        )

        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials

        request.session['google_credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }

        room_id = request.session.get('calendar_room_id')
        if room_id:
            return add_event_to_calendar(request, room_id)

        return redirect('queues')
    except Exception as e:
        return HttpResponse(f"Auth error: {str(e)}", status=500)


def add_event_to_calendar(request, room_id):
    creds_data = request.session.get('google_credentials')
    if not creds_data:
        return redirect('google_auth')

    creds = Credentials(**creds_data)
    service = build('calendar', 'v3', credentials=creds)

    try:
        room = Room.objects.get(id=room_id)

        start_time = room.event_date if room.event_date else datetime.datetime.utcnow() + datetime.timedelta(days=1)
        end_time = start_time + datetime.timedelta(hours=1)

        event = {
            'summary': f'E-Queue: {room.name}',
            'location': 'Online / Location',
            'description': f'Event: {room.name}. Code: {room.id}',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'Europe/Kyiv',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'Europe/Kyiv',
            },
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        if 'calendar_room_id' in request.session:
            del request.session['calendar_room_id']

        return render(request, "calendar_success.html", {"link": event.get('htmlLink')})

    except Exception as e:
        return JsonResponse({"ok": False, "message": str(e)}, status=500)


@csrf_exempt
@login_required(login_url="/login/")
def create_room(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "message": "Method not allowed"}, status=405)

    user = request.user
    if not (user.is_staff or user.is_superuser):
        return JsonResponse({"ok": False, "message": "Forbidden"}, status=403)

    try:
        body = json.loads(request.body.decode("utf-8"))
        name = body.get("name", "").strip()
        description = body.get("description", "").strip()
        date_str = body.get("event_date", "").strip()

        if not name:
            return JsonResponse({"ok": False, "message": "Name is required"}, status=400)

        event_date = None
        if date_str:
            try:
                event_date = datetime.datetime.fromisoformat(date_str)
            except ValueError:
                event_date = None

        room = Room.objects.create(
            name=name,
            teacher=user,
            description=description,
            event_date=event_date
        )
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
            return JsonResponse({"ok": False, "message": "Room not found"}, status=404)

        existing = QueueEntry.objects.filter(
            user=user, room=room, status__in=['waiting', 'ready']
        ).first()
        if existing:
            return JsonResponse({"ok": False, "message": "Already joined"}, status=400)

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
            "position": position,
            "event_date": room.event_date.strftime("%Y-%m-%d %H:%M") if room.event_date else "TBA"
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

    if room.teacher != request.user and not request.user.is_superuser:
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

    if room.teacher != user and not user.is_superuser:
        return JsonResponse({"ok": False, "message": "Not authorized"}, status=403)

    next_entry = room.entries.filter(status='waiting').order_by('created_at').first()

    if not next_entry:
        return JsonResponse({"ok": False, "message": "Queue is empty"}, status=400)

    current_user = next_entry.user
    phone = getattr(current_user, 'phone_number', "+380961094823")

    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

        if account_sid and auth_token and twilio_number:
            client = Client(account_sid, auth_token)
            client.messages.create(
                body=f"E-Queue: {room.name} - You are next!",
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


@csrf_exempt
@login_required(login_url="/login/")
def next_student(request):
    if request.method != "POST":
        return JsonResponse({"ok": "Method not allowed"}, status=405)
    return JsonResponse({'ok': "Use next_student_in_room instead"}, status=400)


class QueueListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        rooms = Room.objects.all()
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = RoomSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(teacher=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QueueDetailView(APIView):
    permission_classes = [IsQueueOwnerOrAdmin]

    def get_object(self, pk):
        return get_object_or_404(Room, pk=pk)

    def get(self, request, pk):
        room = self.get_object(pk)
        serializer = RoomSerializer(room)
        return Response(serializer.data)

    def put(self, request, pk):
        room = self.get_object(pk)
        self.check_object_permissions(request, room)
        serializer = RoomSerializer(room, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        room = self.get_object(pk)
        self.check_object_permissions(request, room)
        room.delete()
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
            position = QueueEntry.objects.filter(room=entry.room).count()
            entry.position = position
            entry.save()
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
            return Response(
                {"message": "Success registration", "user_id": user.id, "authenticated": True},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    role = get_user_role_name(user)
    return Response({
        "username": user.username,
        "email": user.email,
        "role": role,
        "phone": getattr(user, "phone_number", "")
    })


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


class MonoData(APIView):
    def get(self, request, data):
        if data == "trans":
            last_trns = get_last_transs()
            return JsonResponse(last_trns, safe=False)
        else:
            return redirect("/")


@login_required
def delete_queue(request, queue_id):
    queue = get_object_or_404(Room, id=queue_id)
    if request.user == queue.teacher or request.user.is_superuser:
        queue.delete()
    return redirect('queues')