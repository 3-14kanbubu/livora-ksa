from django.contrib import admin
from .models import HealthReport

admin.site.site_header = "Livora Nurse Dashboard"
admin.site.site_title = "Livora Admin"
admin.site.index_title = "Welcome, Nurse"

@admin.register(HealthReport)
class HealthReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'symptoms', 'created_at', 'reviewed')
    list_filter = ('created_at', 'reviewed')
    search_fields = ('user__username','symptoms', 'extra_comments')
    actions = ['mark_as_reviewed']

    def mark_as_reviewed(self, request, queryset):
        updated = queryset.update(reviewed=True)
        self.message_user(request, f"{updated} reports marked as reviewed.")
    mark_as_reviewed.short_description = "Mark selected reports as reviewed"