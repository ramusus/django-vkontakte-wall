# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from vkontakte_api.admin import VkontakteModelAdmin
from models import Post, Comment

class WallOwnerListFilter(SimpleListFilter):
    title = 'Владелец записи'
    parameter_name = 'owner'

    def lookups(self, request, model_admin):
        return [('%s-%s' % (post.wall_owner_content_type.id, post.wall_owner_id), post.wall_owner.name) for post in Post.objects.order_by().distinct('wall_owner_content_type','wall_owner_id')]

    def queryset(self, request, queryset):
        if self.value() and '-' in self.value():
            content_type, id = self.value().split('-')
            return queryset.filter(wall_owner_content_type=content_type, wall_owner_id=id)

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

admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)