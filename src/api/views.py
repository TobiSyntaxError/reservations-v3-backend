from django.http import JsonResponse

def status(request):
    return JsonResponse({"authors": ["Tobias", "Daniel"]})
    

def health(request):
    return JsonResponse({"live": True, "ready": True})
