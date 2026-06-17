from django.contrib import admin
from django.utils.html import format_html
from .models import Section, Ticket, ConcernType
from django.contrib.admin import AdminSite

class MyAdminSite(AdminSite):
    class Media:
        css = {
            "all": ("css/admin.css",)
        }

admin_site = MyAdminSite(name="myadmin")

@admin.register(ConcernType)
class ConcernTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'section')
    list_filter = ('section',)
    
@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    class Media:
        js = ('css/js/admin_autorefresh.js',)
        
    search_fields =[
        'outlet',
        'section__name',
        'concern_type__name'
        ]

    list_display = ('outlet', 'section', 'concern_type', 'status', 'priority','scheduled_date', 'scheduled_time')

    readonly_fields = ('download_button', 'outlet', 'message')
    list_filter = ('section', 'status', 'priority')

    fields = ('outlet', 'message', 'status', 
              'scheduled_date', 'scheduled_time', 'admin_note',
              'attachment', 'download_button',
              'section', 'priority', 'concern_type')

    def download_button(self, obj):
        if obj.attachment:
            return format_html(
            '<a href="/ticket/{}/download/">⬇ Download File</a>',
            obj.id
        )
        return "No file"

    download_button.short_description = "Download File" 

    def colored_status(self, obj):
        color = "orange" if obj.status == "pending" else "green"
        return format_html(
        '<span style="color:{}; font-weight:bold;">{}</span>',
        color,
     obj.status
    )

    colored_status.short_description = "Status"

# Register your models here.

admin.site.site_header = "FB MANAGEMENT GROUP INC."

admin.site.site_title = "Ticket System"

admin.site.index_title = "Welcome Admin"