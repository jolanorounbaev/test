from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.text import Truncator

User = get_user_model()

class Like(models.Model):
    """Abstract base model for like functionality"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='%(class)s_likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} liked {self.content_object}"

class Post(models.Model):
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='posts'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(
        User,
        through='PostLike',
        through_fields=('post', 'user'),
        related_name='liked_posts'
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at'], name='post_created_at_idx'),
        ]

    def __str__(self):
        return f"Post #{self.id} by {self.author.email}"

    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'pk': self.pk})

    def preview(self, length=50):
        """Return truncated content for previews"""
        return Truncator(self.content).chars(length)

    @property
    def comment_count(self):
        return self.comments.count()

    @property
    def like_count(self):
        return self.likes.count()

    def user_has_liked(self, user):
        """Check if a user has liked this post"""
        return self.likes.filter(id=user.id).exists()

class PostLike(Like):
    """Through model for post likes"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes')

    class Meta:
        unique_together = ('user', 'post')

class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(
        User,
        through='CommentLike',
        through_fields=('comment', 'user'),
        related_name='liked_comments'
    )

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at'], name='comment_post_created_idx'),
        ]

    def __str__(self):
        return f"Comment #{self.id} by {self.author.email} on Post #{self.post.id}"

    def preview(self, length=50):
        return Truncator(self.content).chars(length)

    @property
    def reply_count(self):
        return self.replies.count()

    @property
    def like_count(self):
        return self.likes.count()

    def user_has_liked(self, user):
        """Check if a user has liked this comment"""
        return self.likes.filter(id=user.id).exists()

class CommentLike(Like):
    """Through model for comment likes"""
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='comment_likes')

    class Meta:
        unique_together = ('user', 'comment')

class Reply(models.Model):
    comment = models.ForeignKey(
        Comment,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='replies'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(
        User,
        through='ReplyLike',
        through_fields=('reply', 'user'),
        related_name='liked_replies'
    )

    class Meta:
        verbose_name_plural = 'Replies'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['comment', 'created_at'], name='reply_comment_created_idx'),
        ]

    def __str__(self):
        return f"Reply #{self.id} by {self.author.email} to Comment #{self.comment.id}"

    def preview(self, length=50):
        return Truncator(self.content).chars(length)

    @property
    def like_count(self):
        return self.likes.count()

    def user_has_liked(self, user):
        """Check if a user has liked this reply"""
        return self.likes.filter(id=user.id).exists()

class ReplyLike(Like):
    """Through model for reply likes"""
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE, related_name='reply_likes')

    class Meta:
        unique_together = ('user', 'reply')
