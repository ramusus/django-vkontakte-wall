# -*- coding: utf-8 -*-
from django.contrib import admin
from vkontakte_api.admin import VkontakteModelAdmin, GenericRelationListFilter
from models import Post, Comment

class WallOwnerListFilter(GenericRelationListFilter):
    title = u'Владелец стены'
    parameter_name = 'owner'

    ct_field_name = 'wall_owner_content_type'
    id_field_name = 'wall_owner_id'
    field_name = 'wall_owner'

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    can_delete = False
    fields = ('author','text','date','likes')
    readonly_fields = fields

class PostAdmin(VkontakteModelAdmin):
    list_display = ('wall_owner','text','author','vk_link','date','comments','likes','reposts')
    list_display_links = ('text',)
    list_filter = (WallOwnerListFilter,)
    search_fields = ('text','copy_text')
    exclude = ('like_users','repost_users',)
    inlines = [CommentInline]

class CommentAdmin(VkontakteModelAdmin):
    list_display = ('author','text','post','vk_link','date','likes')
    search_fields = ('text',)
    list_filter = (WallOwnerListFilter,)

admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)