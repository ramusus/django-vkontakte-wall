# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.translation import ugettext as _
from vkontakte_api.admin import VkontakteModelAdmin
from models import Post, Comment

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    can_delete = False
    fields = ('author','text','date','likes')
    readonly_fields = fields

class PostAdmin(VkontakteModelAdmin):
    list_display = ('wall_owner','text','author','vk_link','date','comments','likes','reposts')
    list_display_links = ('text',)
#    list_filter = ('wall_owner',)
    search_fields = ('text','copy_text')
    exclude = ('like_users','repost_users',)
    inlines = [CommentInline]

class CommentAdmin(VkontakteModelAdmin):
    list_display = ('author','post','vk_link','date','likes')

admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)