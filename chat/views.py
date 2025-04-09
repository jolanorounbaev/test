from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import ChatMessage, GroupChat, GroupMember
from registerandlogin.models import CustomUser

@login_required
def chat_room(request, mode, id):
    context = {}
    
    if mode == "private":
        receiver = get_object_or_404(CustomUser, id=id)
        context["chat_title"] = receiver.full_name
        context["is_private"] = True
        context["receiver"] = receiver

        if request.method == "POST":
            content = request.POST.get("content")
            if content:
                ChatMessage.objects.create(sender=request.user, receiver=receiver, content=content)
                return redirect("chat:chat_room", mode="private", id=receiver.id)

        messages = ChatMessage.objects.filter(
            sender=request.user, receiver=receiver
        ) | ChatMessage.objects.filter(
            sender=receiver, receiver=request.user
        )
        context["messages"] = messages.order_by("timestamp")

    elif mode == "group":
        group = get_object_or_404(GroupChat, id=id)
        if not GroupMember.objects.filter(group=group, user=request.user).exists():
            return render(request, "chat/access_denied.html")

        context["chat_title"] = group.name
        context["is_private"] = False
        context["group"] = group

        if request.method == "POST":
            content = request.POST.get("content")
            if content:
                ChatMessage.objects.create(sender=request.user, group=group, content=content)
                return redirect("chat:chat_room", mode="group", id=group.id)

        context["messages"] = ChatMessage.objects.filter(group=group).order_by("timestamp")

    else:
        return render(request, "chat/invalid_chat_type.html")

    return render(request, "chat/chat.html", context)


from django.db.models import Q

@login_required
def chat_index(request):
    user = request.user

    # Recent private conversations (you as sender or receiver)
    private_conversations = ChatMessage.objects.filter(
        Q(sender=user) | Q(receiver=user),
        receiver__isnull=False  # Only private messages
    ).order_by('-timestamp')

    # We'll deduplicate based on who you're chatting with
    recent_contacts = {}
    for msg in private_conversations:
        other = msg.receiver if msg.sender == user else msg.sender
        if other.id not in recent_contacts:
            recent_contacts[other.id] = other

    # Groups user is part of
    group_memberships = GroupMember.objects.filter(user=user).select_related('group')
    groups = [membership.group for membership in group_memberships]

    return render(request, 'chat/index.html', {
        'recent_contacts': recent_contacts.values(),
        'groups': groups,
    })
