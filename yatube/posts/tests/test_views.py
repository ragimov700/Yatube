from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.paginator import Page
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.images import ImageFile
from django.core.cache import cache
from django.conf import settings
import tempfile
import shutil
from http import HTTPStatus
from ..models import Post, Group, Comment, Follow
from ..forms import PostForm

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded
        )
        cls.first_group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_slug1',
            description='Тестовое описание 1',
        )
        cls.second_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug2',
            description='Тестовое описание 2',
        )
        cls.post_first_group = Post.objects.create(
            author=cls.user,
            text='Тестовый пост первой группы',
            group=cls.first_group
        )
        cls.post_second_group = Post.objects.create(
            author=cls.user,
            text='Тестовый пост второй группы',
            group=cls.second_group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Test_User')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        slug = self.group.slug
        response = self.authorized_client.get(
            reverse(('posts:group_list'), kwargs={'slug': slug})
        )
        field_klass = {
            'group': Group,
            'page_obj': Page,
        }
        for value, expected_klass in field_klass.items():
            with self.subTest(value=value):
                field_klass = response.context[value]
                self.assertIsInstance(field_klass, expected_klass)
        self.assertIsInstance(response.context['page_obj'][0].image, ImageFile)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        field_klass = response.context['page_obj']
        expected_klass = Page
        self.assertIsInstance(field_klass, expected_klass)
        self.assertIsInstance(response.context['page_obj'][0].image, ImageFile)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        user = self.post.author
        self.authorized_client.force_login(user)
        response = self.authorized_client.get(
            reverse(('posts:profile'), kwargs={'username': user})
        )
        field_klass = {
            'author': User,
            'page_obj': Page,
        }
        for value, expected_klass in field_klass.items():
            with self.subTest(value=value):
                field_klass = response.context[value]
                self.assertIsInstance(field_klass, expected_klass)
        self.assertIsInstance(response.context['page_obj'][0].image, ImageFile)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        post_id = self.post.pk
        response = self.authorized_client.get(
            reverse(('posts:post_detail'), kwargs={'post_id': post_id})
        )
        expected_klass = Post
        field_klass = response.context['post']
        self.assertIsInstance(field_klass, expected_klass)
        self.assertIsInstance(response.context['post'].image, ImageFile)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_create')
        )
        expected_klass = PostForm
        field_klass = response.context['form']
        self.assertIsInstance(field_klass, expected_klass)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        post_id = self.post.pk
        user = self.post.author
        self.authorized_client.force_login(user)
        response = self.authorized_client.get(
            reverse(('posts:post_edit'), kwargs={'post_id': post_id})
        )
        field_klass = {
            'form': PostForm,
            'is_edit': bool,
        }
        for value, expected_klass in field_klass.items():
            with self.subTest(value=value):
                field_klass = response.context[value]
                self.assertIsInstance(field_klass, expected_klass)

    def test_second_group_list_page_show_correct_context(self):
        """В шаблон для второй группы не попал не свой контекст."""
        slug_first_group = self.first_group.slug
        slug_second_group = self.second_group.slug
        response = self.authorized_client.get(
            reverse(('posts:group_list'), kwargs={'slug': slug_first_group})
        )
        second_response = self.authorized_client.get(
            reverse(('posts:group_list'), kwargs={'slug': slug_second_group})
        )
        post_first_group = response.context['page_obj'][0]
        post_second_group = second_response.context['page_obj'][0]
        self.assertEqual(post_second_group, self.post_second_group,
                         'Пост попал в другую группу')
        self.assertEqual(post_first_group, self.post_first_group,
                         'Пост попал в другую группу')

    def test_comment_avalible_for_guest_client(self):
        """Комментирование недоступно для неавторизованного пользователя"""
        post_id = self.post.pk
        response = self.guest_client.get(
            reverse(('posts:add_comment'), kwargs={'post_id': post_id})
        )
        self.assertEqual(
            response.status_code, HTTPStatus.FOUND,
            'Комментирование доступно для незарегистрированного пользователя'
        )

    def test_comment_add_comment(self):
        """Создается комментарий в БД """
        post_id = self.post.pk
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий'
        }
        self.authorized_client.post(
            reverse(('posts:add_comment'), kwargs={'post_id': post_id}),
            data=form_data
        )
        self.assertEqual(comments_count + 1, Comment.objects.count())
        self.assertTrue(Comment.objects.filter(
            text=form_data['text']).exists()
        )

    def test_cache_create_index(self):
        """Проверка кэширования главной страницы"""
        posts_count = Post.objects.count()
        post_cache = Post.objects.create(
            text='Проверка кэширования',
            author=self.user
        )
        self.assertEqual(posts_count + 1, Post.objects.count())
        post_cache.delete()
        self.assertEqual(posts_count, Post.objects.count())
        self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(post_cache.text,
                         'Проверка кэширования',
                         'Отсутствует кэш')


class PaginatorViewsTest(TestCase):
    FIRST_PAGE_POSTS = 10
    SECOND_PAGE_POSTS = 4
    SUM_OF_POSTS = FIRST_PAGE_POSTS + SECOND_PAGE_POSTS
    FIRST_POST = 0

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        posts = [
            Post(author=cls.user,
                 group=cls.group,
                 text=f'Тестовый пост {i}') for i in range(cls.FIRST_POST,
                                                           cls.SUM_OF_POSTS)
        ]
        cls.post = Post.objects.bulk_create(posts)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Test_User')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_page_index_contains_ten_records(self):
        """Проерка паджинатора страница 1 index"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context['page_obj']), self.FIRST_PAGE_POSTS
        )

    def test_second_page_index_contains_three_records(self):
        """Проерка паджинатора страница 2 index"""
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']), self.SECOND_PAGE_POSTS
        )

    def test_first_page_group_list_contains_ten_records(self):
        """Проерка паджинатора страница 1 group_list"""
        slug = self.group.slug
        response = self.authorized_client.get(
            (reverse(('posts:group_list'), kwargs={'slug': slug}))
        )
        self.assertEqual(
            len(response.context['page_obj']), self.FIRST_PAGE_POSTS
        )

    def test_second_page_group_list_contains_three_records(self):
        """Проерка паджинатора страница 2 group_list"""
        slug = self.group.slug
        response = self.authorized_client.get(
            (reverse('posts:group_list', kwargs={'slug': slug}) + '?page=2'))
        self.assertEqual(
            len(response.context['page_obj']), self.SECOND_PAGE_POSTS
        )

    def test_first_page_profile_contains_ten_records(self):
        """Проерка паджинатора страница 1 profile"""
        username = self.post[self.FIRST_POST].author
        response = self.authorized_client.get(
            (reverse(('posts:profile'), kwargs={'username': username}))
        )
        self.assertEqual(
            len(response.context['page_obj']), self.FIRST_PAGE_POSTS
        )

    def test_second_page_profile_contains_three_records(self):
        """Проерка паджинатора страница 2 profile"""
        username = self.post[self.FIRST_POST].author
        response = self.authorized_client.get(
            (reverse
                ('posts:profile', kwargs={'username': username}) + '?page=2'))
        self.assertEqual(
            len(response.context['page_obj']), self.SECOND_PAGE_POSTS
        )


class FollowUsersTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post_auth = Post.objects.create(
            author=cls.user,
            text='Тестовый пост пользователя auth'
        )

    def setUp(self):
        self.user = User.objects.create_user(username='Test_User')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_client_follow_unfollow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок"""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0,
                         'Имеются посты в подписках')
        Follow.objects.create(
            user=self.user,
            author=self.post_auth.author
        )
        # Проверка подписки
        posts_user_count = Post.objects.filter(author=self.post_auth.author
                                               ).count()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), posts_user_count,
                         'Количество постов в follow не совпадает')
        # Проверка отписки
        Follow.objects.filter(user=self.user, author=self.post_auth.author
                              ).delete()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0,
                         'Имеются посты в подписках после отписки')

    def test_new_post_in_following(self):
        """Новая запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех, кто не подписан."""
        user = User.objects.create_user(username='Test_User2')
        authorized_user = Client()
        authorized_user.force_login(user)
        Follow.objects.create(
            user=user,
            author=self.post_auth.author
        )
        posts_user_count = Post.objects.filter(author=self.post_auth.author
                                               ).count()
        response_user = authorized_user.get(reverse('posts:follow_index'))
        response_client = self.authorized_client.get(
            reverse('posts:follow_index'))
        posts_count_user = len(response_user.context['page_obj'])
        posts_count_client = len(response_client.context['page_obj'])
        self.assertEqual(
            posts_count_user, posts_user_count, 'Есть посты в follow')
        self.assertEqual(posts_count_client, 0, 'Есть посты в follow')
        Post.objects.create(
            author=self.post_auth.author,
            text='Тестовый пост'
        )
        response_user = authorized_user.get(reverse('posts:follow_index'))
        response_client = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertEqual(
            posts_count_user + 1, len(response_user.context['page_obj']),
            'Количество постов в follow не совпадает')
        self.assertEqual(
            posts_count_client, len(response_client.context['page_obj']),
            'Есть посты у неподписанного в follow после создания поста')
