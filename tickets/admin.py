from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Department, Ticket, ConcernType, Outlet, UserProfile
from .websocket import notify_ticket_update
from django.contrib.admin import AdminSite
from .models import Ticket, TicketStatusLog, TicketAttachment, Technician, TicketAssignmentLog
from unfold.admin import ModelAdmin, TabularInline
from unfold.sites import UnfoldAdminSite
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.safestring import mark_safe
from .models import DeviceToken
from tickets.notification import send_push
from .websocket import notify_ticket_delete

admin.site.register(DeviceToken)
admin.site.site_url = "/reports/"

@admin.register(Outlet)
class OutletAdmin(ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(UserProfile)
class UserProfileAdmin(ModelAdmin):
    list_display = ("user", "outlet")
    list_filter = ("outlet",)
    search_fields = ("user__username",)

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
    


@admin.register(TicketAssignmentLog)
class TicketAssignmentLogAdmin(ModelAdmin):
    list_display = (
        "ticket",
        "old_technician",
        "new_technician",
        "assigned_at"
    )

@admin.register(Technician)
class TechnicianAdmin(ModelAdmin):
    list_display = ("full_name", 'department')
    search_fields = ("full_name",)

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
    list_display = ('name', 'department')
    list_filter = ('department',)
    
@admin.register(Department)
class DepartmentAdmin(ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
class TicketAttachmentInline(admin.TabularInline):
    model = TicketAttachment
    extra = 1

class TicketStatusLogInline(TabularInline):
    model = TicketStatusLog
    extra = 0
    can_delete = False

    readonly_fields = (
        'old_status',
        'reasons',
        'new_status',
        'changed_at',
    )


@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    class Media:
        js = ('js/attach_modal.js',
              'js/page_loader.js',)

    inlines = [TicketStatusLogInline]
    search_fields =[
        'outlet__name',
        'department__name',
        'concern_type__name'
        ]

    list_display = ('outlet_with_badge', 
                    'department', 
                    'concern_type', 
                    'status', 
                    'priority',
                    'created_at',
                    'assigned_to',
                    'deadline',
                    'overdue',)

    @admin.display(description="Outlet")
    def outlet_with_badge(self, obj):   
        if not obj.is_opened:
            return format_html(
            '{} <span class="inline-flex items-center rounded-full bg-red-600 px-2 py-0.5 text-xs font-medium text-white">NEW</span>',
            obj.outlet.name,
        )
        return obj.outlet

    readonly_fields = ( 'attachment_preview', 'download_button', 'message')
    list_filter = ('department', 'status', 'priority', 'assigned_to', 'outlet')

    fields = ('outlet', 'message', 'attachment_preview', 'status',
              'scheduled_date', 'scheduled_time', 'admin_note', 'assigned_to',
              'department', 'priority', 'concern_type')


    def change_view(self, request, object_id, form_url="", extra_context=None):
        ticket = self.get_object(request, object_id)

        if ticket and not ticket.is_opened:
            ticket.is_opened = True
            ticket.save(update_fields=["is_opened"])

        return super().change_view(
            request,
            object_id,
            form_url,
            extra_context,
        )

    def  formfield_for_foreignkey(self, db_field, request, **kwargs):
            object_id = request.resolver_match.kwargs.get("object_id")   
            if db_field.name == "assigned_to":
             if object_id:
                 ticket = Ticket.objects.get(pk=object_id)

                 kwargs["queryset"] = Technician.objects.filter(
                     department=ticket.department
                 )
             else:
                kwargs["queryset"] = Technician.objects.none()

            return super().formfield_for_foreignkey(
             db_field,
             request,
             **kwargs
         )       

    def attachment_preview(self, obj):
        images = obj.attachments.all()

        if not images.exists():
            return "-"
        
        html = [] 

        html.append("""
    <div style="
        display: grid !important;
        grid-template-columns: repeat(3, 50px) !important;
        gap: 6px !important;
        width: fit-content;
    ">
    """)

        for a in images:
            html .append (f'''
            <div style="text-align:center;">
                 <input type="checkbox"
                        name="attachments"
                        value="{a.id}">

               <br>

                <img src="{a.file.url}"
                   onclick="openImageModal(this.src)"
                   style="width:45px;
                    height:45px;
                    object-fit:cover;
                    border-radius:50%;
                    cursor:pointer;
                    margin-right:5px;
                    border:2px solid #ddd;
                    display:block;
                    "/>
             </div> 
                   ''')
            
        html.append("</div>")

        html.append("""
                    <br>
                    <button type="button"
                            onclick="downloadSelectedAttachments()">
                        ⬇ Download Selected
                    </button>
                    """)

        return mark_safe("".join(html))
    
    attachment_preview.short_description = "attachments"

    def delete_model(self, request, obj):
        notify_ticket_delete(obj)
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for ticket in queryset:
            notify_ticket_delete(ticket)

        super().delete_queryset(request, queryset)

    def overdue(self, obj):
        if obj.is_overdue:
                return format_html ('<span style="color: {} !important; font-weight: bold;">{}</span>',
                                    'red',
                                    '⚠️Overdue')
        return format_html ('<span style="color: {} !important;">{}</span>',
                            'green',
                            '✅On time')

    overdue.short_description = "Overdue"
    
  

    def save_model(self, request, obj, form, change):

        if change:
            old_obj = Ticket.objects.get(pk=obj.pk)
        
            if old_obj.assigned_to != obj.assigned_to:
                TicketAssignmentLog.objects.create(
                    ticket=obj,
                    old_technician=old_obj.assigned_to,
                    new_technician=obj.assigned_to,
                    reason="Reassigned by admin"
             ) 

            if old_obj.status != obj.status:
                TicketStatusLog.objects.create(
                    ticket=obj,
                    old_status=old_obj.status,
                    new_status=obj.status,
                    technician=obj.assigned_to,
            )
            
        if obj.status == "resolved" and not obj.resolve_at:
            obj.resolve_at = timezone.now()

        elif obj.status != "resolved":
            obj.resolve_at = None    

        if not change and not obj.created_by:
            obj.created_by = request.user

        super().save_model(request, obj, form, change)

        profiles = UserProfile.objects.filter(outlet=obj.outlet)

        for profile in profiles:
            if change:
                send_push(
                    user=profile.user,
                    title="Ticket Updated",
                    body=f"Ticket #{obj.id} has been updated.",
                    data={
                        "ticket_id": str(obj.id),
                        "url": "https://fbmanagement.onrender.com/home/"
                    }
                )
            else:
                send_push(
                    user=profile.user,
                    title="New Ticket",
                    body=f"A new ticket has been created for {obj.outlet.name}.",
                    data={
                        "ticket_id": str(obj.id),
                        "url": "https://fbmanagement.onrender.com/home/"
                    }
                )
        
        notify_ticket_update(obj, action="update" if change else "create")
        

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
        first_file = obj.attachments.first()

        if first_file and first_file.file:
            return format_html(
            '<a href="{}" download>⬇ Download File</a>',
            first_file.file.url
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

