from django.db import models

class Building(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g. Main Building, RH Building")
    code = models.CharField(max_length=20, unique=True, help_text="e.g. MB, RH")
    description = models.TextField(blank=True, default='')
    latitude = models.FloatField(default=23.7508)
    longitude = models.FloatField(default=90.3883)
    is_active = models.BooleanField(default=True, help_text="Active for new problem reporting")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_building'
        ordering = ['name']

    def __str__(self):
        return self.name


class Floor(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='floors')
    floor_number = models.IntegerField(default=0, help_text="e.g. 0 for Ground, 1 for 1st Floor, etc.")
    name = models.CharField(max_length=100, help_text="e.g. Ground Floor, 7th Floor (CSE)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_floor'
        ordering = ['building', 'floor_number', 'name']
        unique_together = ('building', 'name')

    def __str__(self):
        return f"{self.building.name} - {self.name}"


class Room(models.Model):
    ROOM_TYPE_CHOICES = [
        ('Classroom', 'Classroom'),
        ('Lab', 'Computer / Engineering Lab'),
        ('Faculty', 'Faculty / Department Office'),
        ('Auditorium', 'Auditorium / Conference Hall'),
        ('Washroom', 'Washroom / Restroom'),
        ('Common', 'Common Area / Lounge / Mosque / Game Room'),
        ('Other', 'Other Facility'),
    ]
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=50, help_text="e.g. 702, 404, PL-01, Software Lab 2")
    name = models.CharField(max_length=150, help_text="e.g. Room 702 (CSE Lecture), Software Lab 2")
    room_type = models.CharField(max_length=50, choices=ROOM_TYPE_CHOICES, default='Classroom')
    is_active = models.BooleanField(default=True, help_text="Deactivated rooms cannot receive new reports")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_room'
        ordering = ['floor__building', 'floor__floor_number', 'room_number']
        unique_together = ('floor', 'room_number')

    def __str__(self):
        return f"{self.floor.building.name} • {self.floor.name} • {self.room_number}"

    @property
    def building(self):
        return self.floor.building


class Landmark(models.Model):
    name = models.CharField(max_length=150, help_text="e.g. Auditorium, Garage, Washroom, Staircase, Elevator, Corridor, Main Entrance, Emergency Exit, Parking Area")
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='landmarks', null=True, blank=True)
    floor = models.ForeignKey(Floor, on_delete=models.SET_NULL, related_name='landmarks', null=True, blank=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, related_name='as_landmarks', null=True, blank=True,
                            help_text="Optional room reference if this landmark is a specific room")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_landmark'
        ordering = ['name']

    def __str__(self):
        b_name = self.building.name if self.building else "Campus"
        f_name = f" ({self.floor.name})" if self.floor else ""
        return f"{self.name} [{b_name}{f_name}]"


class Equipment(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='equipments', null=True, blank=True)
    name = models.CharField(max_length=100, help_text="e.g. Projector, AC, PC, Switch")
    code = models.CharField(max_length=50, help_text="e.g. AC-01, Projector-1, PC-24")
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'core_equipment'
        ordering = ['name', 'code']

    def __str__(self):
        loc = self.room.room_number if self.room else "General"
        return f"{self.name} ({self.code}) - {loc}"


class Area(models.Model):
    BUILDING_CHOICES = [
        ('Main Building', 'Main Building'),
        ('RH Building', 'RH Building'),
        ('Campus Premises', 'Campus Premises / Outdoor'),
    ]
    building = models.CharField(max_length=50, choices=BUILDING_CHOICES, default='Main Building')
    floor = models.CharField(max_length=100, blank=True, default='', help_text="e.g. Ground Floor, 7th Floor, etc.")
    name = models.CharField(max_length=150, unique=True)
    latitude = models.FloatField(default=23.7508)
    longitude = models.FloatField(default=90.3883)

    class Meta:
        db_table = 'core_area'
        ordering = ['building', 'name']

    def __str__(self):
        return self.name
