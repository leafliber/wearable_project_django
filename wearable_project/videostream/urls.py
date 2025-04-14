# videostream/urls.py（应用路由）
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),  # Index page
    path('ui/', views.surgical_workflow_view, name='surgical_workflow'),  # Surgical workflow visualization
    path('video/', views.video_view, name='video'),  # Simple video view
    path('stats/', views.model_stats_view, name='model_stats'),  # Model statistics
]