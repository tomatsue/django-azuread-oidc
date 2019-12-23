from django.urls import include, path

from . import views

urlpatterns = [
    path('', views.index),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('oidc/callback/', views.callback_view),
    path('graphcall/', views.graphcall_view, name='graphcall')
]
