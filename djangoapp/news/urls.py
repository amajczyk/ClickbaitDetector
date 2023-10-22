from django.urls import path


from . import views


app_name = "news"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("browse/", views.BrowseView.as_view(), name="browse"),


    path("detail/<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:article_id>/vote/", views.vote, name="vote"),
]
