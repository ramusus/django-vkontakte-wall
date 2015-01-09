# -*- coding: utf-8 -*-
from django.utils import timezone
import factory
from vkontakte_api.factories import DjangoModelNoCommitFactory
from vkontakte_groups.factories import GroupFactory
from vkontakte_users.factories import UserFactory

from .models import Post


class PostFactory(DjangoModelNoCommitFactory):

    date = factory.LazyAttribute(lambda o: timezone.now())

    owner = factory.SubFactory(UserFactory)
    author = factory.SubFactory(UserFactory)
    remote_id = factory.LazyAttributeSequence(lambda o, n: '%s_%s' % (o.owner.remote_id, n))

    class Meta:
        model = Post


class GroupPostFactory(PostFactory):
    owner = factory.SubFactory(GroupFactory)
    remote_id = factory.LazyAttributeSequence(lambda o, n: '-%s_%s' % (o.owner.remote_id, n))
