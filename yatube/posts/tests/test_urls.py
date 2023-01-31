from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus
from ..models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Test_User')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_urls_exists_at_desired_location(self):
        """URL-адрес доступен по соответствующему
        адресу для всех пользоателей."""
        username = self.post.author
        post_id = self.post.id
        slug = self.group.slug
        url_names = (
            '/',
            reverse(('posts:group_list'), kwargs={'slug': slug}),
            reverse(('posts:profile'), kwargs={'username': username}),
            reverse(('posts:post_detail'), kwargs={'post_id': post_id}),
        )
        clients = (self.authorized_client, self.guest_client)
        for client in clients:
            for address in url_names:
                with self.subTest(address=address):
                    response = client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK,
                                     'Ошибка в доступе к страницам!')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        username = self.post.author
        post_id = self.post.id
        slug = self.group.slug
        templates_url_names = {
            'posts/index.html': (reverse('posts:index')),
            'posts/group_list.html':
                reverse(('posts:group_list'), kwargs={'slug': slug}),
            'posts/profile.html':
                reverse(('posts:profile'), kwargs={'username': username}),
            'posts/post_detail.html':
                reverse(('posts:post_detail'), kwargs={'post_id': post_id}),
        }
        clients = (self.authorized_client, self.guest_client)
        for client in clients:
            cache.clear()
            for template, address in templates_url_names.items():
                with self.subTest(address=address):
                    response = client.get(address)
                    self.assertTemplateUsed(response, template,
                                            'Ошибка в доступе к шаблонам!')

    def test_unexsisting_page_url(self):
        """Несуществующая страница недоступна для пользователей"""
        clients = (self.authorized_client, self.guest_client)
        for client in clients:
            response = client.get('/unexsisting_page/')
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND,
                             'Несуществующая страница доступна для'
                             ' пользователей!')

    def test_post_create_authorized_user(self):
        """Страница создания поста /create/ доступна
        для авторизованного пользователя"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(
            response.status_code, HTTPStatus.OK,
            'Страница создания поста недоступна для зарег пользователя'
        )

    def test_post_create_guest_user(self):
        """Страница создания поста /create/ недоступна
        для неавторизованного пользователя"""
        response = self.guest_client.get('/create/')
        self.assertEqual(
            response.status_code, HTTPStatus.FOUND,
            'Страница создания поста доступна для'
            ' незарегистрированного пользователя'
        )

    def test_post_edit_guest_user(self):
        """Страница редактирования поста /posts/post_id/edit недоступна
        для неавторизованного пользователя"""
        post_id = self.post.id
        response = self.guest_client.get(
            reverse(('posts:post_edit'), kwargs={'post_id': post_id})
        )
        self.assertEqual(
            response.status_code, HTTPStatus.FOUND,
            'Страница редактирования поста недоступна'
            ' для незарегистрированного пользователя')

    def test_post_edit_authorized_user(self):
        """Страница редактирования поста /posts/post_id/edit недоступна
        для авторизованного пользователя"""
        post_id = self.post.id
        response = self.authorized_client.get(
            reverse(('posts:post_edit'), kwargs={'post_id': post_id})
        )
        self.assertEqual(
            response.status_code, HTTPStatus.FOUND,
            'Страница редактирования поста доступна для не автора')

    def test_post_edit_author(self):
        """Страница редактирования поста /posts/post_id/edit доступна
        для автора поста"""
        author = self.post.author
        post_id = self.post.id
        self.authorized_client.force_login(author)
        response = self.authorized_client.get(
            reverse(('posts:post_edit'), kwargs={'post_id': post_id})
        )
        self.assertEqual(
            response.status_code, HTTPStatus.OK,
            'Страница редактирования поста недоступна для автора')
