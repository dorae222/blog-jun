from django.contrib import admin
from .models import (
    Category, Tag, Series, Post, PostImage, PostTemplate,
    ArchitectureConcept, ArchitectureEntry,
    CloudServiceEntry, CloudServiceRelation,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'slug', 'icon', 'color', 'parent', 'order']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order']


class PostImageInline(admin.TabularInline):
    model = PostImage
    extra = 1


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'post_type', 'status', 'view_count', 'created_at']
    list_filter = ['status', 'post_type', 'category']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PostImageInline]
    readonly_fields = ['view_count', 'reading_time']


@admin.register(PostTemplate)
class PostTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'post_type', 'category']


@admin.register(ArchitectureConcept)
class ArchitectureConceptAdmin(admin.ModelAdmin):
    list_display = ['name', 'abbreviation', 'slug', 'color']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'abbreviation']


class ConceptInline(admin.TabularInline):
    model = ArchitectureEntry.concepts.through
    extra = 1


@admin.register(ArchitectureEntry)
class ArchitectureEntryAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'decoder_type', 'param_scale', 'release_date']
    list_filter = ['decoder_type', 'organization']
    search_fields = ['name', 'organization']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ConceptInline]
    exclude = ['concepts']  # managed via inline
    readonly_fields = ['created_at', 'updated_at']


class CloudServiceRelationInline(admin.TabularInline):
    model = CloudServiceRelation
    fk_name = 'from_service'
    extra = 1


@admin.register(CloudServiceEntry)
class CloudServiceEntryAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'service_domain', 'importance', 'is_serverless', 'launch_year']
    list_filter = ['provider', 'service_domain', 'is_serverless']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [CloudServiceRelationInline]
    readonly_fields = ['created_at', 'updated_at']
