from vkontakte_users.factories import UserFactory
from vkontakte_groups.factories import GroupFactory
from models import Post, Comment
from datetime import datetime
import factory
import random

class PostFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Post

    date = datetime.now()

    wall_owner = factory.SubFactory(UserFactory)
    author = factory.SubFactory(UserFactory)
    remote_id = factory.LazyAttributeSequence(lambda o, n: '%s_%s' % (o.wall_owner.remote_id, n))

class GroupPostFactory(PostFactory):
    wall_owner = factory.SubFactory(GroupFactory)
    remote_id = factory.LazyAttributeSequence(lambda o, n: '-%s_%s' % (o.wall_owner.remote_id, n))

class CommentFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Comment

    date = datetime.now()

    post = factory.SubFactory(PostFactory)
    author = factory.SubFactory(UserFactory)
    remote_id = factory.LazyAttributeSequence(lambda o, n: '%s_%s' % (o.post.remote_id, n))