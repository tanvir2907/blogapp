# blog/urls.py

from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('login/', user_login, name='login'),  # URL for user login
    path('signup/', user_signup, name='signup'),  # URL for user signup
    path('logout/', user_logout, name='logout'), # url for logout
    path('dashboard/', dashboard, name='dashboard'),
    path('addblog/', add_blog, name='add_blog'),
    path('blogs/', BlogListView.as_view(), name='blog_list'),
    path('blogs/<slug:slug>/', BlogDetailView.as_view(), name='blog_detail'),
    path('blog/<int:pk>/delete/', BlogDeleteView.as_view(), name='delete_blog'),
    path('<int:pk>/update/', update_blog, name='update_blog'),
    path('search_blog/', search_blog, name='search_blog'),
    path('blog/<int:blog_id>/share/', share_blog_email, name='share_blog_email'),
    path('send_email/', send_email, name='send_email'),

    # Add more URLs for other views as needed
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)