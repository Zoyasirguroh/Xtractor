from django.urls import path
from .views import *
from . import views
from .views import FilePathView
from django.urls import path
# from .views import upload_view
from .views import upload_file

from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    # path ('', index, name='index.html'),
    # path('', EHRpage, name="EHRpage.html"),
    path('Xtractor/Processing', FilePathView.as_view(), name='file-path'),
    path('Xtractor/Uploadfiles', Uploadfiles, name="dashboard.html"),
    # path('Xtractor/Upload_1/', upload_view, name='upload_view'),
    path('Xtractor/Upload/', upload_file, name='upload_file'),
    path('upload_file/', upload_file, name='upload_file'),


    # path('cardpage/', cardpage, name="cardpage.html"),
    # path('EHRMLpage/', EHRMLpage, name="EHRMLpage.html"),
    # path('Charts/', Charts, name="Charts")

]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

