from django.urls import path


from . import views


app_name = "news"
urlpatterns = [
    path("", views.scrape_articles, name="scrape_articles"),
    path("browse/", views.browse_articles, name="browse"),


    path("detail/<int:pk>/", views.DetailView.as_view(), name="detail"),
    path('check_url/', views.check_url, name='check_url'),
    
    path('load_more_articles/', views.load_more_articles, name='load_more_articles'),

    
]
