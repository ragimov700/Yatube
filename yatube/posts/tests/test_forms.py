from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Test_User')
        cls.group = Group.objects.create(
            title='группа0',
            slug='test_slug0',
            description='проверка описания0'
        )

        cls.post = Post.objects.create(
            text='Тестовый заголовок',
            author=cls.author,
        )

    def setUp(self):
        self.guest_user = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post(self):
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), 2)
        post = Post.objects.last()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group.id, form_data['group'])

    def test_edit_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
        }
        self.authorized_client.post(reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id},
        ), data=form_data)
        post_endcount = Post.objects.count()
        post = Post.objects.last()
        self.assertEqual(post_count, post_endcount)
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.group.id, form_data['group'])

    def test_unauth_user_cant_publish_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
        }
        responce = self.guest_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        redirect = reverse("login") + "?next=" + reverse("posts:post_create")
        self.assertRedirects(responce, redirect)
        self.assertEqual(Post.objects.count(), posts_count)
