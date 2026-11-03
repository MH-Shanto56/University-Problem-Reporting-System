from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q
from .models import Building, Floor, Room, Landmark, Equipment, Area
from .forms import RoomForm, LandmarkForm, AreaForm, BuildingForm, FloorForm


def location_list_view(request):
    """Admin and Student overview of campus locations and room registry."""
    buildings = Building.objects.prefetch_related('floors__rooms').all()
    rooms = Room.objects.select_related('floor__building').all().order_by('floor__building', 'floor__floor_number', 'room_number')
    landmarks = Landmark.objects.select_related('building', 'floor', 'room').all()
    equipments = Equipment.objects.select_related('room__floor__building').all()
    areas = Area.objects.all().order_by('building', 'name')
    return render(request, 'locations/location_list.html', {
        'buildings': buildings,
        'rooms': rooms,
        'landmarks': landmarks,
        'equipments': equipments,
        'areas': areas,
        'total_rooms': rooms.count(),
        'active_page': 'locations',
    })


@login_required
def admin_locations_view(request):
    """Admin Campus Location & Room Registry Management."""
    if not (request.user.is_staff or request.user.is_superuser):
        return render(request, '403.html', {'reason': 'Access restricted to authorized administrators.'}, status=403)

    if not request.user.is_superuser:
        return redirect('department_dashboard')

    # Handle inline quick POST actions from admin modals
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_building':
            name = request.POST.get('name', '').strip()
            code = request.POST.get('code', '').strip().upper()
            description = request.POST.get('description', '').strip()
            if name:
                if not code:
                    code = ''.join([w[0] for w in name.split() if w]).upper()[:10] or 'BLDG'
                bldg, created = Building.objects.get_or_create(
                    name=name,
                    defaults={'code': code, 'description': description}
                )
                if created:
                    messages.success(request, f'Campus Building "{bldg.name}" ({bldg.code}) registered successfully!')
                else:
                    messages.info(request, f'Building "{bldg.name}" already exists.')
            else:
                messages.error(request, 'Building name is required.')
            return redirect('admin_locations')

        elif action == 'create_area':
            name = request.POST.get('name', '').strip()
            building = request.POST.get('building', 'Campus Premises / Outdoor').strip()
            floor = request.POST.get('floor', 'Ground / Outdoor Area').strip()
            if name:
                area, created = Area.objects.get_or_create(
                    name=name,
                    defaults={'building': building, 'floor': floor}
                )
                if created:
                    messages.success(request, f'Campus Land Area "{area.name}" defined successfully!')
                else:
                    messages.info(request, f'Land Area "{area.name}" already exists.')
            else:
                messages.error(request, 'Land Area name is required.')
            return redirect('admin_locations')

    buildings = Building.objects.prefetch_related('floors__rooms').order_by('name')
    total_rooms = Room.objects.count()
    landmarks = Landmark.objects.select_related('building', 'floor', 'room').order_by('name')
    rooms = Room.objects.select_related('floor__building').order_by('floor__building__name', 'room_number')
    areas = Area.objects.all().order_by('building', 'name')

    return render(request, 'admin/location_management.html', {
        'active_page': 'admin_locations',
        'admin_active': 'locations',
        'buildings': buildings,
        'total_rooms': total_rooms,
        'landmarks': landmarks,
        'rooms': rooms,
        'areas': areas,
    })


@login_required
def building_create_view(request):
    """Define a new Campus Building / Wing."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only administrators can define campus buildings.')
        return redirect('location_list')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, 'Building name is required.')
        else:
            if not code:
                code = ''.join([w[0] for w in name.split() if w]).upper()[:10] or 'BLDG'
            bldg, created = Building.objects.get_or_create(
                name=name,
                defaults={'code': code, 'description': description}
            )
            if created:
                messages.success(request, f'Building "{bldg.name}" ({bldg.code}) registered successfully!')
            else:
                messages.info(request, f'Building "{bldg.name}" already exists.')

    next_url = request.POST.get('next') or ('admin_locations' if request.user.is_superuser else 'location_list')
    return redirect(next_url)


@login_required
def building_update_view(request, pk):
    """Modify building details."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only administrators can edit campus buildings.')
        return redirect('location_list')

    building = get_object_or_404(Building, pk=pk)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on' or request.POST.get('is_active') == 'true'

        if not name:
            messages.error(request, 'Building name cannot be empty.')
        else:
            if Building.objects.filter(name=name).exclude(pk=building.pk).exists():
                messages.error(request, f'A building named "{name}" already exists.')
            elif code and Building.objects.filter(code=code).exclude(pk=building.pk).exists():
                messages.error(request, f'Building code "{code}" is already used by another building.')
            else:
                building.name = name
                if code:
                    building.code = code
                building.description = description
                building.is_active = is_active
                building.save()
                messages.success(request, f'Building "{building.name}" updated successfully!')
                next_url = request.POST.get('next') or ('admin_locations' if request.user.is_superuser else 'location_list')
                return redirect(next_url)

    return render(request, 'locations/building_form.html', {
        'building': building,
        'title': f'Edit Building: {building.name}',
        'active_page': 'admin_locations' if request.user.is_superuser else 'locations'
    })


@login_required
def building_delete_view(request, pk):
    """Delete a building with confirmation and safety checks."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only administrators can delete campus buildings.')
        return redirect('location_list')

    building = get_object_or_404(Building, pk=pk)
    floors_count = building.floors.count()
    rooms_count = Room.objects.filter(floor__building=building).count()
    issues_count = building.issues.count()

    if request.method == 'POST':
        name = building.name
        building.delete()
        messages.success(request, f'Building "{name}" and associated floors/rooms deleted successfully.')
        next_url = request.POST.get('next') or ('admin_locations' if request.user.is_superuser else 'location_list')
        return redirect(next_url)

    return render(request, 'locations/building_delete.html', {
        'building': building,
        'floors_count': floors_count,
        'rooms_count': rooms_count,
        'issues_count': issues_count,
        'title': f'Delete Building: {building.name}',
        'active_page': 'admin_locations' if request.user.is_superuser else 'locations'
    })


@login_required
def floor_create_view(request):
    """Define a new Floor level under a Building."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only administrators can define campus floors.')
        return redirect('location_list')

    if request.method == 'POST':
        building_id = request.POST.get('building')
        floor_name = request.POST.get('name', '').strip()
        floor_number = request.POST.get('floor_number', '0')

        if not building_id or not floor_name:
            messages.error(request, 'Please select a building and specify a floor name.')
        else:
            building = get_object_or_404(Building, pk=building_id)
            try:
                floor_number = int(floor_number)
            except (ValueError, TypeError):
                floor_number = 0
            floor, created = Floor.objects.get_or_create(
                building=building,
                name=floor_name,
                defaults={'floor_number': floor_number}
            )
            if created:
                messages.success(request, f'Floor "{floor.name}" defined under {building.name}!')
            else:
                messages.info(request, f'Floor "{floor.name}" already exists under {building.name}.')

    next_url = request.POST.get('next') or ('admin_locations' if request.user.is_superuser else 'location_list')
    return redirect(next_url)


@login_required
def floor_delete_view(request, pk):
    """Delete a floor level."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only administrators can delete floors.')
        return redirect('location_list')
    floor = get_object_or_404(Floor, pk=pk)
    if request.method == 'POST':
        name = floor.name
        b_name = floor.building.name
        floor.delete()
        messages.success(request, f'Floor "{name}" under {b_name} deleted successfully.')
    return redirect('admin_locations' if request.user.is_superuser else 'location_list')


@login_required
def room_create_view(request):
    """Register a new Room with Building -> Floor -> Room cascading and on-the-fly definition."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only University Administrators can register new rooms.')
        return redirect('location_list')

    buildings = Building.objects.filter(is_active=True).prefetch_related('floors').order_by('name')

    if request.method == 'POST':
        post_data = request.POST.copy()

        # 1. On-the-fly Building creation if requested
        new_building_name = request.POST.get('new_building_name', '').strip()
        new_building_code = request.POST.get('new_building_code', '').strip()
        building_id = request.POST.get('building')

        if new_building_name:
            if not new_building_code:
                new_building_code = ''.join([w[0] for w in new_building_name.split() if w]).upper()[:10] or 'BLDG'
            bldg, _ = Building.objects.get_or_create(
                name=new_building_name,
                defaults={'code': new_building_code}
            )
            building_id = bldg.id
            post_data['building'] = bldg.id

        # 2. On-the-fly Floor creation if requested
        new_floor_name = request.POST.get('new_floor_name', '').strip()
        new_floor_number = request.POST.get('new_floor_number', '0').strip()
        try:
            new_floor_num = int(new_floor_number)
        except (ValueError, TypeError):
            new_floor_num = 0

        if new_floor_name and building_id:
            bldg = get_object_or_404(Building, pk=building_id)
            floor, _ = Floor.objects.get_or_create(
                building=bldg,
                name=new_floor_name,
                defaults={'floor_number': new_floor_num}
            )
            post_data['floor'] = floor.id

        form = RoomForm(post_data)
        if form.is_valid():
            room = form.save()
            messages.success(request, f'Room "{room.room_number}" ({room.name}) registered successfully in {room.floor.building.name} - {room.floor.name}!')
            next_url = 'admin_locations' if request.user.is_superuser else 'location_list'
            return redirect(next_url)
        else:
            if 'floor' in form.errors and not post_data.get('floor'):
                messages.error(request, 'Please select a Building and Floor Level (or define a new floor).')
    else:
        form = RoomForm()

    return render(request, 'locations/room_form.html', {
        'form': form,
        'buildings': buildings,
        'title': 'Register New Room',
        'active_page': 'admin_locations' if request.user.is_superuser else 'locations'
    })


@login_required
def room_update_view(request, pk):
    """Modify a Room."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only University Administrators can modify rooms.')
        return redirect('location_list')
    room = get_object_or_404(Room, pk=pk)
    buildings = Building.objects.filter(is_active=True).prefetch_related('floors').order_by('name')

    if request.method == 'POST':
        post_data = request.POST.copy()

        # 1. On-the-fly Building creation if requested
        new_building_name = request.POST.get('new_building_name', '').strip()
        new_building_code = request.POST.get('new_building_code', '').strip()
        building_id = request.POST.get('building')

        if new_building_name:
            if not new_building_code:
                new_building_code = ''.join([w[0] for w in new_building_name.split() if w]).upper()[:10] or 'BLDG'
            bldg, _ = Building.objects.get_or_create(
                name=new_building_name,
                defaults={'code': new_building_code}
            )
            building_id = bldg.id
            post_data['building'] = bldg.id

        # 2. On-the-fly Floor creation if requested
        new_floor_name = request.POST.get('new_floor_name', '').strip()
        new_floor_number = request.POST.get('new_floor_number', '0').strip()
        try:
            new_floor_num = int(new_floor_number)
        except (ValueError, TypeError):
            new_floor_num = 0

        if new_floor_name and building_id:
            bldg = get_object_or_404(Building, pk=building_id)
            floor, _ = Floor.objects.get_or_create(
                building=bldg,
                name=new_floor_name,
                defaults={'floor_number': new_floor_num}
            )
            post_data['floor'] = floor.id

        form = RoomForm(post_data, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, f'Room "{room.room_number}" updated successfully!')
            next_url = 'admin_locations' if request.user.is_superuser else 'location_list'
            return redirect(next_url)
    else:
        form = RoomForm(instance=room)

    return render(request, 'locations/room_form.html', {
        'form': form,
        'room': room,
        'buildings': buildings,
        'current_building_id': room.floor.building.id if room.floor and room.floor.building else None,
        'title': f'Edit Room {room.room_number}',
        'active_page': 'admin_locations' if request.user.is_superuser else 'locations'
    })


@login_required
def room_deactivate_view(request, pk):
    """Deactivate or activate a Room."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized.')
        return redirect('location_list')
    room = get_object_or_404(Room, pk=pk)
    room.is_active = not room.is_active
    room.save()
    status_str = "activated" if room.is_active else "deactivated"
    messages.success(request, f'Room "{room.room_number}" {status_str} successfully.')
    next_url = 'admin_locations' if request.user.is_superuser else 'location_list'
    return redirect(next_url)


@login_required
def landmark_create_view(request):
    """Add a new landmark."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized.')
        return redirect('location_list')
    if request.method == 'POST':
        form = LandmarkForm(request.POST)
        if form.is_valid():
            lm = form.save()
            messages.success(request, f'Landmark "{lm.name}" added successfully!')
            next_url = 'admin_locations' if request.user.is_superuser else 'location_list'
            return redirect(next_url)
    else:
        form = LandmarkForm()
    return render(request, 'locations/landmark_form.html', {
        'form': form,
        'title': 'Add Campus Landmark',
        'active_page': 'admin_locations' if request.user.is_superuser else 'locations'
    })


@login_required
def landmark_update_view(request, pk):
    """Edit an existing landmark."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized.')
        return redirect('location_list')
    lm = get_object_or_404(Landmark, pk=pk)
    if request.method == 'POST':
        form = LandmarkForm(request.POST, instance=lm)
        if form.is_valid():
            form.save()
            messages.success(request, f'Landmark "{lm.name}" updated successfully!')
            next_url = request.POST.get('next') or ('admin_locations' if request.user.is_superuser else 'location_list')
            return redirect(next_url)
    else:
        form = LandmarkForm(instance=lm)
    return render(request, 'locations/landmark_form.html', {
        'form': form,
        'landmark': lm,
        'title': f'Edit Landmark: {lm.name}',
        'active_page': 'admin_locations' if request.user.is_superuser else 'locations'
    })


@login_required
def landmark_delete_view(request, pk):
    """Delete a landmark with confirmation."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized.')
        return redirect('location_list')
    lm = get_object_or_404(Landmark, pk=pk)
    issues_count = lm.issues.count()
    if request.method == 'POST':
        name = lm.name
        lm.delete()
        messages.success(request, f'Landmark "{name}" deleted successfully.')
        next_url = request.POST.get('next') or ('admin_locations' if request.user.is_superuser else 'location_list')
        return redirect(next_url)
    return render(request, 'locations/landmark_delete.html', {
        'landmark': lm,
        'issues_count': issues_count,
        'title': f'Delete Landmark: {lm.name}',
        'active_page': 'admin_locations' if request.user.is_superuser else 'locations'
    })


@login_required
def landmark_deactivate_view(request, pk):
    """Deactivate or activate a landmark."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized.')
        return redirect('location_list')
    lm = get_object_or_404(Landmark, pk=pk)
    lm.is_active = not lm.is_active
    lm.save()
    status_str = "activated" if lm.is_active else "deactivated"
    messages.success(request, f'Landmark "{lm.name}" {status_str} successfully.')
    next_url = 'admin_locations' if request.user.is_superuser else 'location_list'
    return redirect(next_url)


@login_required
def location_create_view(request):
    """Add a new Land Area / Campus Location."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized.')
        return redirect('location_list')
    if request.method == 'POST':
        form = AreaForm(request.POST)
        if form.is_valid():
            area = form.save()
            messages.success(request, f'Campus Land Area "{area.name}" added successfully!')
            next_url = request.POST.get('next') or ('admin_locations' if request.user.is_superuser else 'location_list')
            return redirect(next_url)
    else:
        form = AreaForm()
    return render(request, 'locations/location_form.html', {
        'form': form,
        'title': 'Add Campus Land Area / Outdoor Zone',
        'active_page': 'admin_locations' if request.user.is_superuser else 'locations'
    })


@login_required
def location_update_view(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized.')
        return redirect('location_list')
    area = get_object_or_404(Area, pk=pk)
    if request.method == 'POST':
        form = AreaForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            messages.success(request, f'Campus Land Area "{area.name}" updated successfully!')
            next_url = request.POST.get('next') or ('admin_locations' if request.user.is_superuser else 'location_list')
            return redirect(next_url)
    else:
        form = AreaForm(instance=area)
    return render(request, 'locations/location_form.html', {
        'form': form,
        'area': area,
        'title': 'Edit Campus Land Area',
        'active_page': 'admin_locations' if request.user.is_superuser else 'locations'
    })


@login_required
def location_delete_view(request, pk):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Unauthorized.')
        return redirect('location_list')
    area = get_object_or_404(Area, pk=pk)
    if request.method == 'POST':
        linked_issues = area.issues.count()
        if linked_issues > 0:
            messages.error(request, f'Cannot delete "{area.name}" because {linked_issues} issue reports are linked to it.')
            next_url = request.POST.get('next') or ('admin_locations' if request.user.is_superuser else 'location_list')
            return redirect(next_url)
        name = area.name
        area.delete()
        messages.success(request, f'Land Area "{name}" deleted successfully.')
        next_url = request.POST.get('next') or ('admin_locations' if request.user.is_superuser else 'location_list')
        return redirect(next_url)
    return render(request, 'locations/location_delete.html', {'area': area, 'active_page': 'admin_locations' if request.user.is_superuser else 'locations'})


def area_map_view(request):
    return redirect('dashboard')


def api_floors(request):
    building_id = request.GET.get('building_id')
    if not building_id:
        return JsonResponse({'floors': []})
    floors = Floor.objects.filter(building_id=building_id, is_active=True).order_by('floor_number')
    data = [{'id': f.id, 'name': f.name, 'floor_number': f.floor_number} for f in floors]
    return JsonResponse({'floors': data})


def api_rooms(request):
    floor_id = request.GET.get('floor_id')
    if not floor_id:
        return JsonResponse({'rooms': []})
    rooms = Room.objects.filter(floor_id=floor_id, is_active=True).order_by('room_number')
    data = [{'id': r.id, 'room_number': r.room_number, 'name': r.name, 'type': r.room_type} for r in rooms]
    return JsonResponse({'rooms': data})


def api_landmarks(request):
    building_id = request.GET.get('building_id')
    floor_id = request.GET.get('floor_id')
    qs = Landmark.objects.filter(is_active=True)
    if building_id:
        qs = qs.filter(Q(building_id=building_id) | Q(building__isnull=True))
    if floor_id:
        qs = qs.filter(Q(floor_id=floor_id) | Q(floor__isnull=True))
    data = [{'id': lm.id, 'name': lm.name} for lm in qs]
    return JsonResponse({'landmarks': data})
