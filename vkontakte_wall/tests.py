# -*- coding: utf-8 -*-
from datetime import datetime, tzinfo
import time

from django.test import TestCase
from django.utils import timezone
import mock
import simplejson as json
from vkontakte_comments.factories import CommentFactory, Comment
from vkontakte_users.factories import User
from vkontakte_users.tests import user_fetch_mock

from .factories import PostFactory, UserFactory, GroupFactory, Post

USER_ID = 5223304
POST_ID = '5223304_130'

GROUP_ID = 16297716
GROUP_SCREEN_NAME = 'cocacola'
GROUP_POST_ID = '-16297716_126261'
GROUP_COMMENT_ID = '-16297716_126262'
GROUP_POST_WITH_MANY_REPOSTS_ID = '-16297716_263109'

OPEN_WALL_GROUP_ID = 26604743
OPEN_WALL_GROUP_SCREEN_NAME = 'club26604743'

GROUP_CRUD_ID = 59154616
POST_CRUD_ID = '-59154616_366'
USER_AUTHOR_ID = 201164356

GROUP2_ID = 10362317
GROUP2_POST_WITH_MANY_LIKES_ID = '-10362317_236186'


class VkontakteWallTest(TestCase):

    def setUp(self):
        self.objects_to_delete = []

    def tearDown(self):
        for object in self.objects_to_delete:
            object.delete(commit_remote=True)

    def test_fetch_posts(self, *args, **kwargs):

        self.assertTrue(Post.objects.count() == 0)

        posts = Post.remote.fetch(ids=[POST_ID, GROUP_POST_ID])
        self.assertEqual(posts.count(), Post.objects.count())
        self.assertEqual(posts.count(), 2)

    def fetch_post_comments_recursive_calls_ammount_side_effect(*args, **kwargs):
        comments_count = 100 if kwargs.get('offset', 0) == 0 else 6
        comments = [CommentFactory() for i in range(comments_count)]
        return Comment.objects.filter(pk__in=[comment.pk for comment in comments])

    @mock.patch('vkontakte_comments.models.Comment.remote.fetch', side_effect=fetch_post_comments_recursive_calls_ammount_side_effect)
    def test_fetch_post_comments_recursive_calls_ammount(self, fetch_method, *args, **kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id=GROUP_POST_ID, owner=group)

        comments = post.fetch_comments(sort='desc', all=True)

        self.assertEqual(comments.count(), 106)
        self.assertEqual(fetch_method.called, True)
        self.assertEqual(fetch_method.call_count, 2)
        self.assertTrue('offset' not in fetch_method.call_args_list[0][1])
        self.assertEqual(fetch_method.call_args_list[1][1]['offset'], 100)

    def fetch_post_reposts_recursive_calls_ammount_side_effect(*args, **kwargs):
        if kwargs['offset'] == 0:
            count = 100
        elif kwargs['offset'] == 100:
            count = 6
        else:
            count = 0
        return {'items': [{'from_id': UserFactory().pk, 'date': time.time()} for i in range(count)]}

    @mock.patch('vkontakte_wall.mixins.api_call', side_effect=fetch_post_reposts_recursive_calls_ammount_side_effect)
    def test_fetch_post_reposts_recursive_calls_ammount(self, fetch_method, *args, **kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id=GROUP_POST_ID, owner=group)

        reposts = post.fetch_reposts(all=True)

        self.assertEqual(reposts.count(), 106)
        self.assertEqual(fetch_method.called, True)
        self.assertEqual(fetch_method.call_count, 5)
        self.assertEqual(fetch_method.call_args_list[0][1]['offset'], 0)
        self.assertEqual(fetch_method.call_args_list[1][1]['offset'], 100)
        self.assertEqual(fetch_method.call_args_list[2][1]['offset'], 106)
        self.assertEqual(fetch_method.call_args_list[3][1]['offset'], 107)
        self.assertEqual(fetch_method.call_args_list[4][1]['offset'], 108)

    def test_fetch_user_wall(self):

        owner = UserFactory(remote_id=USER_ID)

        self.assertEqual(Post.objects.count(), 0)

        posts = owner.fetch_posts()

        self.assertGreater(posts.count(), 0)
        self.assertEqual(Post.objects.count(), posts.count())
        self.assertEqual(posts[0].owner, owner)

        owner.fetch_posts(all=True)
        self.assertGreaterEqual(Post.objects.count(), posts.count())

    def test_fetch_group_wall(self):

        group = GroupFactory(remote_id=GROUP_ID, screen_name=GROUP_SCREEN_NAME)

        self.assertEqual(Post.objects.count(), 0)

        posts = group.fetch_posts(count=10)

        self.assertEqual(posts[0].owner, group)
        self.assertEqual(posts.count(), Post.objects.count())
        self.assertEqual(posts.count(), 10)
        self.assertIsInstance(posts[0].date, datetime)
        self.assertGreater(posts[0].likes_count + posts[1].likes_count, 0)
        self.assertGreater(posts[0].comments_count + posts[1].comments_count, 0)
        self.assertGreater(len(posts[0].text), 0)

        # testing `after` parameter
        after = Post.objects.order_by('date')[0].date

        Post.objects.all().delete()
        self.assertEqual(Post.objects.count(), 0)

        posts = group.fetch_posts(after=after)
        self.assertEqual(posts.count(), Post.objects.count())
        self.assertEqual(posts.count(), 10)

        # testing `before` parameter
        before = Post.objects.order_by('-date')[5].date

        Post.objects.all().delete()
        self.assertEqual(Post.objects.count(), 0)

        posts = group.fetch_posts(before=before, after=after)
        self.assertEqual(posts.count(), Post.objects.count())
        self.assertEqual(posts.count(), 5)

        # testing `after` and `all` parameters and returning less than all scope of posts
        Post.objects.all().delete()
        self.assertEqual(Post.objects.count(), 0)

        group.fetch_posts(count=30)
        self.assertEqual(Post.objects.count(), 30)

        posts = group.fetch_posts(after=after, all=True)
        self.assertEqual(posts.count(), 10)

    def test_fetch_group_wall_before(self):
        # TODO: finish test
        group = GroupFactory(remote_id=34384434, screen_name='topmelody')

        before = datetime(2013, 10, 3, tzinfo=timezone.utc)
        after = datetime(2013, 10, 1, tzinfo=timezone.utc)

        posts = group.fetch_posts(all=True, before=before, after=after, filter='owner')

#        print posts
#        self.assertTrue(posts.count() == Post.objects.count() == 100)

    def test_fetch_group_open_wall(self):

        group = GroupFactory(remote_id=OPEN_WALL_GROUP_ID, screen_name=OPEN_WALL_GROUP_SCREEN_NAME)

        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)

        posts = group.fetch_posts(own=0, count=10, extended=1)

        self.assertEqual(posts.count(), 10)
        self.assertEqual(Post.objects.count(), 10)
        self.assertGreater(User.objects.count(), 0)
        self.assertGreater(Post.objects.exclude(author_id=None).count(), 0)

    def test_fetch_user_post_comments(self):

        owner = UserFactory(remote_id=USER_ID)
        post = PostFactory(remote_id=POST_ID, owner=owner, author=owner)
        self.assertEqual(Comment.objects.count(), 0)

        comments = post.fetch_comments()

        self.assertGreater(comments.count(), 0)
        self.assertEqual(Comment.objects.count(), comments.count())
        self.assertEqual(comments[0].object, post)

        post.fetch_comments(all=True)
#        self.assertTrue(Comment.objects.count() > comments.count()) only 1 comment

    @mock.patch('vkontakte_users.models.User.remote.get_by_slug', side_effect=lambda s: UserFactory())
    def test_fetch_group_post_comments(self, *args, **kwargs):
        group = GroupFactory(remote_id=GROUP_ID, screen_name=GROUP_SCREEN_NAME)
        post = PostFactory(remote_id=GROUP_POST_ID, owner=group)
        self.assertEqual(Comment.objects.count(), 0)

        comments = post.fetch_comments(sort='desc', count=90)

        self.assertEqual(comments.count(), 90)
        self.assertEqual(comments.count(), Comment.objects.count())
        self.assertEqual(comments.count(), post.comments.count())
        self.assertEqual(comments[0].object, post)
        self.assertEqual(comments[0].owner, group)

        # testing `after` parameter
        after = Comment.objects.order_by('date')[0].date

        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.count(), 0)

        comments = post.fetch_comments(sort='desc', after=after, count=100)
        self.assertEqual(comments.count(), 90)
        self.assertEqual(comments.count(), Comment.objects.count())
        self.assertEqual(comments.count(), post.comments.count())

        # testing `before` parameter
        before = Comment.objects.order_by('-date')[5].date

        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.count(), 0)

        comments = post.fetch_comments(sort='desc', before=before, after=after)
        self.assertEqual(comments.count(), 85)
        self.assertEqual(comments.count(), Comment.objects.count())

        # testing `after` and `all` parameters
        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.count(), 0)

        comments = post.fetch_comments(sort='desc', after=after, all=True)
        self.assertEqual(comments.count(), 90)
        self.assertEqual(comments.count(), Comment.objects.count())
        self.assertEqual(comments.count(), post.comments.count())

    @mock.patch('vkontakte_users.models.User.remote.get_by_slug', side_effect=lambda s: UserFactory())
    def test_fetch_group_post_comments_bad_unicode(self, *args, **kwargs):
        # http://vk.com/wall-23482909_195292
        # UnicodeDecodeError: 'utf8' codec can't decode byte 0xca in position 0: invalid continuation byte
        group = GroupFactory(remote_id=23482909)
        post = PostFactory(remote_id='-23482909_195292', owner=group)

        comments = post.fetch_comments(sort='desc', count=100)
        self.assertGreater(comments.count(), 0)

        # http://vk.com/wall-41330561_73352
        # UnicodeDecodeError: 'utf8' codec can't decode byte 0xd3 in position 0: invalid continuation byte
        group = GroupFactory(remote_id=41330561)
        post = PostFactory(remote_id='-41330561_73352', owner=group)

        comments = post.fetch_comments(sort='desc', count=100)
        self.assertGreater(comments.count(), 0)

    @mock.patch('vkontakte_users.models.User.remote.get_by_slug', side_effect=lambda s: UserFactory())
    def test_fetch_post_reposts(self, *args, **kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id=GROUP_POST_ID, owner=group)
        users_initial = User.objects.count()

        self.assertEqual(post.reposts_users.count(), 0)

        users = post.fetch_reposts(all=True)

        self.assertGreater(post.reposts_count, 20)
#        self.assertTrue(len(post.reposters) > 20)
        self.assertEqual(post.reposts_count, users.count())
        self.assertEqual(post.reposts_count, User.objects.count() - users_initial)
        self.assertEqual(post.reposts_count, post.reposts_users.count())

    @mock.patch('vkontakte_users.models.User.remote.get_by_slug', side_effect=lambda s: UserFactory())
    def test_fetch_post_reposts1(self, *args, **kwargs):

        group = GroupFactory(remote_id=36948301)
        post = PostFactory(remote_id='-36948301_23383', owner=group)
        users_initial = User.objects.count()

        self.assertEqual(post.reposts_users.count(), 0)

        users = post.fetch_reposts(all=True)

        self.assertGreaterEqual(post.reposts_count, 104)  # total >130, but we store only by users
        self.assertEqual(post.reposts_count, users.count())
        self.assertEqual(post.reposts_count, User.objects.count() - users_initial)
        self.assertEqual(post.reposts_count, post.reposts_users.count())

    @mock.patch('vkontakte_users.models.User.remote.get_by_slug', side_effect=lambda s: UserFactory())
    def test_fetch_post_likes_parser(self, *args, **kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id=GROUP_POST_ID, owner=group)

        self.assertEqual(post.likes_users.count(), 0)

        post.fetch_likes(source='parser')
        self.assertGreater(post.likes_count, 120)
        self.assertEqual(post.likes_count, post.likes_users.count())

    @mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=user_fetch_mock)
    def test_fetch_group_post_likes(self, *args, **kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id=GROUP_POST_ID, owner=group)

        self.assertEqual(post.likes_users.count(), 0)

        users_initial = User.objects.count()
        users = post.fetch_likes(all=True)

        self.assertGreater(post.likes_count, 120)
        self.assertEqual(post.likes_count, len(users))
        self.assertEqual(post.likes_count, User.objects.count() - users_initial)
        self.assertEqual(post.likes_count, post.likes_users.count())

    @mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=user_fetch_mock)
    def test_fetch_group_post_many_likes(self, *args, **kwargs):

        group = GroupFactory(remote_id=GROUP2_ID)
        post = PostFactory(remote_id=GROUP2_POST_WITH_MANY_LIKES_ID, owner=group)
        users_initial = User.objects.count()

        self.assertEqual(post.likes_users.count(), 0)

        users = post.fetch_likes(all=True)

        self.assertGreater(post.likes_count, 3800)
        self.assertEqual(post.likes_count, len(users))
        self.assertEqual(post.likes_count, User.objects.count() - users_initial)
        self.assertEqual(post.likes_count, post.likes_users.count())

    @mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=user_fetch_mock)
    def test_fetch_group_post_many_reposts(self, *args, **kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id=GROUP_POST_WITH_MANY_REPOSTS_ID, owner=group)
        users_initial = User.objects.count()

        self.assertEqual(post.reposts_users.count(), 0)

        users = post.fetch_reposts(all=True)

        self.assertGreater(post.reposts_count, 2500)
#        self.assertTrue(len(post.reposters) > 2500)
        self.assertEqual(post.reposts_count, users.count())
        self.assertEqual(post.reposts_count, User.objects.count() - users_initial)
        self.assertEqual(post.reposts_count, post.reposts_users.count())

    @mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=user_fetch_mock)
    def test_fetch_group_post_changing_likes(self, *args, **kwargs):

        group = GroupFactory(remote_id=GROUP2_ID)
        post = PostFactory(remote_id=GROUP2_POST_WITH_MANY_LIKES_ID, owner=group)

        ids1 = range(100, 200)
        with mock.patch('vkontakte_users.models.User.remote.fetch_likes_user_ids', side_effect=lambda **kw: ids1):
            users1 = post.fetch_likes(all=True)
        state_time1 = post.likes_users.last_update_time()

        self.assertEqual(post.likes_users.count(), users1.count())
        self.assertEqual(post.likes_users.count(), len(ids1))
        self.assertItemsEqual(post.likes_users.all(), User.objects.filter(remote_id__in=ids1))

        ids2 = range(50, 150)
        with mock.patch('vkontakte_users.models.User.remote.fetch_likes_user_ids', side_effect=lambda **kw: ids2):
            users2 = post.fetch_likes(all=True)
        state_time2 = post.likes_users.last_update_time()

        self.assertEqual(post.likes_users.count(), users2.count())
        self.assertEqual(post.likes_users.count(), len(ids2))
        self.assertItemsEqual(post.likes_users.all(), User.objects.filter(remote_id__in=ids2))

        ids3 = range(0, 30)
        with mock.patch('vkontakte_users.models.User.remote.fetch_likes_user_ids', side_effect=lambda **kw: ids3):
            users3 = post.fetch_likes(all=True)
        state_time3 = post.likes_users.last_update_time()

        self.assertEqual(post.likes_users.count(), users3.count())
        self.assertEqual(post.likes_users.count(), len(ids3))
        self.assertItemsEqual(post.likes_users.all(), User.objects.filter(remote_id__in=ids3))

        self.assertItemsEqual(post.likes_users.were_at(state_time1, only_pk=True), ids1)
        self.assertItemsEqual(post.likes_users.were_at(state_time2, only_pk=True), ids2)
        self.assertItemsEqual(post.likes_users.were_at(state_time3, only_pk=True), ids3)

        self.assertItemsEqual(post.likes_users.added_at(state_time2, only_pk=True), range(50, 100))
        self.assertItemsEqual(post.likes_users.removed_at(state_time2, only_pk=True), range(150, 200))

        self.assertItemsEqual(post.likes_users.added_at(state_time3, only_pk=True), range(0, 30))
        self.assertItemsEqual(post.likes_users.removed_at(state_time3, only_pk=True), range(50, 150))

    @mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=user_fetch_mock)
    def test_fetch_group_post_updating_initial_reposts_time_from(self, *args, **kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id=GROUP_POST_ID, owner=group)

        post.reposts_users.through.objects.bulk_create([post.reposts_users.through(user_id=1, post_id=post.pk)])

        self.assertEqual(post.reposts_users.through.objects.count(), 1)

        resources = [{'from_id': 1, 'date': int(time.time())}]
        with mock.patch('vkontakte_wall.models.Post.fetch_reposts_items', side_effect=lambda **kw: resources):
            post.fetch_reposts(all=True)

        self.assertEqual(post.reposts_users.through.objects.count(), 1)
        instance = post.reposts_users.through.objects.all()[0]
        self.assertEqual(instance.user_id, 1)
        self.assertEqual(instance.post_id, post.pk)
        self.assertEqual(instance.time_from, datetime.fromtimestamp(resources[0]['date'], tz=timezone.utc))

    @mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=user_fetch_mock)
    def test_fetch_group_post_changing_reposts(self, *args, **kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id=GROUP_POST_ID, owner=group)

        resources1 = [{'from_id': 1, 'date': int(time.time()) - 1000}]
        with mock.patch('vkontakte_wall.models.Post.fetch_reposts_items', side_effect=lambda **kw: resources1):
            users1 = post.fetch_reposts(all=True)
        state_time1 = post.reposts_users.last_update_time()

        self.assertEqual(post.reposts_users.count(), users1.count())
        self.assertEqual(post.reposts_users.count(), 1)
        self.assertItemsEqual(post.reposts_users.all(), User.objects.filter(remote_id__in=[1]))

        resources2 = [{'from_id': 2, 'date': int(time.time()) - 500}]
        with mock.patch('vkontakte_wall.models.Post.fetch_reposts_items', side_effect=lambda **kw: resources1 + resources2):
            users2 = post.fetch_reposts(all=True)
        state_time2 = post.reposts_users.last_update_time()

        self.assertEqual(post.reposts_users.count(), users2.count())
        self.assertEqual(post.reposts_users.count(), 2)
        self.assertItemsEqual(post.reposts_users.all(), User.objects.filter(remote_id__in=[1, 2]))

        resources3 = [{'from_id': 3, 'date': int(time.time()) - 100}]
        with mock.patch('vkontakte_wall.models.Post.fetch_reposts_items', side_effect=lambda **kw: resources3):
            users3 = post.fetch_reposts(all=True)
        state_time3 = post.reposts_users.last_update_time()

        self.assertEqual(post.reposts_users.count(), users3.count())
        self.assertEqual(post.reposts_users.count(), 1)
        self.assertItemsEqual(post.reposts_users.all(), User.objects.filter(remote_id__in=[3]))

        # check results of 3 changes
        self.assertItemsEqual(post.reposts_users.were_at(state_time1, only_pk=True), [1])
        self.assertItemsEqual(post.reposts_users.were_at(state_time2, only_pk=True), [1, 2])
        self.assertItemsEqual(post.reposts_users.were_at(state_time3, only_pk=True), [3])

        state_time_add1 = datetime.utcfromtimestamp(resources1[0]['date']).replace(tzinfo=timezone.utc)
        state_time_add2 = datetime.utcfromtimestamp(resources2[0]['date']).replace(tzinfo=timezone.utc)
        state_time_add3 = datetime.utcfromtimestamp(resources3[0]['date']).replace(tzinfo=timezone.utc)

        self.assertItemsEqual(post.reposts_users.added_at(state_time_add1, only_pk=True), [1])
        self.assertItemsEqual(post.reposts_users.added_at(state_time_add2, only_pk=True), [2])
        self.assertItemsEqual(post.reposts_users.added_at(state_time_add3, only_pk=True), [3])

        self.assertItemsEqual(post.reposts_users.removed_at(state_time1, only_pk=True), [])
        self.assertItemsEqual(post.reposts_users.removed_at(state_time2, only_pk=True), [])
        self.assertItemsEqual(post.reposts_users.removed_at(state_time3, only_pk=True), [1, 2])

        # returns user ID=2 with old date
        resources4 = resources3 + resources2
        with mock.patch('vkontakte_wall.models.Post.fetch_reposts_items', side_effect=lambda **kw: resources4):
            users4 = post.fetch_reposts(all=True)

        self.assertEqual(post.reposts_users.count(), users4.count())
        self.assertEqual(post.reposts_users.count(), 2)
        self.assertItemsEqual(post.reposts_users.all(), User.objects.filter(remote_id__in=[2, 3]))

        # changed after last fetching
        self.assertItemsEqual(post.reposts_users.were_at(state_time3, only_pk=True), [2, 3])
        self.assertItemsEqual(post.reposts_users.removed_at(state_time3, only_pk=True), [1])

    @mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=user_fetch_mock)
    def test_fetch_group_post_comment_likes(self, *args, **kwargs):
        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id=GROUP_POST_ID, owner=group)
        comment = CommentFactory(remote_id=GROUP_COMMENT_ID, object=post, owner=group)

        self.assertEqual(comment.likes_users.count(), 0)
        users_initial = User.objects.count()

        users = comment.fetch_likes(all=True)

        self.assertGreater(comment.likes_count, 0)
        self.assertEqual(comment.likes_count, len(users))
        self.assertEqual(comment.likes_count, User.objects.count() - users_initial)
        self.assertEqual(comment.likes_count, comment.likes_users.count())

    def test_parse_post(self):
        response = '''{"comments": {"can_post": 0, "count": 4},
                 "date": 1298365200,
                 "from_id": 55555,
                 "geo": {"coordinates": "55.6745689498 37.8724562529",
                  "place": {"city": "Moskovskaya oblast",
                   "country": "Russian Federation",
                   "title": "Shosseynaya ulitsa, Moskovskaya oblast"},
                  "type": "point"},
                 "id": 465,
                 "likes": {"can_like": 1, "can_publish": 1, "count": 10, "user_likes": 0},
                 "online": 1,
                 "post_source": {"type": "api"},
                 "reply_count": 0,
                 "reposts": {"count": 3, "user_reposted": 0},
                 "text": "qwerty",
                 "owner_id": 201164356}
            '''
        instance = Post()
        owner = UserFactory(remote_id=201164356)  # Travis Djangov
        author = UserFactory(remote_id=55555)
        instance.parse(json.loads(response))
        instance.save()

        self.assertTrue(instance.remote_id.startswith('201164356_'))
        self.assertEqual(instance.owner, owner)
        self.assertEqual(instance.author, author)
        self.assertEqual(instance.reply_count, 0)
        self.assertEqual(instance.likes_count, 10)
        self.assertEqual(instance.reposts_count, 3)
        self.assertEqual(instance.comments_count, 4)
        self.assertEqual(instance.text, 'qwerty')
        self.assertIsInstance(instance.date, datetime)
        self.assertIsInstance(instance.raw_json, dict)
        self.assertEqual(instance.raw_json['comments'], {"can_post": 0, "count": 4})

    def test_parse_comment(self):

        response = '''{"response":[6,
            {"id":2505,"from_id":16271479,"date":1298365200,"text":"Добрый день , кароче такая идея когда опросы создаешь вместо статуса - можно выбрать аудитории опрашиваемых, например только женский или мужской пол могут участвовать (то бишь голосовать в опросе)."},
            {"id":2507,"from_id":16271479,"date":1286105582,"text":"Это уже не практично, имхо.<br>Для этого делайте группу и там опрос, а в группу принимайте тех, кого нужно.","reply_to_uid":16271479,"reply_to_cid":2505},
            {"id":2547,"from_id":2943,"date":1286218080,"text":"Он будет только для групп благотворительных организаций."}]}
            '''
        user = UserFactory(remote_id=USER_ID)
        post = PostFactory(remote_id=POST_ID, owner=user)
        #instance = Comment(post=post)
        instance = CommentFactory(object=post)
        author = UserFactory(remote_id=16271479)
        instance.parse(json.loads(response)['response'][1])
        instance.save()

        self.assertEqual(instance.remote_id, '%s_2505' % USER_ID)
        self.assertEqual(
            instance.text, u'Добрый день , кароче такая идея когда опросы создаешь вместо статуса - можно выбрать аудитории опрашиваемых, например только женский или мужской пол могут участвовать (то бишь голосовать в опросе).')
        self.assertEqual(instance.author, author)
        self.assertIsInstance(instance.date, datetime)

        instance = Comment(object=post)
        instance.parse(json.loads(response)['response'][2])
        instance.save()

        self.assertEqual(instance.remote_id, '%s_2507' % USER_ID)
        self.assertEqual(instance.reply_for.remote_id, 16271479)

    def test_post_prepare_create_params(self):
        text = 'test text'
        expected_config = {
            'owner_id': GROUP_ID * -1,
            'friends_only': 0,
            'from_group': '',
            'message': text,
            'attachments': u'',
            'services': '',
            'signed': 0,
            'publish_date': '',
            'lat': '',
            'long': '',
            'place_id': '',
            'post_id': ''
        }
        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory()
        post.owner = group
        post.text = text
        self.assertEqual(post.prepare_create_params(), expected_config)

    def test_post_prepare_update_params(self):
        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id='%s_17' % GROUP_ID, owner=group)
        update_text = 'update text'
        expected_config = {
            'owner_id': GROUP_ID * -1,
            'friends_only': 0,
            'from_group': '',
            'message': update_text,
            'attachments': u'',
            'services': '',
            'signed': 0,
            'publish_date': '',
            'lat': '',
            'long': '',
            'place_id': '',
            'post_id': u'17'
        }
        post1 = Post.objects.get(id=post.id)
        post1.text = update_text
        self.assertEqual(post1.prepare_update_params(), expected_config)

    def test_post_prepare_delete_params(self):
        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id='%s_17' % GROUP_ID, owner=group)
        expected_params = {
            'owner_id': GROUP_ID * -1,
            'post_id': '17',
        }
        self.assertEqual(post.prepare_delete_params(), expected_params)

    def assertPostTheSameEverywhere(self, post):
        post_remote = Post.remote.fetch(ids=[post.remote_id])[0]
        self.assertEqual(post_remote.remote_id, post.remote_id)
        self.assertEqual(post_remote.text, post.text)

    def test_post_crud_methods(self):
        group = GroupFactory(remote_id=GROUP_CRUD_ID)
        user = UserFactory(remote_id=USER_AUTHOR_ID)

        self.assertEqual(Post.objects.count(), 0)

        # create
        post = Post(text='Test message', owner=group, author=user, date=datetime.now())
        post.save(commit_remote=True)
        self.objects_to_delete += [post]

        self.assertEqual(Post.objects.count(), 1)
        self.assertNotEqual(len(post.remote_id), 0)
        self.assertPostTheSameEverywhere(post)

        # create by manager
        post = Post.objects.create(
            text='Test message created by manager', owner=group, author=user, date=datetime.now(), commit_remote=True)
        self.objects_to_delete += [post]

        self.assertEqual(Post.objects.count(), 2)
        self.assertNotEqual(len(post.remote_id), 0)
        self.assertPostTheSameEverywhere(post)

        # create by manager on user's wall
        post = Post.objects.create(
            text='Test message', owner=user, author=user, date=datetime.now(), commit_remote=True)
        self.objects_to_delete += [post]

        self.assertEqual(Post.objects.count(), 3)
        self.assertNotEqual(len(post.remote_id), 0)
        self.assertPostTheSameEverywhere(post)

        # update
        post.text = 'Test message updated'
        post.save(commit_remote=True)

        self.assertEqual(Post.objects.count(), 3)
        self.assertPostTheSameEverywhere(post)

        # delete
        post.delete(commit_remote=True)

        self.assertEqual(Post.objects.count(), 3)
        self.assertTrue(post.archived)
        self.assertEqual(Post.remote.fetch(ids=[post.remote_id]).count(), 0)

        # restore
        post.restore(commit_remote=True)
        self.assertFalse(post.archived)

        self.assertEqual(Post.objects.count(), 3)
        self.assertPostTheSameEverywhere(post)
