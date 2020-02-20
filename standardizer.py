import traceback
from env import EnvVarSetter
from db_tools.standardizers.giant import GiantStandardizer

if __name__ == '__main__':
    try:
        EnvVarSetter().set_vars()
        GiantStandardizer().standardize_records()
    except Exception:
        traceback.print_exc()
