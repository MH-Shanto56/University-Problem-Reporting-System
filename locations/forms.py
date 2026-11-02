from django import forms
from .models import Building, Floor, Room, Landmark, Equipment, Area

class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ['name', 'code', 'description', 'latitude', 'longitude', 'is_active']


class FloorForm(forms.ModelForm):
    class Meta:
        model = Floor
        fields = ['building', 'floor_number', 'name', 'is_active']


class RoomForm(forms.ModelForm):
    # Use CharField to prevent strict ChoiceField rejection on lowercase/variant inputs
    room_type = forms.CharField(max_length=50, required=False)

    class Meta:
        model = Room
        fields = ['floor', 'room_number', 'name', 'room_type', 'is_active']

    def clean_room_type(self):
        val = self.cleaned_data.get('room_type', '')
        if not val:
            return 'Classroom'
        val = str(val).strip()
        val_lower = val.lower()
        mapping = {
            'classroom': 'Classroom',
            'class room': 'Classroom',
            'lecture_room': 'Classroom',
            'lecture hall': 'Classroom',
            'lab': 'Lab',
            'laboratory': 'Lab',
            'computer_lab': 'Lab',
            'faculty': 'Faculty',
            'faculty_room': 'Faculty',
            'office': 'Faculty',
            'dept_office': 'Faculty',
            'auditorium': 'Auditorium',
            'seminar_hall': 'Auditorium',
            'conference_hall': 'Auditorium',
            'washroom': 'Washroom',
            'restroom': 'Washroom',
            'toilet': 'Washroom',
            'common': 'Common',
            'library': 'Common',
            'cafeteria': 'Common',
            'lounge': 'Common',
            'prayer_room': 'Common',
            'mosque': 'Common',
            'other': 'Other',
        }
        if val_lower in mapping:
            return mapping[val_lower]
        # Match case-insensitively with defined Room.ROOM_TYPE_CHOICES
        for choice_key, choice_label in Room.ROOM_TYPE_CHOICES:
            if choice_key.lower() == val_lower or choice_label.lower() == val_lower:
                return choice_key
        return 'Classroom'


class LandmarkForm(forms.ModelForm):
    class Meta:
        model = Landmark
        fields = ['name', 'building', 'floor', 'room', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'style': 'width:100%;box-sizing:border-box;padding:10px 14px;background:#1c1917;color:#ffffff;border:1px solid rgba(255,255,255,0.15);border-radius:8px;font-size:14px;', 'placeholder': 'e.g. Auditorium, Main Elevator, Central Mosque'}),
            'building': forms.Select(attrs={'class': 'form-select', 'style': 'width:100%;padding:10px 14px;background:#1c1917;color:#ffffff;border:1px solid rgba(255,255,255,0.15);border-radius:8px;font-size:14px;'}),
            'floor': forms.Select(attrs={'class': 'form-select', 'style': 'width:100%;padding:10px 14px;background:#1c1917;color:#ffffff;border:1px solid rgba(255,255,255,0.15);border-radius:8px;font-size:14px;'}),
            'room': forms.Select(attrs={'class': 'form-select', 'style': 'width:100%;padding:10px 14px;background:#1c1917;color:#ffffff;border:1px solid rgba(255,255,255,0.15);border-radius:8px;font-size:14px;'}),
            'is_active': forms.CheckboxInput(attrs={'style': 'width:18px;height:18px;accent-color:#3b82f6;cursor:pointer;'}),
        }



