from django.shortcuts import render

# Create your views here.


def chat(request):
    print("chat triggered")
    if not request.session.session_key:
        request.session.create()

    return render(request, "chat.html")
