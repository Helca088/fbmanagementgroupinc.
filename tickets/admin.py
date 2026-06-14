from django.contrib import admin
from django.utils.html import format_html
from .models import Section, Ticket, ConcernType

@admin.register(ConcernType)
class ConcernTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'section')
    list_filter = ('section',)
    
@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    

    list_display = ('title', 'email', 'section', 'concern_type', 'status', 'priority')

    readonly_fields = ('download_button',)
    list_filter = ('section', 'status', 'priority')

    fields = ('title', 'email', 'message', 'status', 'attachment', 'download_button', 'section', 'priority')

    def download_button(self, obj):
        if obj.attachment:
            return format_html(
            '<a href="/ticket/{}/download/">⬇ Download File</a>',
            obj.id
        )
        return "No file"

    download_button.short_description = "Download File" 

    def status(self, obj):
        color = "orange" if obj.status == "pending" else "green"
        return format_html(
        '<span style="color:{}; font-weight:bold;">{}</span>',
        color,
     obj.status
    )

    status.short_description = "Status"

# Register your models here.

admin.site.site_header = "FB MANAGEMENT GROUP INC."

admin.site.site_title = "Ticket System"

admin.site.index_title = "Welcome Admin"