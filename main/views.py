from django.http import HttpResponse, JsonResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import CustomUserSerializer, LoginSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.shortcuts import render
from .serializers import CustomUserSerializer, QueueSerializer, QueueEntrySerializer
from .permissions import IsQueueOwnerOrAdmin, IsAuthenticatedOrReadOnly, IsTeacherOrAdmin
from .models import Queue, QueueEntry
import uuid
import json
from twilio.rest import Client
from django.contrib.auth import get_user_model
from django.contrib.auth import login


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
        return Queue.objects.get(pk=pk)

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
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QueueEntryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return QueueEntry.objects.get(pk=pk)

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


class Register(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
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
            
            # логінимо через сесію
            login(request, user)  

            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            return Response({
                'access_token': str(access_token),
                'refresh_token': str(refresh),
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
    user.is_staff
    user.is_superuser

    permission_classes = [IsAuthenticatedOrReadOnly]
    if user.is_staff == True or user.is_superuser == True:
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
        cntxt = {
            "status": current
        }

    request.session["ck"] = ck


    User = get_user_model()
    for u in User.objects.all():
        if u.is_staff == False:
            if u.is_superuser == False:
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


    account_sid = ''
    auth_token = ''
    client = Client(account_sid, auth_token)
    message = client.messages.create(
      messaging_service_sid='',
      body='u are next',
      to='phoneNum'
    )

