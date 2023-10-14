from django.urls import path


from . import views


app_name = "news"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),

    path("detail/<int:pk>/", views.DetailView.as_view(), name="detail"),
    path("<int:article_id>/vote/", views.vote, name="vote"),
]
