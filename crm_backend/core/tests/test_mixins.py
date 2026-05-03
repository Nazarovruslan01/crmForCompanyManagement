"""Tests for core.mixins.ResidentQuerySetMixin."""

from core.mixins import ResidentQuerySetMixin


class MockQuerySet:
    """Stub queryset that records filter calls."""

# pyright: reportAttributeAccessIssue=false, reportCallIssue=false, reportPossiblyUnboundVariable=false, reportIncompatibleMethodOverride=false

    def __init__(self, data: list[object] | None = None) -> None:
        self._data = data or []
        self.filter_calls: list[dict] = []
        self.distinct_called = False

    def filter(self, **kwargs: object) -> "MockQuerySet":
        self.filter_calls.append(kwargs)
        return self

    def distinct(self) -> "MockQuerySet":
        self.distinct_called = True
        return self

    def none(self) -> "MockQuerySet":
        self._data = []
        return self


class MockUser:
    def __init__(self, role: str = "resident", has_profile: bool = True) -> None:
        self.role = role
        self.is_authenticated = True
        self._has_profile = has_profile

    @property
    def resident_profile(self):
        if self._has_profile:
            return object()
        return None


class MockRequest:
    def __init__(self, user: MockUser) -> None:
        self.user = user


class BaseView:
    """Simulates a base ModelViewSet that returns a MockQuerySet."""

    def get_queryset(self) -> MockQuerySet:
        return MockQuerySet()


class ViewStub(ResidentQuerySetMixin, BaseView):
    resident_lookup = "apartment__ownerships__resident__user"

    def __init__(self, request: MockRequest) -> None:
        self.request = request


class ViewStubEmptyLookup(ResidentQuerySetMixin, BaseView):
    resident_lookup = ""

    def __init__(self, request: MockRequest) -> None:
        self.request = request


class TestResidentQuerySetMixin:
    """Unit tests for ResidentQuerySetMixin.get_queryset filtering logic."""

    def test_admin_returns_unfiltered_queryset(self) -> None:
        request = MockRequest(MockUser(role="admin"))
        view = ViewStub(request)
        qs = view.get_queryset()
        assert isinstance(qs, MockQuerySet)
        assert qs.filter_calls == []

    def test_manager_returns_unfiltered_queryset(self) -> None:
        request = MockRequest(MockUser(role="manager"))
        view = ViewStub(request)
        qs = view.get_queryset()
        assert isinstance(qs, MockQuerySet)
        assert qs.filter_calls == []

    def test_resident_with_profile_filters_by_lookup(self) -> None:
        user = MockUser(role="resident", has_profile=True)
        request = MockRequest(user)
        view = ViewStub(request)
        qs = view.get_queryset()
        assert len(qs.filter_calls) == 1
        assert qs.filter_calls[0] == {"apartment__ownerships__resident__user": user}
        assert qs.distinct_called is True

    def test_resident_without_profile_returns_none(self) -> None:
        request = MockRequest(MockUser(role="resident", has_profile=False))
        view = ViewStub(request)
        qs = view.get_queryset()
        # none() is called when resident has no profile, so filter_calls stay empty
        assert qs.filter_calls == []

    def test_empty_resident_lookup_returns_unfiltered(self) -> None:
        request = MockRequest(MockUser(role="resident", has_profile=True))
        view = ViewStubEmptyLookup(request)
        qs = view.get_queryset()
        assert qs.filter_calls == []
        assert qs.distinct_called is False

    def test_worker_returns_unfiltered_queryset(self) -> None:
        request = MockRequest(MockUser(role="worker"))
        view = ViewStub(request)
        qs = view.get_queryset()
        assert isinstance(qs, MockQuerySet)
        assert qs.filter_calls == []
