from django.contrib import admin
from .models import Post, Author
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display= ['title', 'slug', 'author', 'publish', 'status']
    list_filter= ['status', 'created', 'publish', 'author']
    search_fields= ['title', 'body']
    prepopulated_fields= {'slug': ('title',)}
    raw_id_fields= ['author']
    date_hierarchy= 'publish'
    ordering = ['status', 'publish']

@admin.register(CustomUser)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ['id', 'first_name', 'last_name', 'email', 'is_active', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    list_filter = ['is_active', 'is_staff']

    




