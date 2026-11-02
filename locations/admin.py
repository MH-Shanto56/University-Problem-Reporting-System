from django.contrib import admin
from .models import Building, Floor, Room, Landmark, Equipment, Area

@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'latitude', 'longitude']
    list_filter = ['is_active']
    search_fields = ['name', 'code']

@admin.register(Floor)
class FloorAdmin(admin.ModelAdmin):
    list_display = ['name', 'building', 'floor_number', 'is_active']
    list_filter = ['building', 'is_active']
    search_fields = ['name', 'building__name']
    ordering = ['building', 'floor_number']

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'name', 'floor', 'room_type', 'is_active']
    list_filter = ['floor__building', 'floor', 'room_type', 'is_active']
    search_fields = ['room_number', 'name', 'floor__name']
    ordering = ['floor__building', 'floor__floor_number', 'room_number']

@admin.register(Landmark)
class LandmarkAdmin(admin.ModelAdmin):
    list_display = ['name', 'building', 'floor', 'room', 'is_active']
    list_filter = ['building', 'is_active']
    search_fields = ['name', 'building__name']

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'room', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']

@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ['name', 'building', 'floor', 'latitude', 'longitude']
    list_filter = ['building']
    search_fields = ['name', 'building', 'floor']
    ordering = ['building', 'name']
