from django.shortcuts import render

def login_view(request):
    """
    Renders login page.
    """
    return render(request, 'auth/login.html')

def adminDashBoard(request):
    """
    Docstring for adminDashBoard
    
    :param request: Description
    """
    return render(request, 'adminDashBoard.html')
