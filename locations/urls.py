from django.urls import path
from . import views

urlpatterns = [
    path('locations/', views.location_list_view, name='location_list'),
    path('locations/create/', views.location_create_view, name='location_create'),
    path('locations/<int:pk>/update/', views.location_update_view, name='location_update'),
    path('locations/<int:pk>/delete/', views.location_delete_view, name='location_delete'),
    path('locations/buildings/create/', views.building_create_view, name='building_create'),
    path('locations/buildings/<int:pk>/update/', views.building_update_view, name='building_update'),
    path('locations/buildings/<int:pk>/delete/', views.building_delete_view, name='building_delete'),
    path('locations/floors/create/', views.floor_create_view, name='floor_create'),
    path('locations/floors/<int:pk>/delete/', views.floor_delete_view, name='floor_delete'),
    path('locations/rooms/create/', views.room_create_view, name='room_create'),
    path('locations/rooms/<int:pk>/update/', views.room_update_view, name='room_update'),
    path('locations/rooms/<int:pk>/deactivate/', views.room_deactivate_view, name='room_deactivate'),
    path('locations/landmarks/create/', views.landmark_create_view, name='landmark_create'),
    path('locations/landmarks/<int:pk>/update/', views.landmark_update_view, name='landmark_update'),
    path('locations/landmarks/<int:pk>/delete/', views.landmark_delete_view, name='landmark_delete'),
    path('locations/landmarks/<int:pk>/deactivate/', views.landmark_deactivate_view, name='landmark_deactivate'),
    path('map/', views.area_map_view, name='map'),
    path('area-map/', views.area_map_view, name='area_map'),
    path('admin-portal/locations/', views.admin_locations_view, name='admin_locations'),
    path('api/floors/', views.api_floors, name='api_floors'),
    path('api/rooms/', views.api_rooms, name='api_rooms'),
    path('api/landmarks/', views.api_landmarks, name='api_landmarks'),
]
