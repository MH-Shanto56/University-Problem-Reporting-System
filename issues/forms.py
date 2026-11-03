from django import forms
from django.utils import timezone
from .models import Issue, ResolutionVerification, IssueStatusHistory, IssueReopenRequest
from locations.models import Building, Floor, Room, Landmark, Equipment, Area
from departments.models import Department

class IssueForm(forms.ModelForm):
    location_type = forms.ChoiceField(
        choices=Issue.LOCATION_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'location-type-radio'}),
        initial='room',
        required=True
    )
    building = forms.ModelChoiceField(
        queryset=Building.objects.filter(is_active=True),
        required=False,
        empty_label="-- Select Campus Building --",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'buildingSelect'})
    )
    floor = forms.ModelChoiceField(
        queryset=Floor.objects.filter(is_active=True),
        required=False,
        empty_label="-- Select Floor --",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'floorSelect'})
    )
    room = forms.ModelChoiceField(
        queryset=Room.objects.filter(is_active=True),
        required=False,
        empty_label="-- Select Valid Registered Room --",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'roomSelect'})
    )
    equipment_identifier = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. AC-01, Projector-1, Lab PC 24', 'class': 'form-input'})
    )
    landmark = forms.ModelChoiceField(
        queryset=Landmark.objects.filter(is_active=True),
        required=False,
        empty_label="-- Select Landmark (e.g. Auditorium, Stairs, Elevator) --",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'landmarkSelect'})
    )
    landmark_room = forms.ModelChoiceField(
        queryset=Room.objects.filter(is_active=True),
        required=False,
        empty_label="-- Nearby Reference Room (Optional) --",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'landmarkRoomSelect'})
    )
    relative_position = forms.ChoiceField(
        choices=Issue.RELATIVE_POSITION_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'relativePositionSelect'})
    )
    custom_location_description = forms.CharField(
        max_length=300,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. 3rd floor staircase landing on the left, next to water dispenser',
            'class': 'form-input',
            'id': 'customLocationInput'
        })
    )

    class Meta:
        model = Issue
        fields = [
            'title', 'description', 'category', 'priority', 'visibility', 'image',
            'location_type', 'building', 'floor', 'room', 'equipment_identifier',
            'landmark', 'relative_position', 'custom_location_description'
        ]

    def clean(self):
        cleaned = super().clean()
        loc_type = cleaned.get('location_type')
        building = cleaned.get('building')
        floor = cleaned.get('floor')
        room = cleaned.get('room')
        landmark = cleaned.get('landmark')
        custom_desc = cleaned.get('custom_location_description')

        if not building:
            self.add_error('building', 'Please select a campus building.')

        if loc_type == 'room':
            if not room:
                self.add_error('room', 'Please select a registered room number from the directory.')
            elif floor and room.floor_id != floor.id:
                self.add_error('room', f"Room '{room.room_number}' does not belong to {floor.name}.")
            elif building and room.floor.building_id != building.id:
                self.add_error('room', f"Room '{room.room_number}' does not belong to {building.name}.")
        elif loc_type == 'landmark':
            if not landmark and not custom_desc:
                self.add_error('landmark', 'Please select a campus landmark or provide a descriptive custom location.')
        return cleaned


class ResolutionVerificationForm(forms.ModelForm):
    class Meta:
        model = ResolutionVerification
        fields = ['verification_choice', 'comment', 'image']


class StatusUpdateForm(forms.Form):
    status = forms.ChoiceField(choices=Issue.STATUS_CHOICES)
    reason = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, instance=None, **kwargs):
        if instance:
            initial = kwargs.get('initial', {})
            initial.setdefault('status', instance.status)
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)


class IssueClosureForm(forms.Form):
    closure_reason = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter official verification notes and closure justification...'}),
        required=True
    )


class IssueReopenForm(forms.Form):
    reopen_reason = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Explain why this problem still exists or has reoccurred...'}),
        required=True
    )
