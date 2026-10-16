from django.urls import path
from . import views

urlpatterns = [
    path('', views.library_view, name='library'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('books/edit/<int:pk>/', views.edit_book_view, name='edit_book'),
    path('books/delete/<int:pk>/', views.delete_book_view, name='delete_book'),

    path('habits/', views.habits_view, name='habits'),
    path('habits/edit/<int:pk>/', views.edit_habit_view, name='edit_habit'),
    path('habits/delete/<int:pk>/', views.delete_habit_view, name='delete_habit'),
    path('habits/reset/<int:pk>/', views.reset_habit_view, name='reset_habit'),
    path('habits/toggle-pause/<int:pk>/', views.toggle_habit_pause, name='toggle_habit_pause'),
    path('habits/toggle-ajax/', views.toggle_habit_ajax, name='toggle_habit_ajax'),

    path('analytics/', views.analytics_view, name='analytics'),
    path('about/', views.about_view, name='about'),
]