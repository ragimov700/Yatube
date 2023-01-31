from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
import tempfile
import shutil

from ..models import Post, Group

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test_User')
        cls.group = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_slug_one',
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
            image=cls.uploaded
        )
        cls.uploaded.seek(0)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Test_User2')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись Post в БД"""
        username = self.post.author
        author_client = Client()
        author_client.force_login(username)
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост 2',
            'image': self.uploaded,
        }
        response = author_client.post(reverse('posts:post_create'),
                                      data=form_data, follow=True, )
        self.assertRedirects(response,
                             reverse(('posts:profile'),
                                     kwargs={'username': username}
                                     )
                             )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(self.post.author, response.context['author'])
        self.assertTrue(Post.objects.filter(image='posts/small.gif').exists())

    def test_edit_post(self):
        """Валидная форма изменяет Post в БД"""
        group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_two',
            description='Тестовое описание 2',
        )
        post = Post.objects.create(
            author=self.user,
            text='Тестовый пост с группой group2',
            group=group2,
        )
        username = post.author
        post_id = post.pk
        author_client = Client()
        author_client.force_login(username)
        posts_count_group = self.group.group_posts.count()
        posts_count_group2 = group2.group_posts.count()
        form_data = {
            'text': 'Измененный тестовый пост',
            'group': self.group.id
        }
        response = author_client.post(reverse(('posts:post_edit'),
                                              kwargs={'post_id': post_id}),
                                      data=form_data, follow=True)
        self.assertRedirects(response,
                             reverse(('posts:post_detail'),
                                     kwargs={'post_id': post_id}
                                     )
                             )
        self.assertEqual(self.group.group_posts.count(), posts_count_group + 1)
        self.assertEqual(group2.group_posts.count(), posts_count_group2 - 1)
        self.assertEqual(post.author, response.context['user'])
        self.assertEqual(self.group, Post.objects.all()[0].group)
        self.assertTrue(Post.objects.filter(image='posts/small.gif').exists())
