import traceback
from env import EnvVarSetter
from db_tools.standardizers.giant import GiantStandardizer
from db_tools.standardizers.trek import TrekStandardizer


class Standardizer():
    def standardize_records(self):
        TrekStandardizer().standardize_records()
        GiantStandardizer().standardize_records()


if __name__ == '__main__':
    try:
        EnvVarSetter().set_vars()
        Standardizer().standardize_records()
    except Exception:
        traceback.print_exc()
