from django.shortcuts import render
from unwrap.models import IMG
from django.http import StreamingHttpResponse  
def upload(request):
    return render(request, 'unwrap/upload.html')
def show(request):
    new_img = IMG(img=request.FILES.get('img'))
    new_img.save()
    content = {
        'aaa': new_img,
    }
    return render(request, 'unwrap/show.html', content)
def download(request):
    try:
        new_img = IMG(img=request.FILES.get('img'))
        new_img.save()
        response = StreamingHttpResponse(readFile(new_img.path))  
        response['Content-Type']='application/octet-stream'  
        response['Content-Disposition']='attachment;filename="unwrapped.jpg"'  
        return response
    except:
        return render(request, 'unwrap/404.html')

def readFile(filename,chunk_size=512):  
    with open(filename,'rb') as f:  
        while True:  
            c=f.read(chunk_size)  
            if c:  
                yield c  
            else:  
                break 