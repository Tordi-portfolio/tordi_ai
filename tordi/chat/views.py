import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .models import Conversation, Message
from .ai_service import get_tordi_response, build_user_content


def _conversation_or_404(user, conversation_id):
    return get_object_or_404(Conversation, id=conversation_id, user=user)


def _history_for_ai(conversation, up_to_message=None):
    """Build the Anthropic-format message history for a conversation."""
    qs = conversation.messages.all()
    if up_to_message:
        qs = qs.filter(created_at__lte=up_to_message.created_at).exclude(
            id__gt=up_to_message.id
        )
    history = []
    for msg in qs:
        if msg.role == "user":
            content = build_user_content(msg.content, msg.image if msg.image else None)
        else:
            content = msg.content
        history.append({"role": msg.role, "content": content})
    return history


@login_required
def dashboard(request):
    conversations = request.user.conversations.all()
    active_id = request.GET.get("chat")
    active_conversation = None
    messages_qs = []

    if active_id:
        active_conversation = get_object_or_404(
            Conversation, id=active_id, user=request.user
        )
        messages_qs = active_conversation.messages.all()
    elif conversations.exists():
        active_conversation = conversations.first()
        messages_qs = active_conversation.messages.all()

    return render(
        request,
        "chat/dashboard.html",
        {
            "conversations": conversations,
            "active_conversation": active_conversation,
            "chat_messages": messages_qs,
        },
    )


@login_required
@require_POST
def new_chat(request):
    conversation = Conversation.objects.create(user=request.user, title="New chat")
    return redirect(f"/?chat={conversation.id}")


@login_required
@require_POST
def send_message(request, conversation_id):
    conversation = _conversation_or_404(request.user, conversation_id)

    text = (request.POST.get("message") or "").strip()
    image = request.FILES.get("image")
    audio = request.FILES.get("audio")
    # Voice notes are transcribed client-side (Web Speech API) and arrive as
    # text in `message`; if a raw audio file is also attached we store it
    # for the record even though the transcript is what's sent to the AI.

    if not text and not image and not audio:
        return JsonResponse({"ok": False, "error": "Empty message."}, status=400)

    user_msg = Message.objects.create(
        conversation=conversation,
        role="user",
        content=text,
        image=image,
        audio=audio,
    )

    if conversation.title == "New chat" and text:
        conversation.title = text[:60]
    conversation.save(update_fields=["title", "updated_at"])

    history = _history_for_ai(conversation)
    reply_text = get_tordi_response(history)

    assistant_msg = Message.objects.create(
        conversation=conversation, role="assistant", content=reply_text
    )

    return JsonResponse(
        {
            "ok": True,
            "conversation_title": conversation.title,
            "user_message": {
                "id": user_msg.id,
                "content": user_msg.content,
                "image_url": user_msg.image.url if user_msg.image else None,
            },
            "assistant_message": {
                "id": assistant_msg.id,
                "content": assistant_msg.content,
            },
        }
    )


@login_required
@require_POST
def edit_message(request, message_id):
    """Edit a user message, delete everything after it, and re-ask the AI."""
    message = get_object_or_404(
        Message, id=message_id, conversation__user=request.user, role="user"
    )
    new_text = (request.POST.get("message") or "").strip()
    if not new_text:
        return JsonResponse({"ok": False, "error": "Message can't be empty."}, status=400)

    conversation = message.conversation
    message.content = new_text
    message.edited = True
    message.save(update_fields=["content", "edited"])

    # Remove every message that came after this one (old branch of the chat)
    conversation.messages.filter(created_at__gt=message.created_at).delete()

    history = _history_for_ai(conversation, up_to_message=message)
    reply_text = get_tordi_response(history)
    assistant_msg = Message.objects.create(
        conversation=conversation, role="assistant", content=reply_text
    )
    conversation.save(update_fields=["updated_at"])

    return JsonResponse(
        {
            "ok": True,
            "assistant_message": {"id": assistant_msg.id, "content": assistant_msg.content},
        }
    )


@login_required
@require_POST
def rename_chat(request, conversation_id):
    conversation = _conversation_or_404(request.user, conversation_id)
    new_title = (request.POST.get("title") or "").strip()
    if new_title:
        conversation.title = new_title[:100]
        conversation.save(update_fields=["title"])
    return JsonResponse({"ok": True, "title": conversation.title})


@login_required
@require_POST
def delete_chat(request, conversation_id):
    conversation = _conversation_or_404(request.user, conversation_id)
    conversation.delete()
    return JsonResponse({"ok": True})


@login_required
@require_POST
def pin_chat(request, conversation_id):
    conversation = _conversation_or_404(request.user, conversation_id)
    conversation.pinned = not conversation.pinned
    conversation.save(update_fields=["pinned"])
    return JsonResponse({"ok": True, "pinned": conversation.pinned})
