from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from posts.forms import PostForm
from posts.models import Post, Group

User = get_user_model()


class GroupPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД,
        # она понадобится для тестирования страницы deals:task_detail
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Отдельная запись',
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def check_post_info(self, post):
        with self.subTest(post=post):
            self.assertEqual(post.text, self.post.text)
            self.assertEqual(post.author, self.post.author)
            self.assertEqual(post.group.id, self.post.group.id)

# Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        self.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={
                'slug': self.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={
                'username': self.user.username}): 'posts/profile.html',
            reverse('posts:post_detail', kwargs={
                'post_id': self.post.id}): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.id}): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }

        for reverse_name, template, in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

# проверяем контекст
    def test_index_page_show_correct_context(self):
        """Шаблон главной страницы с правильным контекстом"""

        response = self.authorized_client.get(reverse('posts:index'))
        self.check_post_info(response.context['page_obj'][0])

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'], self.group)
        self.check_post_info(response.context['page_obj'][0])

    def test_profile_page_show_correct_context(self):
        """Страница профиля с правильным контекстом"""

        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(response.context['author'], self.user)
        self.check_post_info(response.context['page_obj'][0])

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.check_post_info(response.context['post'])

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        # Словарь ожидаемых типов полей формы:
        form_fields = (
            ('text', forms.fields.CharField),
            ('group', forms.fields.ChoiceField),
        )
        for value, expected in form_fields:
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertIsInstance(response.context.get('is_edit'), bool)
        self.assertTrue(response.context.get('is_edit'))

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""

        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_post_appears_in_correct_group(self):
        """Проверка что пост появился в нужной группе"""
        namespace_dict = {
            reverse("posts:index"): "page_obj",
            reverse(
                "posts:group_list",
                args=[GroupPagesTests.group.slug]
            ): "page_obj",
            reverse(
                "posts:profile",
                args=[GroupPagesTests.user.username]
            ): "page_obj",
        }
        for reverse_name, context in namespace_dict.items():
            with self.subTest(reverse_name=reverse_name, context=context):
                response = self.client.get(reverse_name)
                self.assertIn(GroupPagesTests.post, response.context[context])
        another_group = Group.objects.create(
            title="Другая группа",
            slug="another-group",
            description="Описание другой группы",
        )
        response = self.client.get(
            reverse("posts:group_list", args={another_group.slug})
        )
        self.assertNotIn(GroupPagesTests.post, response.context["page_obj"])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание'
        )

    # создаём 13 тестовых записей.
        list_posts = [Post(
            text=f'Текст для проверки {i}',
            author=cls.user,
            group=cls.group,
        ) for i in range(13)]
        Post.objects.bulk_create(list_posts)

    # список шаблонов для проверки работы paginator
        cls.list_template_names = {
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': cls.group.slug}),
            reverse('posts:profile', kwargs={'username': cls.user.username}),
        }

    def test_first_page_contains_ten_records(self):
        """ тестируем работу Paginator. Проверка вывода 10 записей"""

        num_posts_on_first_page = 10
        for reverse_name in self.list_template_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']),
                    num_posts_on_first_page
                )

    def test_second_page_contains_three_records(self):
        """ тестируем работу Paginator. Проверка вывода оставшихся 3 записей"""

        num_posts_on_second_page = 3

        for reverse_name in self.list_template_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    num_posts_on_second_page
                )
