from unittest.mock import patch

from django.test import TestCase

from .cache_keys import CACHE_KEY_DASHBOARD
from .models import Feeder


class FeederDashboardCacheTests(TestCase):
    def test_saving_or_deleting_a_feeder_invalidates_dashboard_cache(self):
        with patch("myapp.signals.cache.delete") as delete_cache:
            with self.captureOnCommitCallbacks(execute=True):
                feeder = Feeder.objects.create(name="Dashboard cache test feeder")

            delete_cache.assert_called_once_with(CACHE_KEY_DASHBOARD)
            delete_cache.reset_mock()

            with self.captureOnCommitCallbacks(execute=True):
                feeder.delete()

            delete_cache.assert_called_once_with(CACHE_KEY_DASHBOARD)
