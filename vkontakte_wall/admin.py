# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.text import truncate_words
from vkontakte_api.admin import VkontakteModelAdmin, GenericRelationListFilter
from models import Post, Comment

class WallOwnerListFilter(GenericRelationListFilter):
    title = u'Владелец стены'

    ct_field_name = 'wall_owner_content_type'
    id_field_name = 'wall_owner_id'
    field_name = 'wall_owner'

class PostListFilter(admin.SimpleListFilter):
    title = u'Сообщение'
    parameter_name = 'post'

    field_name = 'post'

    separator = '-'
    ct_field_name = 'wall_owner_content_type'
    id_field_name = 'wall_owner_id'
    parent_parameter_name = 'wall_owner'

    def lookups(self, request, model_admin):
        parent_value = request.REQUEST.get(self.parent_parameter_name)
        if parent_value:
            ct_value, id_value = parent_value.split(self.separator)
            return [(str(instance.post_id), truncate_words(instance.post.text, 5)) for instance in model_admin.model.objects.order_by().filter(**{self.ct_field_name: ct_value, self.id_field_name: id_value}).distinct(self.field_name)]

    def queryset(self, request, queryset):
        parent_value = request.REQUEST.get(self.parent_parameter_name)
        if parent_value and self.value():
            ct_value, id_value = parent_value.split(self.separator)
            return queryset.filter(**{self.ct_field_name: ct_value, self.id_field_name: id_value, self.field_name: self.value()})

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
    search_fields = ('text','copy_text','remote_id')
    exclude = ('like_users','repost_users',)
    inlines = [CommentInline]

class CommentAdmin(VkontakteModelAdmin):
    list_display = ('author','text','post','vk_link','date','likes')
    search_fields = ('text','remote_id')
    list_filter = (WallOwnerListFilter,PostListFilter,)

admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)