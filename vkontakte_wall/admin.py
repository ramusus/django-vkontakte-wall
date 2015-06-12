# -*- coding: utf-8 -*-
from django.contrib import admin
from vkontakte_api.admin import VkontakteModelAdmin, GenericRelationListFilter
from vkontakte_comments.models import Comment
try: # Deprecated since version 1.7. Support for importing from this old location will be removed in Django 1.9.
    from django.contrib.contenttypes.generic import GenericTabularInline
except ImportError:
    from django.contrib.contenttypes.admin import GenericTabularInline

from .models import Post

try:
    from django.template.defaultfilters import truncatewords
except ImportError:
    from django.utils.text import truncate_words as truncatewords


class WallOwnerListFilter(GenericRelationListFilter):
    title = u'Владелец стены'

    ct_field_name = 'owner_content_type'
    id_field_name = 'owner_id'
    field_name = 'owner'


class PostListFilter(admin.SimpleListFilter):
    title = u'Сообщение'
    parameter_name = 'post'

    field_name = 'post'

    separator = '-'
    ct_field_name = 'owner_content_type'
    id_field_name = 'owner_id'
    parent_parameter_name = 'owner'

    def lookups(self, request, model_admin):
        parent_value = request.REQUEST.get(self.parent_parameter_name)
        if parent_value:
            ct_value, id_value = parent_value.split(self.separator)
            return [(str(instance.post_id), truncatewords(instance.post.text, 5)) for instance in model_admin.model.objects.order_by().filter(**{self.ct_field_name: ct_value, self.id_field_name: id_value}).distinct(self.field_name)]

    def queryset(self, request, queryset):
        parent_value = request.REQUEST.get(self.parent_parameter_name)
        if parent_value and self.value():
            ct_value, id_value = parent_value.split(self.separator)
            return queryset.filter(**{self.ct_field_name: ct_value, self.id_field_name: id_value, self.field_name: self.value()})


class CommentInline(GenericTabularInline):
    model = Comment
    ct_field = 'object_content_type'
    ct_fk_field = 'object_id'
    extra = 0
    can_delete = False
    fields = ('author', 'text', 'date', 'likes_count')
    readonly_fields = fields


class PostAdmin(VkontakteModelAdmin):
    list_display = ('owner', 'text', 'author', 'vk_link', 'date', 'comments_count', 'likes_count', 'reposts_count')
    list_display_links = ('text',)
    list_filter = (WallOwnerListFilter,)
    search_fields = ('text', 'copy_text', 'remote_id')
    exclude = ('likes_users', 'reposts_users',)
    inlines = [CommentInline]


class CommentAdmin(VkontakteModelAdmin):
    list_display = ('author', 'text', 'object', 'vk_link', 'date', 'likes_count')
    search_fields = ('text', 'remote_id')
    list_filter = (WallOwnerListFilter, PostListFilter,)


admin.site.register(Post, PostAdmin)
#admin.site.register(Comment, CommentAdmin)
