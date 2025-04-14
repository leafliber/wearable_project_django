# videostream/views.py
from django.shortcuts import render
from .model_interface import get_classifier
import os
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def index_view(request):
    """Index page with links to all available views"""
    return render(request, 'index.html')

def video_view(request):
    """View for the basic video stream page"""
    return render(request, 'video.html')

def surgical_workflow_view(request):
    """View for the surgical workflow visualization page"""
    model = get_classifier()
    context = {
        'classes': model.CLASSES
    }
    return render(request, 'surgical_workflow_visualization.html', context)

def model_stats_view(request):
    """View for model statistics and performance metrics"""
    model = get_classifier()
    
    # Get model performance statistics
    context = {
        'frames_processed': model.frames_processed,
        'avg_inference_time': round(model.avg_inference_time * 1000, 2) if model.frames_processed > 0 else 0,
        'last_inference_time': round(model.last_inference_time * 1000, 2),
        'model_loaded': model.model is not None,
        'classes': model.CLASSES
    }
    
    return render(request, 'model_stats.html', context)