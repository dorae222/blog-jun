from django.http import HttpResponse
from django.conf import settings

from blog.models import Post


def sitemap_xml(request):
    base_url = getattr(settings, 'SITE_URL', 'https://blog.dorae222.com').rstrip('/')
    posts = (
        Post.objects.filter(status='published')
        .values('slug', 'updated_at')
        .order_by('-updated_at')
    )

    urls = [
        f'<url><loc>{base_url}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>',
        f'<url><loc>{base_url}/posts</loc><changefreq>daily</changefreq><priority>0.9</priority></url>',
    ]
    for post in posts:
        lastmod = post['updated_at'].strftime('%Y-%m-%d')
        urls.append(
            f'<url>'
            f'<loc>{base_url}/post/{post["slug"]}</loc>'
            f'<lastmod>{lastmod}</lastmod>'
            f'<changefreq>weekly</changefreq>'
            f'<priority>0.8</priority>'
            f'</url>'
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + '\n'.join(urls)
        + '\n</urlset>'
    )
    return HttpResponse(xml, content_type='application/xml')


def robots_txt(request):
    site_url = getattr(settings, 'SITE_URL', 'https://blog.dorae222.com').rstrip('/')
    content = (
        'User-agent: *\n'
        'Allow: /\n'
        'Disallow: /admin/\n'
        'Disallow: /api/\n'
        f'\nSitemap: {site_url}/sitemap.xml\n'
    )
    return HttpResponse(content, content_type='text/plain')
