from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username="TestAuthor")
        cls.user_not_author = User.objects.create_user(
            username="TestNotAuthor"
        )
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="testslug",
            description="Тестовое описание",
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовая запись",
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.user_not_author)

    def test_guest_urls_access(self):
        url_names = {
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.id}/',
        }
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # Проверяем доступность страниц для авторизованного пользователя
    def test_autorized_urls_access(self):
        url_names = {
            "/",
            f"/group/{self.group.slug}/",
            f"/profile/{self.user.username}/",
            f"/posts/{self.post.id}/",
            f"/posts/{self.post.id}/edit/",
            "/create/",
        }
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, 200)

    # Проверяем редиректы для неавторизованного пользователя
    def test_list_url_redirect_guest(self):
        url_names_redirects = {
            f"/posts/{self.post.id}/edit/": (
                f"/auth/login/?next=/posts/{self.post.id}/edit/"
            ),
            "/create/": "/auth/login/?next=/create/",
        }
        for address, redirect_address in url_names_redirects.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect_address)

    # Редирект для не автора
    def test_redirect_not_author(self):
        response = self.authorized_client_not_author.get(
            f"/posts/{self.post.id}/edit/", follow=True
        )
        self.assertRedirects(response, f"/posts/{self.post.id}/")

    # Проверка вызываемых шаблонов для каждого адреса
    def test_task_list_url_corret_templates(self):
        url_names_templates = {
            "/": "posts/index.html",
            f"/group/{self.group.slug}/": "posts/group_list.html",
            f"/profile/{self.user.username}/": "posts/profile.html",
            f"/posts/{self.post.id}/": "posts/post_detail.html",
            f"/posts/{self.post.id}/edit/": "posts/create_post.html",
            "/create/": "posts/create_post.html",
        }
        for address, template in url_names_templates.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    # Страница не найденна
    def test_page_not_found(self):
        """Страница не найденна."""
        response = self.guest_client.get("/unexisting_page/")
        self.assertEqual(response.status_code, 404)
