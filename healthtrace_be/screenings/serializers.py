from rest_framework import serializers
from .models import RoleConfig, ScreeningStation, PatientWorkflow, StationEntry


class RoleConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoleConfig
        fields = '__all__'


class ScreeningStationSerializer(serializers.ModelSerializer):
    role_config_detail = RoleConfigSerializer(source='role_config', read_only=True)

    class Meta:
        model = ScreeningStation
        fields = '__all__'


class PatientWorkflowSerializer(serializers.ModelSerializer):
    current_station_name = serializers.CharField(source='current_station.name', read_only=True)

    class Meta:
        model = PatientWorkflow
        fields = '__all__'
        read_only_fields = ('token_id',)


class StationEntrySerializer(serializers.ModelSerializer):
    client_submission_id = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
        default=''
    )

    class Meta:
        model = StationEntry
        fields = '__all__'
        read_only_fields = ('recorded_by', 'created_at')

    def validate(self, attrs):
        """
        Validates the JSON payload in `data` against the schema 
        defined in the station's assigned RoleConfig.
        """
        station = attrs.get('station')
        data = attrs.get('data', {})

        if not station or not station.role_config:
            return attrs

        schema = station.role_config.schema or []
        errors = {}

        # Iterate through field specs defined in the RoleConfig schema
        for field in schema:
            field_name = field.get('name')
            label = field.get('label', field_name)
            is_required = field.get('required', False)
            field_type = field.get('type', 'text')

            value = data.get(field_name)

            # 1. Required Field Validation
            if is_required and (value is None or value == ''):
                errors[field_name] = f"Field '{label}' is required."
                continue

            # Skip type validation if value is optional and missing
            if value is None or value == '':
                continue

            # 2. Field Type Validation
            if field_type == 'number':
                try:
                    float(value)
                except (ValueError, TypeError):
                    errors[field_name] = f"Field '{label}' must be a valid number."

            elif field_type == 'boolean':
                if not isinstance(value, bool):
                    errors[field_name] = f"Field '{label}' must be true or false."

            elif field_type == 'select':
                options = field.get('options', [])
                if options and value not in options:
                    errors[field_name] = f"Value '{value}' is not a valid choice for '{label}'. Options: {options}"

        if errors:
            raise serializers.ValidationError({"data": errors})

        return attrs