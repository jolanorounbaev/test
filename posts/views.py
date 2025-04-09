from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Post, Comment, Reply
from .forms import PostForm, CommentForm, ReplyForm
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import CommentLike, PostLike, ReplyLike

@login_required
def post_feed(request):
    # Optimized query with select_related and prefetch_related
    posts = Post.objects.select_related('author') \
                       .prefetch_related('comments__author', 
                                       'comments__replies__author') \
                       .order_by('-created_at')
    
    post_form = PostForm()
    return render(request, 'posts/feed.html', {
        'posts': posts,
        'post_form': post_form
    })

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Your post has been created!')
        else:
            messages.error(request, 'There was an error with your post.')
    return redirect('post_feed')

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added!')
        else:
            messages.error(request, 'Error adding comment.')
    return redirect('post_feed')

@login_required
def add_reply(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.comment = comment
            reply.author = request.user
            reply.save()
            messages.success(request, 'Reply added!')
        else:
            messages.error(request, 'Error adding reply.')
    return redirect('post_feed')


@login_required
@require_POST  # Extra security to block GET requests
def delete_post(request, post_id):
    try:
        post = get_object_or_404(Post, id=post_id, author=request.user)
        post.delete()
        messages.success(request, '🗑️ Post deleted!')
    except Exception as e:
        messages.error(request, '🚨 Delete failed!')
    return redirect('post_feed')

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, author=request.user)
    comment.delete()
    messages.success(request, 'Comment deleted successfully')
    return redirect('post_feed')

@login_required
def delete_reply(request, reply_id):
    reply = get_object_or_404(Reply, id=reply_id, author=request.user)
    reply.delete()
    messages.success(request, 'Reply deleted successfully')
    return redirect('post_feed')



@require_POST
@login_required
def toggle_post_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = PostLike.objects.get_or_create(
        user=request.user,
        post=post
    )
    
    if not created:
        like.delete()
    
    return JsonResponse({
        'liked': created,
        'like_count': post.likes.count()
    })

@login_required
def toggle_comment_like(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
    if not created:
        like.delete()
    return JsonResponse({
        'liked': created,
        'like_count': comment.like_count
    })

@login_required
def toggle_reply_like(request, reply_id):
    reply = get_object_or_404(Reply, id=reply_id)
    like, created = ReplyLike.objects.get_or_create(user=request.user, reply=reply)
    if not created:
        like.delete()
    return JsonResponse({
        'liked': created,
        'like_count': reply.like_count
    })
