# Generated by Django 4.2.6 on 2023-10-14 18:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0004_article_valid_decision_nlp_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="article",
            name="author",
            field=models.CharField(max_length=64),
        ),
        migrations.AlterField(
            model_name="article",
            name="pub_date",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="article",
            name="source_site",
            field=models.CharField(default="UNKNOWN", max_length=64),
        ),
        migrations.AlterField(
            model_name="article",
            name="title",
            field=models.CharField(max_length=256),
        ),
        migrations.AlterField(
            model_name="article",
            name="url_from",
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]