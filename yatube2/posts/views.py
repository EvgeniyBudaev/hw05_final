from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


from .models import Post, Group, Follow
from .forms import PostForm, CommentForm
from yatube2.settings import POSTS_IN_PAGINATOR

User = get_user_model()


def index(request):
    post_list = Post.objects.all().order_by('-pub_date')
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'posts/index.html',
        {'page': page}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.filter(group=group).order_by("-pub_date")
    paginator = Paginator(posts, POSTS_IN_PAGINATOR)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    context = {
        "group": group,
        "page": page
    }

    return render(request, "posts/group.html", context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all().order_by("-pub_date")
    paginator = Paginator(posts, POSTS_IN_PAGINATOR)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = Follow.objects.filter(
        user=request.user.id, author=author.id).all()

    context = {
        'page': page,
        'author': author,
        "posts_count": author.posts.count(),
        'is_active': True,
        'following': following,
        'follower_count': author.follower.count(),
        'following_count': author.following.count()
    }

    return render(request, 'posts/profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    author = post.author
    posts_count = author.posts.count()
    form = CommentForm(instance=None)
    comments = post.comments.select_related('author').all()

    context = {
        "post": post,
        "author": author,
        "posts_count": posts_count,
        'form': form,
        'comments': comments
    }

    return render(request, 'posts/post.html', context)


@login_required
def new_post(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("index")
    form = PostForm()

    return render(request, 'posts/new_post.html', {'form': form})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if request.user != post.author:
        return redirect(
            'post', post_id=post.id, username=post.author.username)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect(
            'post', post_id=post.id, username=post.author.username)
    return render(
        request, 'posts/new_post.html', {'form': form, 'post': post})


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect(
            'post', post_id=post.id, username=post.author.username)
    return render(
        request, 'posts/include/comments.html',
        {'form': form, 'post': post})


@login_required
def post_delete(request, username, post_id):
    post = get_object_or_404(
        Post, author__username=username, id=post_id)
    post.delete()
    return redirect('profile', username=post.author.username)


def page_not_found(request, exception):
    # Переменная exception содержит отладочную информацию,
    # выводить её в шаблон пользователской страницы 404 мы не станем
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    posts = Post.objects.select_related('author').filter(
        author__following__user=request.user).all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'posts/follow.html',
        {
            'paginator': paginator,
            'page': page})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    follow = author.following.filter(
        author=author.id, user=request.user.id).exists()
    if not follow and request.user != author:
        Follow.objects.create(author=author, user=request.user)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, author=author.id, user=request.user.id)
    follow.delete()
    return redirect('profile', username=username)


class TestFollow(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='Tom')

        cls.user_following = User.objects.create_user(username='Jerry')

        cls.post = Post.objects.create(
            text='Новая запись в ленте подписчиков',
            author=TestFollow.user_following)

    def setUp(self):
        self.client_auth = Client()
        self.client_auth.force_login(TestFollow.user_follower)

    def test_follow_authorized_user(self):
        self.client_auth.get(reverse(
            'profile_follow', kwargs={
                'username': TestFollow.user_following.username}))

        self.assertEqual(Follow.objects.count(), 1)

    def test_unfollow_authorized_user(self):
        self.client_auth.get(reverse(
            'profile_unfollow', kwargs={
                'username': TestFollow.user_following.username}))

        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_not_authorized_user(self):
        response = self.client.get(reverse(
            'profile_follow', kwargs={
                'username': TestFollow.user_following.username}))

        kw = {'username': TestFollow.user_following.username}
        reverse_login = reverse('login')
        reverse_follow = reverse('profile_follow', kwargs=kw)

        self.assertRedirects(
            response, f'{reverse_login}?next={reverse_follow}')

    def test_check_new_post_from_follower(self):
        Follow.objects.create(
            user=TestFollow.user_follower, author=TestFollow.user_following)

        response = self.client_auth.get(reverse('follow_index'))
        self.assertContains(response, TestFollow.post.text)

    def test_check_new_post_from_not_follower(self):
        user_not_follower = User.objects.create_user(username='zhanna')
        self.client.force_login(user_not_follower)

        response = self.client.get(reverse('follow_index'))
        self.assertNotContains(response, TestFollow.post.text)
