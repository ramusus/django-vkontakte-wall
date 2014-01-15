# -*- coding: utf-8 -*-
from django.test import TestCase
from models import Post, Comment
from factories import PostFactory, UserFactory, GroupFactory, CommentFactory
from vkontakte_users.models import User
from datetime import datetime
import simplejson as json
import mock

USER_ID = 5223304
POST_ID = '5223304_130'

GROUP_ID = 16297716
GROUP_SCREEN_NAME = 'cocacola'
GROUP_POST_ID = '-16297716_126261'
GROUP_COMMENT_ID = '-16297716_126262'

OPEN_WALL_GROUP_ID = 19391365
OPEN_WALL_GROUP_SCREEN_NAME = 'nokia'

GROUP_CRUD_ID = 59154616
POST_CRUD_ID = '-59154616_366'
USER_AUTHOR_ID = 201164356

GROUP2_ID = 22522055
GROUP2_POST_WITH_MANY_LIKES_ID = '-22522055_484919'

# TRAVIS_USER_ID = 201164356
# TR_POST_ID = '201164356_15'
# POST_WITH_COMMENT = '-59154616_332'
# POST_OWN_ID = '-59154616_330'


class VkontakteWallTest(TestCase):

    def setUp(self):
        self.objects_to_delete = []

    def tearDown(self):
        for object in self.objects_to_delete:
            object.delete(commit_remote=True)

    def test_fetch_posts(self, *args, **kwargs):

        self.assertTrue(Post.objects.count() == 0)

        posts = Post.remote.fetch(ids=[POST_ID, GROUP_POST_ID])
        self.assertTrue(len(posts) == Post.objects.count() == 2)

    def fetch_post_comments_recursive_calls_ammount_side_effect(*args, **kwargs):
        comments_count = 100 if kwargs['offset'] == 0 else 6
        comments = [CommentFactory() for i in range(comments_count)]
        return Comment.objects.filter(pk__in=[comment.pk for comment in comments])

    @mock.patch('vkontakte_wall.models.Comment.remote.fetch', side_effect=fetch_post_comments_recursive_calls_ammount_side_effect)
    def test_fetch_post_comments_recursive_calls_ammount(self, fetch_method, *args, **kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id=GROUP_POST_ID, wall_owner=group)

        comments = post.fetch_comments(sort='desc', all=True)

        self.assertTrue(len(comments) > 105)
        self.assertEqual(fetch_method.called, True)
        self.assertEqual(fetch_method.call_count, 2)
        self.assertEqual(fetch_method.call_args_list[0][1]['offset'], 0)
        self.assertEqual(fetch_method.call_args_list[1][1]['offset'], 100)

    def test_fetch_user_wall(self):

        owner = UserFactory(remote_id=USER_ID)

        self.assertEqual(Post.objects.count(), 0)

        posts = owner.fetch_posts()

        self.assertTrue(len(posts) > 0)
        self.assertEqual(Post.objects.count(), len(posts))
        self.assertEqual(posts[0].wall_owner, owner)

        owner.fetch_posts(all=True)
        self.assertTrue(Post.objects.count() >= len(posts))

    def test_fetch_group_wall(self):

        group = GroupFactory(remote_id=GROUP_ID, screen_name=GROUP_SCREEN_NAME)

        self.assertEqual(Post.objects.count(), 0)

        posts = group.fetch_posts(count=10)

        self.assertEqual(posts[0].wall_owner, group)
        self.assertTrue(len(posts) == Post.objects.count() == 10)
        self.assertTrue(isinstance(posts[0].date, datetime))
        self.assertTrue(posts[0].likes + posts[1].likes > 0)
        self.assertTrue(posts[0].comments + posts[1].comments > 0)
        self.assertTrue(len(posts[0].text) > 0)

        # testing `after` parameter
        after = Post.objects.order_by('date')[0].date

        Post.objects.all().delete()
        self.assertEqual(Post.objects.count(), 0)

        posts = group.fetch_posts(after=after)
        self.assertTrue(len(posts) == Post.objects.count() == 10)

        # testing `after` and `all` parameters and returning less than all scope of posts
        Post.objects.all().delete()
        self.assertEqual(Post.objects.count(), 0)

        group.fetch_posts(count=30)
        posts = group.fetch_posts(after=after, all=True)
        self.assertEqual(Post.objects.count(), 30)
        self.assertEqual(len(posts), 10)

    def test_fetch_group_open_wall(self):

        group = GroupFactory(remote_id=OPEN_WALL_GROUP_ID, screen_name=OPEN_WALL_GROUP_SCREEN_NAME)

        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(User.objects.count(), 0)

        count = 10
        posts = group.fetch_posts(own=0, count=count, extended=1)

        self.assertEqual(len(posts), count)
        self.assertEqual(Post.objects.count(), count)
        self.assertTrue(User.objects.count() > 0)
        self.assertTrue(Post.objects.exclude(author_id=None).count() > 0)

    def test_fetch_user_post_comments(self):

        owner = UserFactory(remote_id=USER_ID)
        post = PostFactory(remote_id=POST_ID, wall_owner=owner, author=owner)
        self.assertEqual(Comment.objects.count(), 0)

        comments = post.fetch_comments()

        self.assertTrue(len(comments) > 0)
        self.assertEqual(Comment.objects.count(), len(comments))
        self.assertEqual(comments[0].post, post)

        post.fetch_comments(all=True)
#        self.assertTrue(Comment.objects.count() > len(comments)) only 1 comment

    @mock.patch('vkontakte_users.models.User.remote.get_by_slug', side_effect=lambda s: UserFactory())
    def test_fetch_group_post_comments(self, *args, **kwargs):
        group = GroupFactory(remote_id=GROUP_ID, screen_name=GROUP_SCREEN_NAME)
        post = PostFactory(remote_id=GROUP_POST_ID, wall_owner=group)
        self.assertEqual(Comment.objects.count(), 0)

        comments = post.fetch_comments(sort='desc', count=90)

        self.assertTrue(len(comments) == Comment.objects.count() == post.wall_comments.count() == 90)
        self.assertEqual(comments[0].post, post)
        self.assertEqual(comments[0].wall_owner, group)

        # testing `after` parameter
        after = Comment.objects.order_by('date')[0].date

        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.count(), 0)

        comments = post.fetch_comments(sort='desc', after=after, count=100)
        self.assertTrue(len(comments) == Comment.objects.count() == post.wall_comments.count() == 90)

        # testing `after` and `all` parameters
        Comment.objects.all().delete()
        self.assertEqual(Comment.objects.count(), 0)

        comments = post.fetch_comments(sort='desc', after=after, all=True)
        self.assertTrue(len(comments) == Comment.objects.count() == post.wall_comments.count() == 90)

    @mock.patch('vkontakte_users.models.User.remote.get_by_slug', side_effect=lambda s: UserFactory())
    def test_fetch_post_reposts(self, *args, **kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id=GROUP_POST_ID, wall_owner=group)

        self.assertTrue(post.repost_users.count() == 0)
        users = post.fetch_reposts(all=True)
        self.assertTrue(post.reposts >= 20)
        self.assertTrue(post.reposts == post.repost_users.count() == users.count())

        group = GroupFactory(remote_id=36948301)
        post = PostFactory(remote_id='-36948301_13599', wall_owner=group)

        self.assertTrue(post.reposts == post.repost_users.count() == 0)
        users = post.fetch_reposts(all=True)
        self.assertTrue(post.reposts == 1)
        self.assertTrue(post.reposts == post.repost_users.count() == users.count())

    @mock.patch('vkontakte_users.models.User.remote.get_by_slug', side_effect=lambda s: UserFactory())
    def test_fetch_post_likes_parser(self, *args, **kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id=GROUP_POST_ID, wall_owner=group)

        self.assertEqual(post.like_users.count(), 0)
        self.assertEqual(post.likes, 0)

        post.fetch_likes(source='parser')
        self.assertTrue(post.likes > 120)
        self.assertEqual(post.likes, post.like_users.count())

    @mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=lambda ids, **kw: User.objects.filter(id__in=[user.id for user in [UserFactory(remote_id=i) for i in ids]]))
    def test_fetch_group_post_likes(self, *args, **kwargs):

        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id=GROUP_POST_ID, wall_owner=group)

        self.assertEqual(post.like_users.count(), 0)
        self.assertEqual(post.likes, 0)

        User.objects.all().delete()

        users = post.fetch_likes(all=True)

        self.assertTrue(post.likes > 120)
        self.assertEqual(post.likes, len(users))
        self.assertEqual(post.likes, User.objects.count())
        self.assertEqual(post.likes, post.like_users.count())

        # try to fetch again
        likes = post.likes
        User.objects.all().delete()
        users = post.fetch_likes(all=True)

        self.assertEqual(post.likes, likes)
        self.assertEqual(post.likes, len(users))
        self.assertEqual(post.likes, User.objects.count())
        self.assertEqual(post.likes, post.like_users.count())

        # try to fetch more than 1000 likes
        group2 = GroupFactory(remote_id=GROUP2_ID)
        post2 = PostFactory(remote_id=GROUP2_POST_WITH_MANY_LIKES_ID, wall_owner=group2)
        User.objects.all().delete()

        self.assertEqual(post2.like_users.count(), 0)
        self.assertEqual(post2.likes, 0)

        users = post2.fetch_likes(all=True)

        self.assertTrue(post2.likes > 1000)
        self.assertEqual(post2.likes, len(users))
        self.assertEqual(post2.likes, User.objects.count())
        self.assertEqual(post2.likes, post2.like_users.count())

    @mock.patch('vkontakte_users.models.User.remote.fetch', side_effect=lambda ids, **kw: User.objects.filter(id__in=[user.id for user in [UserFactory(remote_id=i) for i in ids]]))
    def test_fetch_group_post_comment_likes(self, *args, **kwargs):
        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id=GROUP_POST_ID, wall_owner=group)
        comment = CommentFactory(remote_id=GROUP_COMMENT_ID, post=post, wall_owner=group)

        self.assertEqual(comment.like_users.count(), 0)
        self.assertEqual(comment.likes, 0)
        users_initial = User.objects.count()

        users = comment.fetch_likes(all=True)

        self.assertTrue(comment.likes > 0)
        self.assertEqual(comment.likes, len(users))
        self.assertEqual(comment.likes, User.objects.count() - users_initial)
        self.assertEqual(comment.likes, comment.like_users.count())

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
                 "to_id": 201164356}
            '''
        instance = Post()
        owner = UserFactory(remote_id=201164356)  # Travis Djangov
        author = UserFactory(remote_id=55555)
        instance.parse(json.loads(response))
        instance.save()

        self.assertTrue(instance.remote_id.startswith('201164356_'))
        self.assertEqual(instance.wall_owner, owner)
        self.assertEqual(instance.author, author)
        self.assertEqual(instance.reply_count, 0)
        self.assertEqual(instance.likes, 10)
        self.assertEqual(instance.reposts, 3)
        self.assertEqual(instance.comments, 4)
        self.assertEqual(instance.text, 'qwerty')
        self.assertTrue(isinstance(instance.date, datetime))

    def test_parse_comment(self):

        response = '''{"response":[6,
            {"cid":2505,"uid":16271479,"date":1298365200,"text":"Добрый день , кароче такая идея когда опросы создаешь вместо статуса - можно выбрать аудитории опрашиваемых, например только женский или мужской пол могут участвовать (то бишь голосовать в опросе)."},
            {"cid":2507,"uid":16271479,"date":1286105582,"text":"Это уже не практично, имхо.<br>Для этого делайте группу и там опрос, а в группу принимайте тех, кого нужно.","reply_to_uid":16271479,"reply_to_cid":2505},
            {"cid":2547,"uid":2943,"date":1286218080,"text":"Он будет только для групп благотворительных организаций."}]}
            '''
        user = UserFactory(remote_id=USER_ID)
        post = PostFactory(remote_id=POST_ID, wall_owner=user)
        #instance = Comment(post=post)
        instance = CommentFactory(post=post)
        author = UserFactory(remote_id=16271479)
        instance.parse(json.loads(response)['response'][1])
        instance.save()

        self.assertEqual(instance.remote_id, '%s_2505' % USER_ID)
        self.assertEqual(instance.text, u'Добрый день , кароче такая идея когда опросы создаешь вместо статуса - можно выбрать аудитории опрашиваемых, например только женский или мужской пол могут участвовать (то бишь голосовать в опросе).')
        self.assertEqual(instance.author, author)
        self.assertTrue(isinstance(instance.date, datetime))

        instance = Comment(post=post)
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
        post.wall_owner = group
        post.text = text
        self.assertEqual(post.prepare_create_params(), expected_config)

    def test_post_prepare_update_params(self):
        group = GroupFactory(remote_id=GROUP_ID)
        post = PostFactory(remote_id='%s_17' % GROUP_ID, wall_owner=group)
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
        post = PostFactory(remote_id='%s_17' % GROUP_ID, wall_owner=group)
        expected_params = {
            'owner_id': GROUP_ID * -1,
            'post_id': '17',
        }
        self.assertEqual(post.prepare_delete_params(), expected_params)

    def test_post_crud_methods(self):
        group = GroupFactory(remote_id=GROUP_CRUD_ID)
        user = UserFactory(remote_id=USER_AUTHOR_ID)

        def assert_local_equal_to_remote(post):
            post_remote = Post.remote.fetch(ids=[post.remote_id])[0]
            self.assertEqual(post_remote.remote_id, post.remote_id)
            self.assertEqual(post_remote.text, post.text)

        self.assertEqual(Post.objects.count(), 0)

        # create
        post = Post(text='Test message', wall_owner=group, author=user, date=datetime.now())
        post.save(commit_remote=True)
        self.objects_to_delete += [post]

        self.assertEqual(Post.objects.count(), 1)
        self.assertNotEqual(len(post.remote_id), 0)
        assert_local_equal_to_remote(post)

        # update
        post.text = 'Test message updated'
        post.save(commit_remote=True)

        self.assertEqual(Post.objects.count(), 1)
        assert_local_equal_to_remote(post)

        # delete
        post.delete(commit_remote=True)

        self.assertEqual(Post.objects.count(), 1)
        self.assertTrue(post.archived)
        self.assertEqual(Post.remote.fetch(ids=[post.remote_id]).count(), 0)

        # restore
        post.restore(commit_remote=True)
        self.assertFalse(post.archived)

        self.assertEqual(Post.objects.count(), 1)
        assert_local_equal_to_remote(post)

        # create by manager
        post = Post.objects.create(text='Test message created by manager', wall_owner=group, author=user, date=datetime.now(), commit_remote=True)
        self.objects_to_delete += [post]

        self.assertEqual(Post.objects.count(), 2)
        self.assertNotEqual(len(post.remote_id), 0)
        assert_local_equal_to_remote(post)

    def test_comment_crud_methods(self):
        group = GroupFactory(remote_id=GROUP_CRUD_ID)
        post = PostFactory(remote_id=POST_CRUD_ID, text='', wall_owner=group)
        user = UserFactory(remote_id=USER_AUTHOR_ID)

        def assert_local_equal_to_remote(comment):
            comment_remote = Comment.remote.fetch_post(post=comment.post).get(remote_id=comment.remote_id)
            self.assertEqual(comment_remote.remote_id, comment.remote_id)
            self.assertEqual(comment_remote.text, comment.text)

        Comment.remote.fetch_post(post=post)
        self.assertEqual(Comment.objects.count(), 0)

        # create
        comment = Comment(text='Test comment', post=post, wall_owner=group, author=user, date=datetime.now())
        comment.save(commit_remote=True)
        self.objects_to_delete += [comment]

        self.assertEqual(Comment.objects.count(), 1)
        self.assertNotEqual(len(comment.remote_id), 0)
        assert_local_equal_to_remote(comment)

        # update
        comment.text = 'Test comment updated'
        comment.save(commit_remote=True)

        self.assertEqual(Comment.objects.count(), 1)
        assert_local_equal_to_remote(comment)

        # delete
        comment.delete(commit_remote=True)

        self.assertEqual(Comment.objects.count(), 1)
        self.assertTrue(comment.archived)
        self.assertEqual(Comment.remote.fetch_post(post=comment.post).filter(remote_id=comment.remote_id).count(), 0)

        # restore
        comment.restore(commit_remote=True)
        self.assertFalse(comment.archived)

        self.assertEqual(Comment.objects.count(), 1)
        assert_local_equal_to_remote(comment)

        # create by manager
        comment = Comment.objects.create(text='Test comment created by manager', post=post, wall_owner=group, author=user, date=datetime.now(), commit_remote=True)
        self.objects_to_delete += [comment]

        self.assertEqual(Comment.objects.count(), 2)
        self.assertNotEqual(len(comment.remote_id), 0)
        assert_local_equal_to_remote(comment)