from django.http import HttpResponse
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
from .permissions import IsQueueOwnerOrAdmin, IsAuthenticatedOrReadOnly
from .models import Queue, QueueEntry



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
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token

            return Response({
                'access_token': str(access_token),
                'refresh_token': str(refresh),
                'username': user.username
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
