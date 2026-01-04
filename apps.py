from django.apps import AppConfig


class StaffConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "staff"
    verbose_name = "Staff"

    def ready(self):
        pass

    @staticmethod
    def do_after_staff_create(staff) -> None:
        """Called after staff member is created."""
        pass

    @staticmethod
    def do_after_clock_in(staff) -> None:
        """Called after staff clocks in."""
        pass

    @staticmethod
    def do_after_clock_out(staff) -> None:
        """Called after staff clocks out."""
        pass

    @staticmethod
    def filter_staff_list(queryset, request):
        """Filter staff queryset."""
        return queryset
