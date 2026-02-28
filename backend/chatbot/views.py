import json
import uuid
import os
from django.http import StreamingHttpResponse
from django.conf import settings
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from openai import OpenAI

from .models import ChatSession, ChatMessage
from blog.models import Post


def get_relevant_posts(query: str, top_k: int = 5):
    """Search for relevant posts using text search (pgvector in production)."""
    posts = Post.objects.filter(
        status='published'
    ).filter(
        Q(title__icontains=query) |
        Q(content__icontains=query) |
        Q(summary__icontains=query)
    )[:top_k]

    return [
        {
            'id': p.id,
            'title': p.title,
            'slug': p.slug,
            'summary': p.summary[:200] if p.summary else p.content[:200],
            'content_snippet': p.content[:1000],
        }
        for p in posts
    ]


def build_rag_prompt(query: str, context_posts: list) -> str:
    """Build a RAG prompt with retrieved context."""
    context = "\n\n---\n\n".join(
        f"**{p['title']}**\n{p['content_snippet']}"
        for p in context_posts
    )

    return f"""You are a helpful assistant for the blog-jun tech blog. Answer the user's question based on the following blog post context.
If the answer isn't in the context, say you don't have enough information but try to be helpful.
Always reference which blog posts you used.

## Blog Context:
{context}

## User Question:
{query}"""


def sse_stream(query: str, session_id: str):
    """Generate SSE stream from OpenAI."""
    api_key = getattr(settings, 'OPENAI_API_KEY', '') or os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        yield f"data: {json.dumps({'error': 'OpenAI API key not configured'})}\n\n"
        return

    # Get relevant posts
    context_posts = get_relevant_posts(query)
    sources = [{'title': p['title'], 'slug': p['slug']} for p in context_posts]

    # Send sources first
    yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

    # Save user message
    session, _ = ChatSession.objects.get_or_create(session_id=session_id)
    ChatMessage.objects.create(session=session, role='user', content=query)

    # Stream from OpenAI
    client = OpenAI(api_key=api_key)
    prompt = build_rag_prompt(query, context_posts)

    full_response = ""
    try:
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": query},
            ],
            stream=True,
            max_tokens=1024,
            temperature=0.7,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_response += token
                yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    # Save assistant message
    ChatMessage.objects.create(
        session=session,
        role='assistant',
        content=full_response,
        sources=sources,
    )

    yield f"data: {json.dumps({'type': 'done'})}\n\n"


@api_view(['POST'])
@permission_classes([AllowAny])
def chat_sse(request):
    """RAG chatbot with SSE streaming."""
    message = request.data.get('message', '')
    session_id = request.data.get('session_id', str(uuid.uuid4()))

    if not message:
        return Response({'error': 'Message is required'}, status=400)

    # Check if SSE is requested
    if request.headers.get('Accept') == 'text/event-stream':
        response = StreamingHttpResponse(
            sse_stream(message, session_id),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

    # Non-streaming fallback
    context_posts = get_relevant_posts(message)
    sources = [{'title': p['title'], 'slug': p['slug']} for p in context_posts]

    api_key = getattr(settings, 'OPENAI_API_KEY', '') or os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        return Response({
            'session_id': session_id,
            'message': 'Chatbot requires OpenAI API key configuration.',
            'sources': sources,
        })

    client = OpenAI(api_key=api_key)
    prompt = build_rag_prompt(message, context_posts)

    response_data = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": message},
        ],
        max_tokens=1024,
        temperature=0.7,
    )

    answer = response_data.choices[0].message.content

    # Save to DB
    session, _ = ChatSession.objects.get_or_create(session_id=session_id)
    ChatMessage.objects.create(session=session, role='user', content=message)
    ChatMessage.objects.create(session=session, role='assistant', content=answer, sources=sources)

    return Response({
        'session_id': session_id,
        'message': answer,
        'sources': sources,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def chat_sessions(request):
    """List recent chat sessions for dashboard."""
    sessions = ChatSession.objects.order_by('-updated_at')[:20]
    data = []
    for s in sessions:
        last_msg = s.messages.last()
        data.append({
            'session_id': s.session_id,
            'last_message': last_msg.content[:100] if last_msg else '',
            'message_count': s.messages.count(),
            'updated_at': s.updated_at,
        })
    return Response(data)
