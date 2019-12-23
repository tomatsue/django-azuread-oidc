from django.contrib import admin
from django.shortcuts import redirect  # 追加
from django.urls import include, path  # include 追加

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda req: redirect('accounts/', permanent=False)),  # 追加
    path('accounts/', include('accounts.urls')),  # 追加
]