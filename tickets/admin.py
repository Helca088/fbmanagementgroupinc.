from django.contrib import admin
from django.utils.html import format_html
from .models import Section, Ticket, ConcernType
from django.contrib.admin import AdminSite
from .models import TicketStatusLog
from unfold.admin import ModelAdmin, TabularInline
from unfold.sites import UnfoldAdminSite
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

# unregister default admin
admin.site.unregister(User)

# re-register with custom settings
@admin.register(User)
class CustomUserAdmin(DjangoUserAdmin, ModelAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('is_staff', 'is_active')

    actions = ['delete_selected'] 


    actions_on_top = True
    actions_on_bottom = True
    actions_selection_counter = True
    show_full_result_count = True
    
class MyAdminSite(UnfoldAdminSite):
    class Media:
        css = {
            "all": ("/static/css/admin.css",)
        }

admin_site = MyAdminSite(name="myadmin")

@admin.register(TicketStatusLog)
class TicketStatuslogAdmin(ModelAdmin):
    list_display = (
    'ticket',
    'old_status',
    'new_status',
    'changed_at'    
    )

@admin.register(ConcernType)
class ConcernTypeAdmin(ModelAdmin):
    list_display = ('name', 'section')
    list_filter = ('section',)
    
@admin.register(Section)
class SectionAdmin(ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

class TicketStatusLogInline(TabularInline):
    model = TicketStatusLog
    extra = 0
    can_delete = False

    readonly_fields = (
        'old_status',
        'new_status',
        'changed_at',
    )


@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    class Media:
        js = ('css/js/admin_autorefresh.js',)

    inlines = [TicketStatusLogInline]
    search_fields =[
        'outlet',
        'section__name',
        'concern_type__name'
        ]

    list_display = ('outlet', 
                    'section', 
                    'concern_type', 
                    'status', 
                    'priority',
                    'ticket_age',
                    'latest_resolution',
                    'reopenings',)

    readonly_fields = ('download_button', 'outlet', 'message')
    list_filter = ('section', 'status', 'priority')

    fields = ('outlet', 'message', 'status', 
              'scheduled_date', 'scheduled_time', 'admin_note',
              'attachment', 'download_button',
              'section', 'priority', 'concern_type')


    
    def ticket_age(self, obj):

        seconds = int(obj.age.total_seconds())

        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        return f"{days}d {hours}h {minutes}m"

    ticket_age.short_description = "Age"

    def save_model(self, request, obj, form, change):

        if change:
            old_obj = Ticket.objects.get(pk=obj.pk)

        if old_obj.status != obj.status:
            TicketStatusLog.objects.create(
                ticket=obj,
                old_status=old_obj.status,
                new_status=obj.status,
            )

        super().save_model(request, obj, form, change)

    def latest_resolution(self, obj):
        last = obj.status_logs.order_by('-changed_at').first()
        return last.changed_at if last else None

    latest_resolution.short_description = "Latest Update"    
    def resolution_time(self, obj):

        if not obj.first_resolution_time:
            return "-"

        seconds = int(obj.first_resolution_time.total_seconds())

        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        return f"{days}d {hours}h {minutes}m"

    resolution_time.short_description = "Resolve"


    def reopenings(self, obj):
        return obj.reopen_count

    reopenings.short_description = "Reopens"
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

