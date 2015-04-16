from django.http import HttpResponseServerError


def fake_error(request):
    raise Exception('FAKE ERROR')


def handler500(request):
    f = open('site_off.html')
    content = f.read()
    f.close()
    return HttpResponseServerError(content)

