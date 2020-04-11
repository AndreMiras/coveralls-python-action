from unittest import mock

import entrypoint


class TestEntryPoint:
    def test_main(self):
        with mock.patch("entrypoint.run_coveralls") as m_run_coveralls:
            entrypoint.main()
        assert m_run_coveralls.call_args_list == [mock.call()]
