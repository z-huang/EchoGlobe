from collections import defaultdict
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import UserSerializer, TransactionSerializer
from .models import Transaction


@login_required(login_url='/login')
def index(request):
    return render(request, 'index.html')


def login_page(request):
    return render(request, 'login.html')


def register_page(request):
    return render(request, 'register.html')


@api_view(['POST'])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return Response({'success': True, 'username': user.username})
    else:
        return Response({'success': False, 'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


@csrf_exempt
def logout_view(request):
    logout(request)
    return JsonResponse({'success': True})


@api_view(['POST'])
def register_view(request):
    serializer = UserSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response({"detail": "註冊成功！"}, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@login_required
def user_list(request):
    users = User.objects.all()
    user_data = [{"id": user.id, "username": user.username} for user in users]

    return JsonResponse({"users": user_data})


@api_view(['GET'])
@login_required
def transaction_list(request):
    user = request.user
    transactions = Transaction.objects.filter(
        creditor=user) | Transaction.objects.filter(debtor=user)
    transaction_data = []
    for transaction in transactions:
        transaction_data.append({
            'id': transaction.id,
            'creditor': transaction.creditor.username,
            'debtor': transaction.debtor.username,
            'amount': transaction.amount,
            'description': transaction.description,
            'created_at': transaction.created_at,
        })
    return Response(transaction_data)


@api_view(['GET'])
@login_required
def transaction_detail(request, pk):
    try:
        transaction = Transaction.objects.get(pk=pk)
    except Transaction.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = TransactionSerializer(transaction)
    return Response(serializer.data)


@api_view(['POST'])
@login_required
def transaction_create(request):
    if request.method == 'POST':
        serializer = TransactionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@login_required
def transaction_update(request, pk):
    try:
        transaction = Transaction.objects.get(pk=pk)
    except Transaction.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = TransactionSerializer(transaction, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@login_required
def debt_relation_get(request):
    transactions = Transaction.objects.all()

    net_balance = defaultdict(float)  # 正數是收錢的，負數是要付錢的

    for transaction in transactions:
        creditor = transaction.creditor.username
        debtor = transaction.debtor.username
        amount = float(transaction.amount)
        net_balance[creditor] += amount
        net_balance[debtor] -= amount

    # 排序債權人與債務人
    creditors = []
    debtors = []

    for user, balance in net_balance.items():
        if round(balance, 2) > 0:
            creditors.append([user, round(balance, 2)])
        elif round(balance, 2) < 0:
            debtors.append([user, round(balance, 2)])

    simplified_transactions = []

    i, j = 0, 0
    while i < len(debtors) and j < len(creditors):
        debtor, d_amt = debtors[i]
        creditor, c_amt = creditors[j]

        settlement = min(-d_amt, c_amt)
        simplified_transactions.append({
            "from": debtor,
            "to": creditor,
            "amount": round(settlement, 2)
        })

        debtors[i][1] += settlement
        creditors[j][1] -= settlement

        if round(debtors[i][1], 2) == 0:
            i += 1
        if round(creditors[j][1], 2) == 0:
            j += 1

    return Response(simplified_transactions, status=status.HTTP_200_OK)


@api_view(['GET'])
@login_required
def total_debt_view(request):
    transactions = Transaction.objects.all()
    net_balance = defaultdict(float)

    for transaction in transactions:
        creditor = transaction.creditor.username
        debtor = transaction.debtor.username
        amount = float(transaction.amount)
        net_balance[creditor] += amount
        net_balance[debtor] -= amount

    result = [
        {"username": username, "total_debt": round(balance, 2)}
        for username, balance in net_balance.items()
    ]

    return Response(result, status=status.HTTP_200_OK)
