from django.urls import path
from  . import views 


urlpatterns=[
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'), 
    path('dashboard/', views.dashboard, name='dashboard'), 
    path('', views.dashboard, name='dashboard'), 
   
    
    path('forgotPassword/', views.forgotPassword, name='forgotPassword'),
    path('my_orders/', views.my_orders, name='my_orders'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    
    ]
