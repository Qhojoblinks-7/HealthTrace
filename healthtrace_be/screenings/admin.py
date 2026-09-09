from django.contrib import admin
from .models import RoleConfig, ScreeningStation, PatientWorkflow, StationEntry

@admin.register(RoleConfig)
class RoleConfigAdmin(admin.ModelAdmin):
    list_display = ('role_name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('role_name',)

@admin.register(ScreeningStation)
class ScreeningStationAdmin(admin.ModelAdmin):
    list_display = ('step_order', 'name', 'role_config', 'is_final_discharge', 'is_active')
    list_filter = ('is_final_discharge', 'is_active')
    ordering = ('step_order',)

@admin.register(PatientWorkflow)
class PatientWorkflowAdmin(admin.ModelAdmin):
    list_display = ('token_id', 'patient_name', 'current_station', 'is_urgent', 'is_completed', 'created_at')
    list_filter = ('current_station', 'is_urgent', 'is_completed')
    search_fields = ('token_id', 'patient_name', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(StationEntry)
class StationEntryAdmin(admin.ModelAdmin):
    list_display = ('patient', 'station', 'recorded_by', 'created_at')
    list_filter = ('station',)
    search_fields = ('patient__token_id', 'patient__patient_name')