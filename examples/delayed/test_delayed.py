# from hatchet_sdk import Hatchet
# import pytest

# from tests.utils import fixture_bg_worker
# from tests.utils.hatchet_client import hatchet_client_fixture


# hatchet = hatchet_client_fixture()
# worker = fixture_bg_worker(["poetry", "run", "manual_trigger"])

# # requires scope module or higher for shared event loop
# @pytest.mark.asyncio(scope="session")
# async def test_run(hatchet: Hatchet):
#     # TODO